import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from monitor.state import Store,observe

def snapshot(d,slots=True):
    return dict(released_dates=[d],slots={d:[dict(start='06:00',end='06:55',duration=55)] if slots else []})

class EdgeTests(unittest.TestCase):
    def test_month_rollover_and_cancellation_after_boundary_regression(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d)/'state.json')
            observe(s,snapshot('2026-10-31'),'2026-10-30T23:00:01+03:00')
            newer=snapshot('2026-11-01')
            self.assertEqual(observe(s,newer,'2026-10-31T00:00:01+03:00',newer),['2026-11-01'])
            observe(s,snapshot('2026-10-31'),'2026-10-31T01:00:01+03:00')
            self.assertEqual(observe(s,newer,'2026-10-31T02:00:01+03:00'),[])
            self.assertEqual(len(s.data['outbox']),1)
    def test_slot_must_be_present_in_both_confirmations(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(Path(d)/'state.json')
            observe(s,snapshot('2026-10-18'),'2026-10-17T23:00:01+03:00')
            self.assertEqual(observe(s,snapshot('2026-10-19'),'2026-10-18T00:00:01+03:00',snapshot('2026-10-19',False)),[])
    def test_missing_required_state_does_not_rebaseline(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'REQUIRE_EXISTING_STATE':'1'}):
            with self.assertRaises(ValueError): Store(Path(d)/'state.json')
