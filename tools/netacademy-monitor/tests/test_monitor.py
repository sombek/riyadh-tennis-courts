import json
import tempfile
import unittest
from pathlib import Path
from monitor.state import Store, observe, failure
from monitor.browser import parse_slots

NOW = '2026-10-17T18:00:01+03:00'

def snap(last='2026-10-18', available=True):
    dates = ['2026-10-17','2026-10-18'] + (['2026-10-19'] if last.endswith('19') else [])
    return {'released_dates': dates, 'slots': {d: ([{'start':'06:00','end':'06:55','duration':55}] if available else []) for d in dates}}

class DetectionTests(unittest.TestCase):
    def test_baseline_restart_unchanged_no_alert(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            store=Store(p)
            self.assertEqual(observe(store, snap(), NOW), [])
            store=Store(p)
            self.assertEqual(observe(store, snap(), NOW), [])
            self.assertEqual(store.data['latest_released'],'2026-10-18')
            self.assertEqual(store.data['outbox'],{})
    def test_new_release_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d)/'s.json'); observe(s,snap(),NOW)
            with self.assertRaises(ValueError): observe(s,snap('2026-10-19'),NOW)
            self.assertEqual(s.data['latest_released'],'2026-10-18')
            self.assertEqual(observe(s,snap('2026-10-19'),NOW,snap('2026-10-19')),['2026-10-19'])
            self.assertEqual(observe(s,snap('2026-10-19'),NOW),[])
            self.assertEqual(len(s.data['outbox']),1)
    def test_cancellation_on_fully_booked_released_day_is_silent(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d)/'s.json'); observe(s,snap(available=False),NOW)
            self.assertEqual(observe(s,snap(),NOW),[])
    def test_new_fully_booked_release_does_not_alert_later_cancellation(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d)/'s.json'); observe(s,snap(),NOW)
            self.assertEqual(observe(s,snap('2026-10-19',False),NOW,snap('2026-10-19',False)),[])
            self.assertEqual(observe(s,snap('2026-10-19'),NOW),[])
    def test_failure_preserves_baseline_and_one_health_event_per_episode(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d)/'s.json'); observe(s,snap(),NOW)
            for _ in range(5): failure(s,NOW,'network timeout')
            self.assertEqual(s.data['latest_released'],'2026-10-18')
            self.assertEqual(len(s.data['outbox']),1)
            self.assertEqual(next(iter(s.data['outbox'].values()))['kind'],'health')
    def test_corrupt_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'s.json'; p.write_text('{broken')
            with self.assertRaises(ValueError): Store(p)

class ParsingTests(unittest.TestCase):
    def test_live_response_fixture(self):
        records=json.loads(Path('evidence/october18-network.json').read_text())
        found=[]
        for r in records:
            try: found += parse_slots(r['body'],'2026-10-18',55)
            except ValueError: pass
        self.assertIn({'start':'06:00','end':'06:55','duration':55},found)
    def test_failed_or_malformed_not_empty_inventory(self):
        for body in ['{}','<html>error</html>','1:{"success":false}', '1:{"success":true,"results":[]}']:
            with self.subTest(body=body), self.assertRaises(ValueError): parse_slots(body,'2026-10-18',55)
