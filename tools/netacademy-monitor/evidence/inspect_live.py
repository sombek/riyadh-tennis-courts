import asyncio, json, os
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    report = {'url': 'https://netacademy.sa/book?activity=tennis&type=court', 'actual_execution_time': datetime.now(ZoneInfo('Asia/Riyadh')).isoformat(), 'website_access_succeeded': False, 'calendar_parsed': False, 'errors': []}
    async with async_playwright() as p:
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        browser = await p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'], proxy={'server':proxy} if proxy else None)
        page = await browser.new_page(timezone_id='Asia/Riyadh')
        page.on('requestfailed', lambda req: report['errors'].append({'url':req.url.split('?')[0], 'failure':req.failure}))
        try:
            response = await page.goto(report['url'], wait_until='networkidle', timeout=45000)
            report['http_status'] = response.status if response else None
            report['website_access_succeeded'] = bool(response and response.ok)
            report['title'] = await page.title()
            report['visible_text'] = (await page.locator('body').inner_text())[:12000]
        except Exception as exc:
            report['errors'].append(str(exc))
        await page.screenshot(path='/workspace/tennis-monitor/evidence/live-access.png', full_page=True)
        await browser.close()
    Path('/workspace/tennis-monitor/evidence/live-access.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

asyncio.run(main())
