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
from infra_resilience.diagnosis import DiagnosisError, diagnose


def example():
    return {'schema_version': 1,
            'catalogue': [{'cause_id': 'drive', 'signals': ['motor_hot', 'belt_stopped']},
                          {'cause_id': 'sensor', 'signals': ['belt_stopped', 'sensor_offline']}],
            'events': [{'event_id': 'e2', 'timestamp_ms': 20, 'signal': 'belt_stopped', 'quality': 'valid', 'alarm': True},
                       {'event_id': 'e1', 'timestamp_ms': 10, 'signal': 'motor_hot', 'quality': 'valid', 'alarm': True}]}


class DiagnosisTests(unittest.TestCase):
    def test_rankings_reference_actual_event_ids(self):
        data = example(); before = copy.deepcopy(data)
        result = diagnose(data)
        self.assertEqual(data, before)
        self.assertEqual(result['status'], 'ranked')
        self.assertEqual(result['ranking'][0], {'cause_id': 'drive', 'score': 2, 'evidence_ids': ['e2', 'e1']})
        self.assertEqual(result['unavailable_signals'], ['sensor_offline'])
        self.assertEqual(result, diagnose(dict(data, events=list(reversed(data['events'])))))

    def test_ties_and_missing_data_are_explicit(self):
        data = example(); data['events'] = [data['events'][0]]
        result = diagnose(data)
        self.assertEqual(result['status'], 'ambiguous')
        self.assertEqual([item['cause_id'] for item in result['ranking']], ['drive', 'sensor'])
        data['events'][0]['quality'] = 'stale'; data['events'][0]['alarm'] = None
        result = diagnose(data)
        self.assertEqual(result['status'], 'unknown')
        self.assertIn('belt_stopped', result['unavailable_signals'])

    def test_newest_event_and_same_time_order_are_deterministic(self):
        data = example()
        data['events'].extend([{'event_id':'a', 'timestamp_ms':30, 'signal':'motor_hot', 'quality':'valid', 'alarm':True},
                               {'event_id':'z', 'timestamp_ms':30, 'signal':'motor_hot', 'quality':'valid', 'alarm':False}])
        result = diagnose(data)
        self.assertEqual(result['status'], 'ambiguous')
        self.assertIn('motor_hot', result['unavailable_signals'])
        self.assertTrue(all('a' not in item['evidence_ids'] for item in result['ranking']))

    def test_newer_reading_clears_a_same_time_conflict(self):
        data = example()
        data['events'].extend([{'event_id':'a', 'timestamp_ms':30, 'signal':'motor_hot', 'quality':'valid', 'alarm':True},
                               {'event_id':'z', 'timestamp_ms':30, 'signal':'motor_hot', 'quality':'valid', 'alarm':False},
                               {'event_id':'new', 'timestamp_ms':31, 'signal':'motor_hot', 'quality':'valid', 'alarm':True}])
        result = diagnose(data)
        self.assertEqual(result['status'], 'ranked')
        self.assertNotIn('motor_hot', result['unavailable_signals'])
        self.assertIn('new', result['ranking'][0]['evidence_ids'])

    def test_duplicate_and_invalid_events_fail(self):
        data = example(); data['events'].append(copy.deepcopy(data['events'][0]))
        with self.assertRaises(DiagnosisError): diagnose(data)
        data = example(); data['events'][0]['quality'] = 'missing'
        with self.assertRaises(DiagnosisError): diagnose(data)

    def test_command_writes_report_and_preserves_output_on_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'input.json'; output = root / 'output.json'
            source.write_text(json.dumps(example()), encoding='utf-8')
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            command = [sys.executable, '-m', 'infra_resilience', str(source), '--output', str(output)]
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['status'], 'ranked')
            before = output.read_bytes()
            source.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
