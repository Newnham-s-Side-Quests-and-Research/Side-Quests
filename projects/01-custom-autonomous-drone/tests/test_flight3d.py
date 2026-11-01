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
from drone_archive.flight3d import run_controlled_flight
from drone_archive.simulation import SimulationError


class ControlledFlightTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'fixtures' / 'controlled-flight-scenario.json').read_text(encoding='utf-8'))

    def test_seeded_runs_reach_target_without_impact(self):
        original = copy.deepcopy(self.config)
        reference = run_controlled_flight(self.config)
        self.assertEqual(reference, run_controlled_flight(self.config))
        self.assertEqual(original, self.config)
        for seed in range(5):
            config = copy.deepcopy(self.config)
            config['controller']['seed'] = seed
            report = run_controlled_flight(config)
            self.assertIsNone(report['terminal_event'])
            self.assertLess(math.dist(report['final']['position_m'], config['controller']['target_position_m']), 0.08)
            self.assertTrue(all(0 <= value <= 5 for row in report['trace'] for value in row['motor_command_n']))
            self.assertTrue(all(row['controller']['pressure_update_accepted'] for row in report['trace']))
        self.assertIn('Horizontal position, velocity and full attitude are ideal model state', reference['limitations'])

    def test_motor_loss_is_recorded_and_ground_contact_stops_run(self):
        config = copy.deepcopy(self.config)
        config['plant']['motor_outage'] = {'motor': 0, 'start': 400, 'end': 1200}
        report = run_controlled_flight(config)
        self.assertEqual(report['terminal_event']['type'], 'ground_contact')
        self.assertEqual(report['trace'][400]['motor_command_n'][0], 0)
        self.assertGreater(report['trace'][400]['controller']['unclamped_motor_commands_n'][0], 0)
        self.assertTrue(any(row['controller']['allocation_saturated'] for row in report['trace'][400:]))
        self.assertEqual(report['final']['position_m'][2], 0)

    def test_singular_motor_allocation_is_rejected(self):
        config = copy.deepcopy(self.config)
        config['plant']['yaw_moment_per_thrust_m'] = 0
        with self.assertRaises(SimulationError):
            run_controlled_flight(config)

    def test_invalid_controller_inputs_are_rejected(self):
        for key, value in [('max_tilt_rad', 0.5), ('pressure_noise_std_pa', 0), ('seed', True),
                           ('target_position_m', [0, 0, 0]), ('position_gain', [-1, 0, 0])]:
            config = copy.deepcopy(self.config)
            config['controller'][key] = value
            with self.subTest(key=key), self.assertRaises(SimulationError):
                run_controlled_flight(config)

    def test_command_exports_the_full_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(ROOT / 'src')
            output = Path(tmp) / 'flight.json'
            result = subprocess.run([sys.executable, '-m', 'drone_archive', 'controlled-flight',
                                     str(ROOT / 'fixtures' / 'controlled-flight-scenario.json'), '--output', str(output)],
                                    cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(report['trace']), 1200)
            self.assertIn('estimated_altitude_m', report['trace'][-1]['controller'])


if __name__ == '__main__':
    unittest.main()
