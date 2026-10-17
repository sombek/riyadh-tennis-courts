"""One serialized, observable check. Run: python -m monitor."""
import argparse
import asyncio
import fcntl
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from .browser import inspect, RIYADH
from .state import Store, observe, failure
from .notify import deliver


def now(): return datetime.now(RIYADH).isoformat()

async def run(args, store, log):
    snapshot = None
    for attempt in range(1,4):
        try:
            snapshot = await inspect(args.diagnostics)
            log['website_access_succeeded'] = True
            log['calendar_parsed'] = True
            old = store.data['latest_released']
            confirmation = None
            if old and snapshot['released_dates'][-1] > old:
                await asyncio.sleep(2)
                confirmation = await inspect(args.diagnostics)
            found = observe(store,snapshot,now(),confirmation)
            log.update(latest_bookable_date=max((d for d,s in snapshot['slots'].items() if s),default=None),
                latest_released_date=snapshot['released_dates'][-1],
                bookable_dates=sum(bool(s) for s in snapshot['slots'].values()),
                available_slots=sum(len(s) for s in snapshot['slots'].values()),
                new_dates=found, new_date_detected=bool(found), attempts=attempt)
            break
        except Exception as exc:
            log['website_access_succeeded'] = log['website_access_succeeded'] or getattr(exc,'access_succeeded',False)
            log['errors'].append(dict(attempt=attempt,type=type(exc).__name__,message=str(exc)[:400]))
            snapshot = None
            if attempt < 3: await asyncio.sleep(attempt*2)
    if snapshot is None:
        log['calendar_parsed'] = False
        failure(store,now(),log['errors'][-1]['message'])
    if args.test_telegram:
        store.data['outbox'].setdefault('test:installation',dict(kind='test',status='pending',detected_at=now()))
        store.save()
    configured = bool(os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'))
    log['telegram_configured'] = configured
    unsent = any(e['status'] != 'sent' for e in store.data['outbox'].values())
    if unsent:
        log['telegram_notification_succeeded'] = deliver(store)
    else:
        log['telegram_notification_succeeded'] = None  # No notification attempted.
    log['telegram_delivery_errors'] = [dict(event=key,status=e['status'],error=e.get('delivery_error','Interrupted or unknown delivery')) for key,e in store.data['outbox'].items() if e['status'] != 'sent']
    log['pending_or_uncertain_notifications'] = sum(e['status'] != 'sent' for e in store.data['outbox'].values())
    return bool(snapshot is not None and not log['pending_or_uncertain_notifications'] and
                (configured or os.getenv('REQUIRE_TELEGRAM') != '1'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--state',default=os.getenv('STATE_PATH','runtime/state.json'))
    parser.add_argument('--diagnostics',default='diagnostics')
    parser.add_argument('--log',default='logs/checks.jsonl')
    parser.add_argument('--test-telegram',action='store_true')
    args=parser.parse_args()
    started=time.monotonic(); actual=datetime.now(RIYADH)
    scheduled=os.getenv('SCHEDULED_AT')
    log=dict(scheduled_execution_time=scheduled, scheduled_time_is_estimate=os.getenv('SCHEDULED_TIME_IS_ESTIMATE')=='1',
        nominal_hour=actual.replace(minute=0,second=0,microsecond=0).isoformat(),
        actual_execution_time=actual.isoformat(), timezone='Asia/Riyadh',
        website_access_succeeded=False,calendar_parsed=False,latest_bookable_date=None,
        bookable_dates=None,available_slots=None,new_date_detected=False,new_dates=[],
        telegram_notification_succeeded=None,errors=[])
    if scheduled:
        log['schedule_delay_seconds']=(actual-datetime.fromisoformat(scheduled)).total_seconds()
    success=False
    try:
        Path(args.state).parent.mkdir(parents=True,exist_ok=True)
        with open(args.state+'.lock','w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            store=Store(args.state)
            success=asyncio.run(run(args,store,log))
    except Exception as exc:
        log['errors'].append(dict(type=type(exc).__name__,message=str(exc)[:400]))
    finally:
        log['duration_seconds']=round(time.monotonic()-started,3)
        log['check_succeeded']=success
        text=json.dumps(log)
        Path(args.log).parent.mkdir(parents=True,exist_ok=True)
        with open(args.log,'a') as f: f.write(text+'\n')
        print(text,flush=True)
    return 0 if success else 1

if __name__=='__main__': sys.exit(main())
