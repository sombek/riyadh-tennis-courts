"""Telegram delivery with durable intent and explicit uncertain outcomes."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from .state import BOOKING_URL

class Rejected(RuntimeError): pass
class Uncertain(RuntimeError): pass


def render(event):
    if event['kind'] == 'test':
        return f"🎾 Tennis monitor TEST notification. Not a booking release.\nDetected at: {event['detected_at']} (Asia/Riyadh)\n{BOOKING_URL}"
    if event['kind'] == 'health':
        return (f"⚠️ TENNIS MONITOR FAILURE (not a booking alert)\n"
                f"Consecutive failed checks: {event['failures']}\n"
                f"Detected at: {event['detected_at']} (Asia/Riyadh)\n"
                f"Error: {event['error']}\nBaseline preserved. Check workflow logs.\n{BOOKING_URL}")
    when = datetime.fromisoformat(event['detected_at']).astimezone(ZoneInfo('Asia/Riyadh'))
    day = datetime.fromisoformat(event['date']).strftime('%A, %B %d, %Y')
    slots = ', '.join(f"{s['start']}–{s['end']} ({s['duration']} min)" for s in event['slots'])
    return (f"🎾 NEW TENNIS BOOKING DAY OPEN!\n\nNew date: {day}\n"
            f"Detected at: {when.strftime('%Y-%m-%d %I:%M:%S %p')} (Asia/Riyadh, UTC+3)\n"
            f"Slots (Riyadh): {slots}\n"
            f"Previous last bookable date: {event['previous_latest']}\n"
            f"New last bookable date: {event['new_latest']}\n"
            f"Previous successful check: {event.get('last_success_at') or 'unknown'}\n"
            f"First observed time; release may have occurred between checks.\n"
            f"Post-midnight slots retain the venue's booking-date label.\n\nBook now:\n{BOOKING_URL}")


def send_telegram(text):
    token, chat = os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat:
        raise Rejected('Telegram credentials missing')
    payload = json.dumps(dict(chat_id=chat, text=text[:4000], disable_web_page_preview=True)).encode()
    request = urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage',data=payload,headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        # A response explicitly rejecting sendMessage is safe to retry next check.
        if 400 <= exc.code < 500: raise Rejected(f'Telegram rejected message: HTTP {exc.code}') from None
        raise Uncertain(f'Telegram server error: HTTP {exc.code}') from None
    except Exception:
        # Never include an exception URL because it contains the bot token.
        raise Uncertain('Telegram network failure; delivery outcome unknown') from None
    if result.get('ok') is not True or not isinstance(result.get('result',{}).get('message_id'),int):
        raise Uncertain('Telegram acknowledgment missing or invalid')
    return result['result']['message_id']


def deliver(store, sender=send_telegram):
    success = True
    for event in store.data['outbox'].values():
        if event['status'] == 'sent': continue
        if event['status'] in ('sending','uncertain'):
            event['status'] = 'uncertain'
            store.save()
            success = False
            continue
        event['status'] = 'sending'
        store.save()  # Fail closed if durable persistence/push fails.
        try:
            message_id = sender(render(event))
        except Rejected as exc:
            event['status'] = 'pending'; event['delivery_error'] = str(exc)
            success = False
        except Uncertain as exc:
            event['status'] = 'uncertain'; event['delivery_error'] = str(exc)
            success = False
        else:
            event['status'] = 'sent'; event['message_id'] = message_id
            event['sent_at'] = datetime.now(ZoneInfo('Asia/Riyadh')).isoformat()
            event.pop('delivery_error',None)
        store.save()
    return success
