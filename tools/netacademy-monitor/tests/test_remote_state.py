"""Exercise real git persistence used by Actions, without network or Telegram."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from monitor.state import Store,observe
from monitor.notify import deliver

class GitPersistenceTests(unittest.TestCase):
    def test_remote_sending_marker_is_pushed_before_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); remote=root/'remote.git'; working=root/'state'
            def git(*args):
                return subprocess.run(['git',*map(str,args)],check=True,capture_output=True,text=True).stdout
            git('init','--bare',remote)
            git('init','--initial-branch=monitor-state',working)
            git('-C',working,'config','user.name','Test Monitor')
            git('-C',working,'config','user.email','test@example.invalid')
            git('-C',working,'remote','add','origin',remote)
            with patch.dict(os.environ,{'STATE_GIT':'1','REQUIRE_EXISTING_STATE':'0'}):
                s=Store(working/'state.json')
                def snapshot(day):
                    return {'released_dates':[day],'slots':{day:[dict(start='06:00',end='06:55',duration=55)]}}
                observe(s,snapshot('2026-10-18'),'2026-10-17T23:00:01+03:00')
                next_day=snapshot('2026-10-19')
                observe(s,next_day,'2026-10-18T00:00:01+03:00',next_day)
                def remote_data():
                    return json.loads(git('--git-dir',remote,'show','monitor-state:state.json'))
                def sender(_):
                    self.assertEqual(remote_data()['outbox']['release:2026-10-19']['status'],'sending')
                    return 321
                self.assertTrue(deliver(s,sender))
                self.assertEqual(remote_data()['outbox']['release:2026-10-19']['status'],'sent')
                self.assertTrue(deliver(Store(s.path),lambda _:self.fail('Duplicate send after restart')))
