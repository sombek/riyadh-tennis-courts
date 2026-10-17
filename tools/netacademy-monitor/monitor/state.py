"""Atomic JSON state and release detection; failed observations never erase baseline."""
import json
import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path

BOOKING_URL = 'https://netacademy.sa/book?activity=tennis&type=court'

class Store:
    def __init__(self, path):
        self.path = Path(path)
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
            if not isinstance(self.data, dict) or self.data.get('version') != 1:
                raise ValueError('Invalid state schema; refusing to reset baseline')
            for key in ('outbox', 'observations', 'seen_dates', 'failure_streak'):
                if key not in self.data:
                    raise ValueError('Incomplete state; refusing to reset baseline')
        else:
            if os.getenv('REQUIRE_EXISTING_STATE') == '1':
                raise ValueError('Required persisted state is missing; refusing silent rebaseline')
            self.data = self.initial()

    @staticmethod
    def initial():
        return dict(version=1, latest_released=None, seen_dates=[], observations=[],
                    failure_streak=0, failure_episode=None, outbox={})

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix='.state-')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(self.data, f, indent=2, sort_keys=True)
                f.write('\n'); f.flush(); os.fsync(f.fileno())
            os.replace(tmp, self.path)
            directory = os.open(self.path.parent, os.O_DIRECTORY)
            try: os.fsync(directory)
            finally: os.close(directory)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
        # Every durable outbox transition must reach remote storage BEFORE sending.
        if os.getenv('STATE_GIT') == '1':
            for args in (['add', self.path.name], ['commit', '--allow-empty', '-m', 'Persist monitor state'], ['push', 'origin', 'HEAD:monitor-state']):
                subprocess.run(['git', '-C', str(self.path.parent), *args], check=True, capture_output=True)


def validate(snapshot):
    dates = snapshot['released_dates']
    if not dates or dates != sorted(set(dates)):
        raise ValueError('Missing, unordered or duplicate released dates')
    for d in dates:
        date.fromisoformat(d)
        if d not in snapshot['slots'] or not isinstance(snapshot['slots'][d], list):
            raise ValueError('Missing slot result for released date')
    return dates


def observe(store, snapshot, now, confirmation=None):
    dates = validate(snapshot)
    state = store.data
    old = state['latest_released']
    candidates = [d for d in dates if old and d > old]
    if candidates:
        if confirmation is None or validate(confirmation) != dates:
            raise ValueError('Release boundary requires a matching independent observation')
    alerts = []
    for d in candidates:
        # A slot must be available in BOTH fetches; never alert on a transient response.
        slots = [s for s in snapshot['slots'][d] if s in confirmation['slots'][d]]
        if slots:
            key = 'release:' + d
            state['outbox'].setdefault(key, dict(kind='release', status='pending', date=d,
                slots=slots, detected_at=now,
                previous_latest=(state['observations'][-1]['latest_bookable'] if state['observations'] else None),
                new_latest=max((day for day in dates if snapshot['slots'][day]),default=None),
                previous_release_boundary=old, new_release_boundary=dates[-1],
                last_success_at=state.get('last_success_at')))
            alerts.append(d)
    state['latest_released'] = max(old or dates[-1], dates[-1])
    state['seen_dates'] = sorted(set(state['seen_dates']) | set(dates))
    state['last_success_at'] = now
    state['failure_streak'] = 0
    state['failure_episode'] = None
    state['observations'].append(dict(at=now, latest_released=dates[-1],
        latest_bookable=max((d for d in dates if snapshot['slots'][d]), default=None),
        released_dates=dates, slots=snapshot['slots'], new_dates=alerts))
    store.save()
    return alerts


def failure(store, now, error):
    state = store.data
    state['failure_streak'] += 1
    if not state['failure_episode']:
        state['failure_episode'] = now
    state['last_failure'] = dict(at=now, error=error)
    if state['failure_streak'] >= 3:
        key = 'health:' + state['failure_episode']
        state['outbox'].setdefault(key, dict(kind='health', status='pending', detected_at=now,
            failures=state['failure_streak'], error=error))
    store.save()
