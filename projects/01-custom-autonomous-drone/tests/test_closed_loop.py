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
from drone_archive.closed_loop import simulate_closed_loop
from drone_archive.simulation import SimulationError

class ClosedLoopTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'fixtures' / 'closed-loop-scenario.json').read_text(encoding='utf-8'))

    def test_repeatable_healthy_tracking_and_seeded_campaign(self):
        config = copy.deepcopy(self.config)
        self.assertEqual(simulate_closed_loop(config), simulate_closed_loop(config))
        self.assertEqual(config, self.config)
        for seed in range(10):
            scenario = dict(config, seed=seed)
            trace = simulate_closed_loop(scenario)['trace']
            self.assertTrue(all(row['control']['state'] == 'tracking' for row in trace))
            self.assertTrue(all(0 <= row['control']['thrust_n'] <= scenario['max_thrust_n'] for row in trace))
            error = math.sqrt(sum((row['truth']['altitude_m'] - scenario['target_altitude_m']) ** 2 for row in trace[-100:]) / 100)
            self.assertLess(error, 0.2, f'seed {seed}')

    def test_controller_uses_estimated_state(self):
        row = simulate_closed_loop(self.config)['trace'][0]
        error = self.config['target_altitude_m'] - row['estimate']['altitude_m']
        expected = self.config['mass_kg'] * self.config['gravity_m_s2'] + self.config['kp_n_per_m'] * error + self.config['ki_n_per_m_second'] * error * self.config['dt_seconds'] - self.config['kd_n_per_m_s'] * row['estimate']['velocity_m_s']
        self.assertAlmostEqual(row['control']['thrust_n'], expected)
        self.assertNotEqual(row['estimate']['altitude_m'], row['truth']['altitude_m'])

    def test_recorded_controller_terms_match_the_command(self):
        trace = simulate_closed_loop(self.config)['trace']
        for row in trace:
            control = row['control']; estimate = row['estimate']
            if control['state'] != 'tracking':
                continue
            error = self.config['target_altitude_m'] - estimate['altitude_m']
            proposed = control['integral_before_m_s'] + error * self.config['dt_seconds']
            raw = (self.config['mass_kg'] * self.config['gravity_m_s2'] + self.config['kp_n_per_m'] * error
                   + self.config['ki_n_per_m_second'] * proposed - self.config['kd_n_per_m_s'] * estimate['velocity_m_s'])
            self.assertAlmostEqual(control['error_m'], error)
            self.assertAlmostEqual(control['proposed_integral_m_s'], proposed)
            self.assertAlmostEqual(control['unclamped_thrust_n'], raw)
            self.assertAlmostEqual(control['thrust_n'], max(0, min(self.config['max_thrust_n'], raw)))
            update = row['updates']['pressure']
            if update is not None:
                self.assertAlmostEqual(update['normalised_innovation_squared'], update['innovation'] ** 2 / update['innovation_variance'])

    def test_missing_observations_enter_degraded_then_recover(self):
        fault = {'start': 10, 'end': 20}
        trace = simulate_closed_loop(dict(self.config, pressure_dropout=fault, gps_dropout=fault))['trace']
        self.assertEqual(trace[14]['control']['state'], 'tracking')
        self.assertEqual(trace[15]['control']['state'], 'degraded')
        self.assertTrue(all(row['control']['thrust_n'] == 0 for row in trace[15:20]))
        self.assertEqual(trace[20]['control']['state'], 'tracking')
        self.assertEqual(trace[20]['estimate']['unobserved_steps'], 0)

    def test_no_tracking_before_first_observation(self):
        outage = {'start': 0, 'end': 10}
        trace = simulate_closed_loop(dict(self.config, initial_altitude_m=3, pressure_dropout=outage, gps_dropout=outage))['trace']
        self.assertTrue(all(row['control']['state'] == 'degraded' for row in trace[:10]))
        self.assertTrue(all(row['control']['thrust_n'] == 0 for row in trace[:10]))
        self.assertTrue(trace[10]['updates']['pressure']['accepted'])
        self.assertEqual(trace[10]['control']['state'], 'tracking')

    def test_missing_imu_is_explicit_and_holds_integral(self):
        trace = simulate_closed_loop(dict(self.config, imu_dropout={'start': 10, 'end': 13}))['trace']
        self.assertTrue(all(row['control']['state'] == 'degraded' and row['sensors']['imu_acceleration_m_s2'] is None for row in trace[10:13]))
        self.assertTrue(all(row['control']['integral_error_m_s'] == trace[9]['control']['integral_error_m_s'] for row in trace[10:13]))
        self.assertEqual(trace[13]['control']['state'], 'tracking')

    def test_biased_pressure_is_rejected(self):
        trace = simulate_closed_loop(dict(self.config, pressure_bias={'start': 30, 'end': 40, 'amount': 1000}))['trace']
        self.assertTrue(all(not row['updates']['pressure']['accepted'] for row in trace[30:40]))
        self.assertIsNotNone(trace[30]['updates']['gps'])
        self.assertTrue(trace[30]['updates']['gps']['accepted'])

    def test_ground_contact_stops_the_explicit_euler_model(self):
        outage = {'start': 0, 'end': 10}
        config = dict(self.config, steps=10, dt_seconds=0.5, initial_altitude_m=1,
                      initial_velocity_m_s=0, gravity_m_s2=2, drag_n_per_m_s=0,
                      pressure_dropout=outage, gps_dropout=outage)
        report = simulate_closed_loop(config)
        self.assertEqual([row['truth']['altitude_m'] for row in report['trace']], [1, 1, 0.5])
        self.assertEqual(report['final']['altitude_m'], 0)
        self.assertAlmostEqual(report['terminal_event']['time_s'], 1.25)
        self.assertAlmostEqual(report['terminal_event']['velocity_m_s'], -2.5)
        self.assertEqual(report['terminal_event']['after_step'], 2)

    def test_airborne_run_has_no_terminal_event(self):
        report = simulate_closed_loop(self.config)
        self.assertIsNone(report['terminal_event'])
        self.assertEqual(len(report['trace']), self.config['steps'])

    def test_invalid_configuration_fails(self):
        for key, value in [('mass_kg', 0), ('steps', True), ('gps_interval_steps', 0), ('pressure_noise_std_pa', 0), ('max_unobserved_steps', -1), ('imu_dropout', {'start':5,'end':4})]:
            with self.subTest(key=key), self.assertRaises(SimulationError): simulate_closed_loop(dict(self.config, **{key:value}))

    def test_command_writes_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src'); output = Path(tmp) / 'closed.json'
            command = [sys.executable, '-m', 'drone_archive', 'closed', str(ROOT / 'fixtures' / 'closed-loop-scenario.json'), '--output', str(output)]
            result = subprocess.run(command, cwd=tmp, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(report['trace']), 300)
            self.assertIn('No original aircraft behaviour or physical flight safety is verified', report['limitations'])

if __name__ == '__main__': unittest.main()
