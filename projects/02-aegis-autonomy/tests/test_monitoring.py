import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from aegis_autonomy.monitor import MonitoringError, ResidualMonitor
from aegis_autonomy.runner import evaluate_run
from aegis_autonomy.supervisor import Supervisor


def run_input():
    return {'schema_version': 1, 'monitor': {'method': 'normalised', 'threshold': 4},
            'supervisor': {'alarms_to_degrade': 2, 'clears_to_recover': 2, 'max_gap_seconds': 2},
            'observations': [{'timestamp_s': 0, 'residual': 1, 'variance': 1},
                             {'timestamp_s': 1, 'residual': 3, 'variance': 1},
                             {'timestamp_s': 2, 'residual': 3, 'variance': 1},
                             {'timestamp_s': 3, 'residual': 0, 'variance': 1},
                             {'timestamp_s': 4, 'residual': 0, 'variance': 1}]}


class MonitorTests(unittest.TestCase):
    def test_thresholds_and_hand_calculated_score(self):
        normalised = ResidualMonitor('normalised', 4)
        self.assertEqual(normalised.evaluate(4, 4)['score'], 4)
        self.assertEqual(normalised.evaluate(4, 4)['decision'], 'clear')
        self.assertEqual(normalised.evaluate(-6, 4)['score'], 9)
        self.assertEqual(normalised.evaluate(-6, 4)['decision'], 'alarm')
        self.assertEqual(ResidualMonitor('absolute', 3).evaluate(-4, 100)['score'], 4)
        self.assertEqual(normalised.evaluate(None, 1)['decision'], 'unavailable')

    def test_invalid_and_overflowing_inputs_fail(self):
        monitor = ResidualMonitor('normalised', 4)
        for residual, variance in ((True, 1), (1, 0), (1, -1), (None, -1), (math.inf, 1), (1e300, 1e-300)):
            with self.subTest(residual=residual, variance=variance), self.assertRaises(MonitoringError):
                monitor.evaluate(residual, variance)
        with self.assertRaises(MonitoringError): ResidualMonitor('unknown', 1)


class SupervisorTests(unittest.TestCase):
    def test_debounce_and_recovery(self):
        supervisor = Supervisor(2, 2, 2)
        actual = [supervisor.update(time, decision)['state'] for time, decision in enumerate(('clear', 'alarm', 'alarm', 'clear', 'clear'))]
        self.assertEqual(actual, ['nominal', 'nominal', 'degraded', 'degraded', 'nominal'])

    def test_missing_and_late_data_degrade_immediately(self):
        supervisor = Supervisor(2, 2, 2)
        supervisor.update(0, 'clear')
        self.assertEqual(supervisor.update(1, 'unavailable')['state'], 'degraded')
        supervisor.update(2, 'clear'); supervisor.update(3, 'clear')
        result = supervisor.update(6, 'clear')
        self.assertEqual((result['state'], result['reason']), ('degraded', 'observation gap'))

    def test_out_of_order_does_not_mutate_state(self):
        supervisor = Supervisor(1, 2, 2)
        supervisor.update(10, 'clear')
        with self.assertRaises(MonitoringError): supervisor.update(9, 'alarm')
        self.assertEqual(supervisor.last_time, 10)
        self.assertEqual(supervisor.state, 'nominal')


class RunTests(unittest.TestCase):
    def test_complete_trace_and_input_isolation(self):
        config = run_input(); before = copy.deepcopy(config)
        result = evaluate_run(config)
        self.assertEqual(config, before)
        self.assertEqual(result['observations_processed'], 5)
        self.assertEqual([row['supervisor']['state'] for row in result['trace']], ['nominal', 'nominal', 'degraded', 'degraded', 'nominal'])
        self.assertEqual(result['trace'][1]['assessment']['score'], 9)

    def test_cli_success_and_failure_do_not_overwrite_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'input.json'; output = root / 'result.json'
            source.write_text(json.dumps(run_input()), encoding='utf-8')
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            command = [sys.executable, '-m', 'aegis_autonomy', str(source), '--output', str(output)]
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['observations_processed'], 5)
            previous = output.read_bytes()
            source.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_bytes(), previous)
            self.assertIn('Duplicate field', result.stderr)


if __name__ == '__main__':
    unittest.main()
