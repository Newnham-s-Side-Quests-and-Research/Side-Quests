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
from drone_archive.rigid_body import simulate_rigid_body
from drone_archive.simulation import SimulationError


class RigidBodyTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'fixtures' / 'rigid-body-scenario.json').read_text(encoding='utf-8'))

    def test_balanced_hover_and_input_immutability(self):
        before = copy.deepcopy(self.config)
        report = simulate_rigid_body(self.config)
        self.assertEqual(before, self.config)
        self.assertEqual(report, simulate_rigid_body(self.config))
        self.assertIsNone(report['terminal_event'])
        for row in report['trace']:
            self.assertEqual(row['position_m'], [0, 0, 2])
            self.assertEqual(row['moment_body_nm'], [0, 0, 0])
            self.assertEqual(row['quaternion_wxyz'], [1, 0, 0, 0])

    def test_rotated_body_thrust_changes_world_acceleration(self):
        root = math.sqrt(0.5)
        report = simulate_rigid_body(dict(self.config, steps=1, initial_quaternion_wxyz=[root, 0, root, 0]))
        row = report['trace'][0]
        self.assertAlmostEqual(row['acceleration_m_s2'][0], 9.81)
        self.assertAlmostEqual(row['acceleration_m_s2'][1], 0)
        self.assertAlmostEqual(row['acceleration_m_s2'][2], -9.81)

    def test_motor_lag_and_rotor_moment_have_expected_sign_and_magnitude(self):
        config = dict(self.config, steps=4, motor_outage={'motor': 0, 'start': 0, 'end': 4})
        rows = simulate_rigid_body(config)['trace']
        old_thrust = self.config['initial_thrust_n'][0]
        expected = old_thrust * math.exp(-self.config['dt_seconds'] / self.config['motor_time_constant_s'])
        self.assertAlmostEqual(rows[1]['motor_thrust_n'][0], expected)
        loss = old_thrust - expected
        self.assertAlmostEqual(rows[1]['moment_body_nm'][0], -0.075 * loss)
        self.assertAlmostEqual(rows[1]['moment_body_nm'][1], 0.075 * loss)
        self.assertAlmostEqual(rows[1]['moment_body_nm'][2], -0.01 * loss)
        self.assertLess(rows[2]['body_rate_rad_s'][0], 0)
        self.assertGreater(rows[2]['body_rate_rad_s'][1], 0)

    def test_torque_free_rotation_preserves_quaternion_norm(self):
        config = dict(self.config, steps=100, initial_body_rate_rad_s=[0, 0, 1],
                      initial_position_m=[0, 0, 100])
        rows = simulate_rigid_body(config)['trace']
        for row in rows:
            self.assertAlmostEqual(math.hypot(*row['quaternion_wxyz']), 1)
            self.assertAlmostEqual(row['body_rate_rad_s'][2], 1)
        angle = 2 * math.atan2(rows[-1]['quaternion_wxyz'][3], rows[-1]['quaternion_wxyz'][0])
        self.assertAlmostEqual(angle, 0.99, places=4)

    def test_free_fall_and_ground_contact(self):
        config = dict(self.config, steps=10, dt_seconds=0.5, mass_kg=1, gravity_m_s2=2,
                      drag_n_per_m_s=0, initial_position_m=[0, 0, 1],
                      initial_thrust_n=[0, 0, 0, 0], command_thrust_n=[0, 0, 0, 0])
        report = simulate_rigid_body(config)
        self.assertEqual([row['position_m'][2] for row in report['trace']], [1, 1, 0.5])
        self.assertAlmostEqual(report['terminal_event']['time_s'], 1.25)
        self.assertAlmostEqual(report['final']['velocity_m_s'][2], -2.5)
        self.assertEqual(report['final']['position_m'][2], 0)

    def test_invalid_inputs_are_rejected(self):
        cases = [('mass_kg', 0), ('inertia_kg_m2', [1, 1, 3]), ('initial_quaternion_wxyz', [0, 0, 0, 0]),
                 ('rotor_spin_signs', [1, -1, 1, True]), ('motor_time_constant_s', 0),
                 ('motor_outage', {'motor': 4, 'start': 0, 'end': 1})]
        for key, value in cases:
            with self.subTest(key=key), self.assertRaises(SimulationError):
                simulate_rigid_body(dict(self.config, **{key: value}))

    def test_command_writes_labelled_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(ROOT / 'src')
            output = Path(tmp) / 'report.json'
            result = subprocess.run([sys.executable, '-m', 'drone_archive', 'rigid-body',
                                     str(ROOT / 'fixtures' / 'rigid-body-scenario.json'), '--output', str(output)],
                                    cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(report['trace']), 400)
            self.assertIn('Not suitable for controlling or validating an aircraft', report['limitations'])


if __name__ == '__main__':
    unittest.main()
