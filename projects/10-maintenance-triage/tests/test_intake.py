from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from maintenance_triage.intake import IntakeError,IntakeQueue


def report():return {'report_id':'r1','unit_id':'u1','timestamp':'2026-01-01T12:00:00Z','text':'There is a smell of gas.'}


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=str(Path(self.temp.name)/'queue.sqlite')
        self.queue=IntakeQueue(self.db,['gas','fire'])
    def tearDown(self):self.temp.cleanup()

    def test_priority_and_unspecified_reports_both_require_human_review(self):
        self.assertEqual(self.queue.submit(report())['route'],'priority_human_review')
        ordinary=report();ordinary['report_id']='r2';ordinary['text']='The window is loose.'
        self.assertEqual(self.queue.submit(ordinary)['route'],'human_review')
        unrelated=report();unrelated['report_id']='r3';unrelated['text']='The sign says vegas.'
        self.assertEqual(self.queue.submit(unrelated)['route'],'human_review')

    def test_idempotency_conflict_and_persistence(self):
        first=self.queue.submit(report())
        self.assertEqual(IntakeQueue(self.db,['gas','fire']).submit(report()),first)
        changed=report();changed['text']='Different report'
        with self.assertRaises(IntakeError):self.queue.submit(changed)
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM reports').fetchone()[0],1)

    def test_concurrent_duplicate_reports_create_one_record(self):
        with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(lambda _:self.queue.submit(report()),range(6)))
        self.assertTrue(all(result==results[0] for result in results))
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM reports').fetchone()[0],1)

    def test_storage_failure_is_not_acknowledged(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.executescript("CREATE TRIGGER fail_insert BEFORE INSERT ON reports BEGIN SELECT RAISE(ABORT,'blocked'); END;")
        with self.assertRaises(sqlite3.IntegrityError):self.queue.submit(report())
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM reports').fetchone()[0],0)

    def test_invalid_time_or_text_is_rejected(self):
        value=report();value['timestamp']='2026-01-01T12:00:00'
        with self.assertRaises(IntakeError):self.queue.submit(value)
        value=report();value['text']=' '
        with self.assertRaises(IntakeError):self.queue.submit(value)

    def test_command_persists_report_and_returns_route(self):
        source=Path(self.temp.name)/'input.json'
        source.write_text(json.dumps({'priority_phrases':['gas','fire'],'report':report()}),encoding='utf-8')
        env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
        result=subprocess.run([sys.executable,'-m','maintenance_triage',self.db,str(source)],cwd=self.temp.name,env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['route'],'priority_human_review')


if __name__=='__main__':unittest.main()
