import copy
import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.simulation import simulate
from drone_archive.telemetry import TelemetryError, build_snapshot

class TelemetryTests(unittest.TestCase):
    def setUp(self):
        config = json.loads((ROOT / 'fixtures' / 'signal-scenario.json').read_text(encoding='utf-8'))
        self.trace = simulate(config)['trace']

    def test_unknown_hardware_is_not_invented(self):
        snapshot = build_snapshot(self.trace[0])
        self.assertEqual(snapshot['source'], 'synthetic simulation')
        self.assertEqual(len(snapshot['motors']), 4)
        self.assertTrue(all(x == 'not modelled' for x in snapshot['motors'].values()))
        self.assertEqual(snapshot['battery'], 'not modelled')
        self.assertEqual(snapshot['position'], 'not modelled')

    def test_missing_signal_and_links_are_preserved(self):
        self.assertIsNone(build_snapshot(self.trace[35])['signals']['altitude_m'])
        self.assertFalse(build_snapshot(self.trace[10])['links']['wifi_available'])
        self.assertFalse(build_snapshot(self.trace[25])['links']['bluetooth_available'])

    def test_cli_writes_only_synthetic_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            output = Path(tmp) / 'telemetry.json'
            result = subprocess.run([sys.executable, '-m', 'drone_archive', 'telemetry', str(ROOT / 'fixtures' / 'signal-scenario.json'), '--output', str(output)], cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = json.loads(output.read_text(encoding='utf-8'))['trace']
            self.assertEqual(len(rows), 50)
            self.assertTrue(all(row['source'] == 'synthetic simulation' for row in rows))

    def test_invalid_samples_are_rejected(self):
        for key, value in [('time_s', -1), ('barometer_pressure_pa', 0), ('links', {}), ('imu', None)]:
            sample = copy.deepcopy(self.trace[0]); sample[key] = value
            with self.subTest(key=key), self.assertRaises(TelemetryError): build_snapshot(sample)

if __name__ == '__main__': unittest.main()
