import tempfile
import unittest
from pathlib import Path
from monitor.state import Store
from monitor.notify import deliver, render, Rejected, Uncertain

class NotificationTests(unittest.TestCase):
    def make_store(self,path):
        s=Store(path)
        s.data['outbox']['release:2026-10-19']=dict(kind='release',status='pending',date='2026-10-19',slots=[dict(start='06:00',end='06:55',duration=55)],detected_at='2026-10-18T00:00:08+03:00',previous_latest='2026-10-18',new_latest='2026-10-19')
        s.save(); return s
    def test_durable_marker_precedes_send_and_restart_does_not_resend(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'s.json'; s=self.make_store(p); sent=[]
            def sender(text):
                self.assertEqual(Store(p).data['outbox']['release:2026-10-19']['status'],'sending')
                sent.append(text); return 123
            deliver(s,sender)
            deliver(Store(p),sender)
            self.assertEqual(len(sent),1)
            self.assertIn('Asia/Riyadh',sent[0])
            self.assertIn('06:00',sent[0])
    def test_ambiguous_network_outcome_not_automatically_retried(self):
        with tempfile.TemporaryDirectory() as d:
            s=self.make_store(Path(d)/'s.json')
            def sender(_): raise Uncertain('timeout')
            self.assertFalse(deliver(s,sender))
            self.assertEqual(s.data['outbox']['release:2026-10-19']['status'],'uncertain')
            self.assertFalse(deliver(s,lambda _:self.fail('resend')))
    def test_definite_rejection_is_retryable(self):
        with tempfile.TemporaryDirectory() as d:
            s=self.make_store(Path(d)/'s.json')
            def sender(_): raise Rejected('429')
            self.assertFalse(deliver(s,sender))
            self.assertEqual(s.data['outbox']['release:2026-10-19']['status'],'pending')
            self.assertTrue(deliver(s,lambda _:123))
    def test_interrupted_send_marked_uncertain(self):
        with tempfile.TemporaryDirectory() as d:
            s=self.make_store(Path(d)/'s.json')
            s.data['outbox']['release:2026-10-19']['status']='sending'; s.save()
            self.assertFalse(deliver(Store(s.path),lambda _:self.fail('resend')))
