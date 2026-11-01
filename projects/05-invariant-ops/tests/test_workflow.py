from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import copy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from invariant_ops.store import WorkflowError, WorkflowStore


def command(command_id, operation, payload):
    return {'command_id': command_id, 'actor': 'operator1', 'operation': operation, 'payload': payload}


def order():
    return command('c1', 'create_order', {'order_id':'o1', 'supplier_id':'s1', 'currency':'GBP', 'quantity':10, 'unit_price_minor':125})


def receipt():
    return command('c2', 'record_receipt', {'receipt_id':'r1', 'order_id':'o1', 'quantity':4})


def invoice():
    return command('c3', 'post_invoice', {'invoice_id':'i1', 'order_id':'o1', 'supplier_id':'s1', 'currency':'GBP', 'quantity':4, 'amount_minor':500})


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = str(Path(self.temp.name) / 'workflow.sqlite')
        self.store = WorkflowStore(self.database)

    def tearDown(self):
        self.temp.cleanup()

    def test_order_receipt_invoice_and_durable_outbox(self):
        self.store.apply(order()); self.store.apply(receipt()); self.store.apply(invoice())
        events = WorkflowStore(self.database).outbox()
        self.assertEqual([event['event_type'] for event in events], ['create_order', 'record_receipt', 'post_invoice'])
        self.assertEqual(events[2]['payload']['result']['status'], 'posted')
        self.assertEqual(self.store.apply(invoice())['status'], 'posted')
        self.assertEqual(len(self.store.outbox()), 3)

    def test_conflicts_and_invariants_do_not_create_events(self):
        self.store.apply(order())
        changed = copy.deepcopy(order()); changed['payload']['quantity'] = 8
        with self.assertRaises(WorkflowError): self.store.apply(changed)
        with self.assertRaises(WorkflowError): self.store.apply(invoice())
        too_many = receipt(); too_many['payload']['quantity'] = 11
        with self.assertRaises(WorkflowError): self.store.apply(too_many)
        self.assertEqual(len(self.store.outbox()), 1)
        self.store.apply(receipt())
        wrong = invoice(); wrong['payload']['amount_minor'] = 499
        with self.assertRaises(WorkflowError): self.store.apply(wrong)
        self.assertEqual(len(self.store.outbox()), 2)

    def test_concurrent_duplicate_commands_commit_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: WorkflowStore(self.database).apply(order()), range(8)))
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(len(self.store.outbox()), 1)

    def test_outbox_failure_rolls_back_business_record(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.executescript("CREATE TRIGGER fail_outbox BEFORE INSERT ON outbox BEGIN SELECT RAISE(ABORT, 'blocked'); END;")
        with self.assertRaises(WorkflowError): self.store.apply(order())
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM orders').fetchone()[0], 0)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM commands').fetchone()[0], 0)

    def test_cli_applies_commands_across_process_restarts(self):
        env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
        input_file = Path(self.temp.name) / 'command.json'
        for item in (order(), receipt(), invoice()):
            input_file.write_text(json.dumps(item), encoding='utf-8')
            result = subprocess.run([sys.executable, '-m', 'invariant_ops', self.database, str(input_file)],
                                    cwd=self.temp.name, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.store.outbox()), 3)


if __name__ == '__main__':
    unittest.main()
