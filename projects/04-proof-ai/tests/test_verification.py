import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from proof_ai.verification import VerificationError, verify_invoice


def inputs():
    values = {'invoice_id': 'INV42', 'supplier_id': 'SUP1', 'currency': 'GBP',
              'subtotal': '100.10', 'tax': '20.02', 'total': '120.12'}
    source_text = ' | '.join(values.values())
    extraction = {'status': 'complete', 'fields': {}}
    for key, value in values.items():
        start = source_text.index(value)
        extraction['fields'][key] = {'value': value, 'source_id': 'page1', 'start': start, 'end': start + len(value)}
    policy = {'supplier_id': 'SUP1', 'currency': 'GBP', 'known_sources': ['page1'],
              'source_texts': {'page1': source_text}, 'existing_invoice_ids': ['INV41'], 'rule_version': '1'}
    return extraction, policy


class VerificationTests(unittest.TestCase):
    def test_consistent_amounts_and_known_source_pass_the_checks(self):
        extraction, policy = inputs(); before = copy.deepcopy((extraction, policy))
        result = verify_invoice(extraction, policy)
        self.assertEqual((extraction, policy), before)
        self.assertEqual(result['decision'], 'checks_passed')
        self.assertTrue(all(item['passed'] for item in result['checks']))
        self.assertIn('Consistent fields and arithmetic do not prove the document is genuine or correct', result['limitations'])

    def test_missing_conflicting_or_failed_extraction_requires_review(self):
        for variant in ('missing', 'amount', 'duplicate', 'supplier', 'currency', 'source', 'failed', 'float'):
            extraction, policy = inputs()
            if variant == 'missing': del extraction['fields']['total']
            if variant == 'amount': extraction['fields']['total']['value'] = '120.13'
            if variant == 'duplicate': policy['existing_invoice_ids'].append('INV42')
            if variant == 'supplier': extraction['fields']['supplier_id']['value'] = 'OTHER'
            if variant == 'currency': extraction['fields']['currency']['value'] = 'USD'
            if variant == 'source': extraction['fields']['tax']['source_id'] = 'unknown'
            if variant == 'failed': extraction['status'] = 'failed'
            if variant == 'float': extraction['fields']['total']['value'] = 120.12
            with self.subTest(variant=variant):
                result = verify_invoice(extraction, policy)
                self.assertEqual(result['decision'], 'review')
                self.assertTrue(any(not check['passed'] for check in result['checks']))

    def test_invalid_policy_is_rejected(self):
        extraction, policy = inputs()
        policy['known_sources'] = ['page1', 'page1']
        with self.assertRaises(VerificationError): verify_invoice(extraction, policy)

    def test_consistent_but_wrong_values_are_not_claimed_as_proven(self):
        extraction, policy = inputs()
        extraction['fields']['subtotal']['value'] = '200.00'
        extraction['fields']['tax']['value'] = '40.00'
        extraction['fields']['total']['value'] = '240.00'
        text = ' | '.join(item['value'] for item in extraction['fields'].values())
        policy['source_texts']['page1'] = text
        for item in extraction['fields'].values():
            item['start'] = text.index(item['value'])
            item['end'] = item['start'] + len(item['value'])
        result = verify_invoice(extraction, policy)
        self.assertEqual(result['decision'], 'checks_passed')
        self.assertIn('Consistent fields and arithmetic do not prove the document is genuine or correct', result['limitations'])

    def test_missing_or_false_source_span_requires_review(self):
        extraction, policy = inputs()
        del extraction['fields']['total']['start']; del extraction['fields']['total']['end']
        result = verify_invoice(extraction, policy)
        self.assertEqual(result['decision'], 'review')
        self.assertTrue(any(check['rule'] == 'source_span_matches' and not check['passed'] for check in result['checks']))
        extraction, policy = inputs()
        extraction['fields']['total']['start'] = 0
        self.assertEqual(verify_invoice(extraction, policy)['decision'], 'review')
        extraction, policy = inputs()
        policy['source_texts']['page1'] = 'Changed source text'
        self.assertEqual(verify_invoice(extraction, policy)['decision'], 'review')

    def test_cli_validates_and_preserves_existing_output_on_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'input.json'; output = root / 'output.json'
            extraction, policy = inputs()
            source.write_text(json.dumps({'schema_version':1, 'extraction':extraction, 'policy':policy}), encoding='utf-8')
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            command = [sys.executable, '-m', 'proof_ai', str(source), '--output', str(output)]
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['decision'], 'checks_passed')
            before = output.read_bytes()
            source.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
