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
from freight_audit.audit import AuditError, audit


def values():
    shipment={'shipment_id':'s1','carrier':'c1','service':'standard','zone':'z1','date':'2026-01-31','weight_g':5000,'accessorials':['lift']}
    card={'tariff_id':'t1','carrier':'c1','service':'standard','zone':'z1','currency':'GBP',
          'start_date':'2026-01-01','end_date':'2026-01-31','min_weight_g':1,'max_weight_g':5000,
          'base_minor':1001,'fuel_bps':500,'accessorials':{'lift':200}}
    invoice={'shipment_id':'s1','currency':'GBP','lines':[{'line_id':'a','component':'base','amount_minor':1001},
             {'line_id':'b','component':'fuel','amount_minor':50},{'line_id':'c','component':'lift','amount_minor':250}]}
    return shipment,[card],invoice


class AuditTests(unittest.TestCase):
    def test_hand_calculated_components_and_provenance(self):
        shipment,cards,invoice=values();before=copy.deepcopy((shipment,cards,invoice))
        result=audit(shipment,cards,invoice)
        self.assertEqual((shipment,cards,invoice),before)
        self.assertEqual(result['status'],'discrepancy')
        self.assertEqual(result['difference_minor'],50)
        self.assertEqual(result['components'][1]['expected_minor'],50)
        self.assertEqual(result['components'][2]['line_id'],'c')
        self.assertEqual(result['components'][2]['tariff_id'],'t1')

    def test_rounding_and_matching(self):
        shipment,cards,invoice=values()
        cards[0]['base_minor']=1010;invoice['lines'][0]['amount_minor']=1010
        invoice['lines'][1]['amount_minor']=51;invoice['lines'][2]['amount_minor']=200
        self.assertEqual(audit(shipment,cards,invoice)['status'],'matched')

    def test_missing_or_ambiguous_rates_are_unresolved(self):
        shipment,cards,invoice=values()
        shipment['date']='2026-02-01'
        self.assertEqual(audit(shipment,cards,invoice)['reason'],'no matching tariff')
        shipment,cards,invoice=values();second=copy.deepcopy(cards[0]);second['tariff_id']='t2';cards.append(second)
        self.assertEqual(audit(shipment,cards,invoice)['reason'],'ambiguous tariffs')

    def test_currency_and_missing_component_are_unresolved(self):
        shipment,cards,invoice=values();invoice['currency']='USD'
        self.assertEqual(audit(shipment,cards,invoice)['reason'],'currency mismatch')
        shipment,cards,invoice=values();invoice['lines'].pop()
        self.assertEqual(audit(shipment,cards,invoice)['reason'],'missing or unexpected invoice component')

    def test_duplicate_line_and_invalid_date_fail(self):
        shipment,cards,invoice=values();invoice['lines'][1]['line_id']='a'
        with self.assertRaises(AuditError):audit(shipment,cards,invoice)
        shipment,cards,invoice=values();shipment['date']='2026-02-30'
        with self.assertRaises(AuditError):audit(shipment,cards,invoice)

    def test_command_end_to_end(self):
        shipment,cards,invoice=values()
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'input.json'
            source.write_text(json.dumps({'shipment':shipment,'rate_cards':cards,'invoice':invoice}),encoding='utf-8')
            env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
            command=[sys.executable,'-m','freight_audit',str(source)]
            result=subprocess.run(command,cwd=tmp,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['difference_minor'],50)


if __name__=='__main__':unittest.main()
