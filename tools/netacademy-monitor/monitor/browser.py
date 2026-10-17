"""Use the public UI. Do not synthesize or replay private server action calls."""
import asyncio
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
from .state import BOOKING_URL

RIYADH = ZoneInfo('Asia/Riyadh')

class InspectionError(RuntimeError):
    def __init__(self, message, access_succeeded=False):
        super().__init__(message)
        self.access_succeeded = access_succeeded


def parse_slots(body, expected_date, duration):
    payload = None
    for line in body.splitlines():
        try: item = json.loads(line.split(':', 1)[1])
        except (ValueError, IndexError): continue
        if isinstance(item, dict) and 'results' in item:
            payload = item
    if not payload or payload.get('success') is not True or not payload['results']:
        raise ValueError('Slot response missing successful results')
    slots = []
    for entry in payload['results']:
        result = entry.get('result', {})
        if result.get('success') is not True or not isinstance(result.get('data'), list):
            raise ValueError('Slot result failed or schema changed')
        if not result['data']:
            raise ValueError('No date-labelled slot rows; inventory is unconfirmed')
        for row in result['data']:
            if row.get('booking_date') != expected_date or type(row.get('is_available')) is not bool:
                raise ValueError('Slot response date or availability schema mismatch')
            for field in ('start_time', 'end_time'):
                if not re.fullmatch(r'\d{2}:\d{2}', row.get(field, '')):
                    raise ValueError('Invalid slot time')
                datetime.strptime(row[field], '%H:%M')
            minutes = (int(row['end_time'][:2])*60 + int(row['end_time'][3:]) - int(row['start_time'][:2])*60 - int(row['start_time'][3:])) % 1440
            if minutes != duration: raise ValueError('Slot duration mismatch')
            if row['is_available']:
                slots.append(dict(start=row['start_time'], end=row['end_time'], duration=duration))
    return sorted([dict(t) for t in {tuple(sorted(s.items())) for s in slots}], key=lambda s:(s['start'], s['duration']))


def booking_window(html):
    values = re.findall(r'"maxAdvanceBookingDays"\s*:\s*(null|\d+)', html.replace('\\"', '"'))
    if len(set(values)) != 1:
        raise ValueError('Public booking window missing or ambiguous')
    days = 30 if values[0] == 'null' else int(values[0])
    if not 0 <= days <= 365:
        raise ValueError('Unexpected public booking window')
    return days


def is_slot_response(response):
    return response.request.method == 'POST' and response.url.split('?')[0] == BOOKING_URL.split('?')[0] and bool(response.request.headers.get('next-action'))


