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
from drone_archive.point_mass import simulate_point_mass
from drone_archive.simulation import SimulationError

class PointMassTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'fixtures' / 'point-mass-scenario.json').read_text(encoding='utf-8'))

    def test_stationary_hover_without_wind(self):
        config = dict(self.config, wind_m_s=[0, 0, 0])
        original = copy.deepcopy(config)
        report = simulate_point_mass(config)
        self.assertEqual(config, original)
        self.assertIsNone(report['terminal_event'])
        for row in report['trace']:
            self.assertEqual(row['position_m'], [0, 0, 2])
            self.assertEqual(row['velocity_m_s'], [0, 0, 0])

    def test_wind_drag_accelerates_toward_wind_speed(self):
        report = simulate_point_mass(self.config)
        self.assertAlmostEqual(report['trace'][0]['acceleration_m_s2'][0], 0.2)
        self.assertGreater(report['final']['position_m'][0], 0)
        self.assertGreater(report['final']['velocity_m_s'][0], 0)
        self.assertLess(report['final']['velocity_m_s'][0], 1)
        self.assertAlmostEqual(report['final']['position_m'][2], 2)

    def test_free_fall_matches_discrete_equations(self):
        config = dict(self.config, steps=4, dt_seconds=0.5, initial_position_m=[0, 0, 10],
                      gravity_m_s2=2, drag_n_per_m_s=0, motor_thrust_n=[0, 0, 0, 0])
        report = simulate_point_mass(config)
        self.assertEqual([r['position_m'][2] for r in report['trace']], [10, 10, 9.5, 8.5])
        self.assertEqual(report['final']['position_m'][2], 7)
        self.assertEqual(report['final']['velocity_m_s'][2], -4)

    def test_motor_outage_changes_thrust_and_ground_stops_run(self):
        config = dict(self.config, steps=100, wind_m_s=[0, 0, 0], motor_outage={'motor': 2, 'start': 0, 'end': 100})
        report = simulate_point_mass(config)
        self.assertEqual(report['trace'][0]['motor_thrust_n'][2], 0)
        self.assertAlmostEqual(report['trace'][0]['acceleration_m_s2'][2], -9.81 / 4)
        self.assertEqual(report['terminal_event']['type'], 'ground_contact')
        self.assertEqual(report['final']['position_m'][2], 0)
        self.assertTrue(all(row['position_m'][2] > 0 for row in report['trace']))
        self.assertIn('Motor failure does not model aircraft rotation or actual failure behaviour', report['limitations'])

    def test_invalid_inputs_are_rejected(self):
        for key, value in [('mass_kg', 0), ('steps', True), ('wind_m_s', [0, 0, math.inf]),
                           ('motor_thrust_n', [1, 2]), ('initial_position_m', [0, 0, 0]),
                           ('motor_outage', {'motor': 4, 'start': 0, 'end': 1})]:
            with self.subTest(key=key), self.assertRaises(SimulationError):
                simulate_point_mass(dict(self.config, **{key:value}))

    def test_command_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(ROOT / 'src')
            output = Path(tmp) / 'report.json'
            result = subprocess.run([sys.executable, '-m', 'drone_archive', 'point-mass',
                                     str(ROOT / 'fixtures' / 'point-mass-scenario.json'), '--output', str(output)],
                                    env=env, cwd=tmp, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(output.read_text(encoding='utf-8'))['trace']), 100)

if __name__ == '__main__':
    unittest.main()
