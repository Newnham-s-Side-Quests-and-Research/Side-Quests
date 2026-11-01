import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delivery_match.matching import MatchError,match


def values():
    order={'order_id':'o1','supplier_id':'s1','product_id':'p1','unit':'item','ordered_quantity':10,'currency':'GBP','unit_price_minor':125}
    receipt={'receipt_id':'r1','order_id':'o1','product_id':'p1','unit':'item','delivered_quantity':10,'accepted_quantity':7}
    invoice={'invoice_id':'i1','order_id':'o1','supplier_id':'s1','product_id':'p1','unit':'item','quantity':10,'currency':'GBP','unit_price_minor':125}
    return order,[receipt],invoice


class MatchTests(unittest.TestCase):
    def test_partial_acceptance_has_reviewable_proposal(self):
        order,receipts,invoice=values();original=copy.deepcopy((order,receipts,invoice))
        result=match(order,receipts,invoice)
        self.assertEqual((order,receipts,invoice),original)
        self.assertEqual(result['status'],'review')
        self.assertEqual(result['proposed_credit_quantity'],3)
        self.assertEqual(result['proposed_credit_minor'],375)
        self.assertEqual(result['receipt_ids'],['r1'])
        self.assertIn('Previous invoices are not tracked and must be reviewed separately',result['limitations'])

    def test_no_excess_is_matched(self):
        order,receipts,invoice=values();invoice['quantity']=7
        self.assertEqual(match(order,receipts,invoice)['status'],'matched')

    def test_missing_or_mismatched_records_are_unresolved(self):
        order,receipts,invoice=values()
        self.assertEqual(match(order,[],invoice)['status'],'unresolved')
        invoice['unit']='case'
        self.assertEqual(match(order,receipts,invoice)['reason'],'invoice does not match order terms')

    def test_duplicate_or_impossible_receipt_fails(self):
        order,receipts,invoice=values()
        with self.assertRaises(MatchError):match(order,receipts+copy.deepcopy(receipts),invoice)
        receipts[0]['accepted_quantity']=11
        with self.assertRaises(MatchError):match(order,receipts,invoice)

    def test_command_end_to_end(self):
        order,receipts,invoice=values()
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'input.json'
            source.write_text(json.dumps({'order':order,'receipts':receipts,'invoice':invoice}),encoding='utf-8')
            env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
            result=subprocess.run([sys.executable,'-m','delivery_match',str(source)],cwd=tmp,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['proposed_credit_minor'],375)


if __name__=='__main__':unittest.main()