async def inspect(diagnostics='diagnostics'):
    actual = datetime.now(RIYADH)
    access = False
    async with async_playwright() as p:
        proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
        options = dict(headless=True, args=['--no-sandbox'])
        if os.getenv('CHROMIUM_EXECUTABLE'):
            options['executable_path'] = os.environ['CHROMIUM_EXECUTABLE']
        if proxy: options['proxy'] = {'server': proxy}
        browser = await p.chromium.launch(**options)
        page = await browser.new_page(timezone_id='Asia/Riyadh', locale='en-US', viewport={'width':1440,'height':1000})
        page.set_default_timeout(20000)
        bodies = []
        tasks = []
        network = []
        async def capture(response):
            if is_slot_response(response):
                network.append(dict(path='/book', status=response.status, method='POST'))
                try:
                    if response.ok: bodies.append(await response.text())
                except Exception: pass  # Canceled navigation isn't availability.
        def receive(response): tasks.append(asyncio.create_task(capture(response)))
        page.on('response', receive)
        try:
            response = await page.goto(BOOKING_URL, wait_until='networkidle', timeout=45000)
            access = bool(response and response.ok)
            if not access: raise ValueError(f'Booking page HTTP {response.status if response else "missing"}')
            await page.locator('button.rdp-day_button:visible').first.wait_for()
            if tasks: await asyncio.gather(*list(tasks))
            window = booking_window(await page.content())
            today = actual.date()
            start = today - timedelta(days=1 if actual.hour < 5 else 0)
            end = today + timedelta(days=window)
            # Calendar's enabled range is independent of cancelled/full inventory.
            expected = [(start+timedelta(days=i)).isoformat() for i in range((end-start).days+1)]
            enabled = set()
            months = {}
            for month_index in range(14):
                rows = await page.locator('button.rdp-day_button:visible').evaluate_all('(es)=>es.map(e=>({day:e.dataset.day,disabled:e.disabled,selected:e.dataset.selectedSingle}))')
                for row in rows:
                    d = datetime.strptime(row['day'], '%m/%d/%Y').date()
                    if not row['disabled']:
                        enabled.add(d.isoformat())
                    months[d.isoformat()] = row['disabled']
                if (end+timedelta(days=1)).isoformat() in months: break
                await page.get_by_role('button',name='Go to the Next Month',exact=True).locator('visible=true').first.click()
            if sorted(enabled) != expected or months.get((end+timedelta(days=1)).isoformat()) is not True:
                raise ValueError('Calendar does not match configured released-date window')
            # The app caches previously fetched date/duration combinations. Reuse only
            # validated responses fetched during THIS inspection, never disk cache.
            async def resolve(d, duration):
                for _ in range(100):
                    if tasks: await asyncio.gather(*list(tasks))
                    for body in reversed(bodies):
                        try: return parse_slots(body, d, duration)
                        except ValueError: pass
                    await asyncio.sleep(0.2)
                raise ValueError(f'No validated live response for {d}/{duration}; {len(bodies)} responses')

            slots = {}
            for d in expected:
                # Use the site's supported date deep-link. Server-action refreshes can
                # reset an unlinked date selection to today; the URL keeps it stable.
                if tasks: await asyncio.gather(*list(tasks))
                bodies.clear()
                await page.goto(BOOKING_URL+'&date='+d,wait_until='networkidle',timeout=45000)
                target = datetime.fromisoformat(d)
                data_day = f'{target.month}/{target.day}/{target.year}'
                selector = f'button.rdp-day_button[data-day="{data_day}"]:visible'
                # Date links must still agree with the publicly enabled calendar.
                for _ in range(14):
                    if await page.locator(selector).count(): break
                    await page.get_by_role('button',name='Go to the Next Month',exact=True).locator('visible=true').first.click()
                button = page.locator(selector).first
                if not await button.count() or await button.is_disabled():
                    raise ValueError('Released date not enabled in linked calendar')
                if await button.get_attribute('data-selected-single') != 'true':
                    raise ValueError('Public date deep-link no longer honored')
                slots[d] = []
                # Always select 110 first, forcing a fetch even if hydration canceled
                # its initial 55-minute response. Then use the ordinary 55 control.
                for duration in (110,55):
                    await page.get_by_role('button',name=f'{duration} Min',exact=True).locator('visible=true').first.click()
                    await page.wait_for_load_state('networkidle')
                    slots[d].extend(await resolve(d,duration))
                slots[d].sort(key=lambda s:(s['start'],s['duration']))
            # Do not persist a snapshot taken across Riyadh calendar rollover.
            if datetime.now(RIYADH).date() != today:
                raise ValueError('Riyadh date changed during inspection; retry required')
            folder=Path(diagnostics); folder.mkdir(parents=True,exist_ok=True)
            # Let the final server-action refresh finish painting the public slot controls.
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(folder/'last-calendar.png'),full_page=True)
            return dict(released_dates=expected, slots=slots, window_days=window,
                        observed_at=datetime.now(RIYADH).isoformat(), website_access_succeeded=True)
        except Exception as exc:
            folder = Path(diagnostics); folder.mkdir(parents=True,exist_ok=True)
            summaries=[]
            for body in bodies:
                summaries.append(re.findall(r'"(?:booking_date|start_time|end_time|is_available)":(?:"[^"]*"|true|false)',body)[:12])
            (folder/'response-summary.json').write_text(json.dumps(summaries,indent=2))
            stamp = datetime.now(RIYADH).strftime('%Y%m%dT%H%M%S')
            # Public calendar screenshot only; never cookies, headers or account data.
            try: await page.screenshot(path=str(folder/f'failure-{stamp}.png'),full_page=True)
            except Exception: pass
            (folder/f'failure-{stamp}.json').write_text(json.dumps(dict(at=datetime.now(RIYADH).isoformat(),
                website_access_succeeded=access, error_type=type(exc).__name__, network=network),indent=2))
            raise InspectionError(f'Public calendar inspection failed ({type(exc).__name__}): {str(exc)[:300]}',access) from None
        finally:
            for task in tasks:
                if not task.done(): task.cancel()
            await browser.close()
