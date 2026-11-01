from test_inputs import input_path
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
from drone_archive.evidence import EvidenceError, hash_file, publication_manifest, validate_register, verify_files
from drone_archive.simulation import SimulationError, simulate
from drone_archive.sensors import altitude_from_pressure, ideal_imu, pressure_from_altitude

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.register = {'schema_version': 1, 'artefacts': [
            {'id': 'a', 'sha256': 'a' * 64, 'source': 'synthetic file', 'rights': 'cleared'},
            {'id': 'b', 'sha256': 'b' * 64, 'source': 'synthetic file', 'rights': 'unknown'}],
            'claims': [{'id': 'c', 'text': 'Example', 'status': 'bench', 'evidence': ['a'],
                        'reviewer': 'Test reviewer', 'review_date': '2026-01-01', 'rationale': 'Fixture only'}]}

    def test_hash_changes_when_file_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'sample.txt'; file.write_bytes(b'first')
            original = hash_file(file); self.assertEqual(len(original), 64)
            file.write_bytes(b'second'); self.assertNotEqual(original, hash_file(file))
            with self.assertRaises(EvidenceError): hash_file(Path(tmp) / 'missing')

    def test_verify_detects_changes_missing_files_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'data.bin'; file.write_bytes(b'original')
            self.register['artefacts'][0]['sha256'] = hash_file(file)
            self.register['artefacts'][0]['storage'] = 'data.bin'
            self.register['artefacts'][1]['storage'] = '../outside.bin'
            result = verify_files(self.register, tmp)
            self.assertEqual([x['status'] for x in result], ['matched', 'invalid path'])
            file.write_bytes(b'changed')
            self.assertEqual(verify_files(self.register, tmp)[0]['status'], 'changed')
            file.unlink()
            self.assertEqual(verify_files(self.register, tmp)[0]['status'], 'missing')

    def test_invalid_registers_are_rejected(self):
        for kind in ('duplicate', 'unknown_reference', 'no_evidence', 'bad_hash', 'bad_status', 'bad_date', 'bad_rights'):
            register = copy.deepcopy(self.register)
            if kind == 'duplicate': register['artefacts'].append(copy.deepcopy(register['artefacts'][0]))
            if kind == 'unknown_reference': register['claims'][0]['evidence'] = ['missing']
            if kind == 'no_evidence': register['claims'][0]['evidence'] = []
            if kind == 'bad_hash': register['artefacts'][0]['sha256'] = 'not-a-hash'
            if kind == 'bad_status': register['claims'][0]['status'] = 'proven'
            if kind == 'bad_date': register['claims'][0]['review_date'] = 'unknown'
            if kind == 'bad_rights': register['artefacts'][0]['rights'] = 'approved by default'
            with self.subTest(kind=kind), self.assertRaises(EvidenceError): validate_register(register)

    def test_manifest_only_lists_cleared_and_flags_claims(self):
        self.register['claims'].append({'id': 'd', 'text': 'Unclear', 'status': 'unsupported', 'evidence': [],
                                        'reviewer': 'Test reviewer', 'review_date': '2026-01-01', 'rationale': 'Fixture'})
        self.register['claims'].append({'id': 'e', 'text': 'Needs rights', 'status': 'bench', 'evidence': ['b'],
                                        'reviewer': 'Test reviewer', 'review_date': '2026-01-01', 'rationale': 'Fixture'})
        result = publication_manifest(self.register)
        self.assertEqual(result['cleared_artefacts'], ['a'])
        self.assertEqual([x['claim_id'] for x in result['claim_blockers']], ['d', 'e'])
        self.assertIn('Human approval', result['decision'])

class SignalTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((input_path('signal-scenario.json')).read_text(encoding='utf-8'))

    def test_known_single_step_dynamics(self):
        cfg = dict(self.config, steps=1, initial_altitude_m=1.0, initial_velocity_m_s=2.0,
                   target_altitude_m=1.0, kp_n_per_m=0, kd_n_per_m_s=0, drag_n_per_m_s=0,
                   altitude_noise_std_m=0, altitude_bias=None, altitude_dropout=None, wifi_dropout=None, bluetooth_dropout=None, gps_dropout=None)
        result = simulate(cfg)
        self.assertAlmostEqual(result['trace'][0]['thrust_n'], 9.81)
        self.assertAlmostEqual(result['final']['altitude_m'], 1.2)
        self.assertAlmostEqual(result['final']['velocity_m_s'], 2.0)

    def test_repeatability_faults_and_signal_bounds(self):
        first = simulate(self.config); second = simulate(self.config)
        self.assertEqual(first, second)
        trace = first['trace']
        self.assertEqual([r['step'] for r in trace if r['altitude_signal_m'] is None], [35, 36, 37])
        self.assertTrue(all(r['thrust_n'] == 0 and r['state'] == 'missing altitude' for r in trace[35:38]))
        self.assertTrue(all(0 <= r['thrust_n'] <= self.config['max_thrust_n'] for r in trace))
        self.assertTrue(all(math.isfinite(r['altitude_m']) for r in trace))

    def test_bias_interval_is_half_open(self):
        cfg = dict(self.config, altitude_noise_std_m=0, altitude_dropout=None)
        trace = simulate(cfg)['trace']
        for i in (19, 20, 29, 30):
            difference = trace[i]['altitude_signal_m'] - trace[i]['altitude_m']
            self.assertAlmostEqual(difference, 0.5 if 20 <= i < 30 else 0.0)

    def test_dropout_does_not_shift_later_noise_samples(self):
        without_fault = simulate(dict(self.config, altitude_dropout=None, altitude_bias=None))['trace']
        with_fault = simulate(dict(self.config, altitude_bias=None))['trace']
        for step in (34, 38, 39):
            expected = without_fault[step]['altitude_signal_m'] - without_fault[step]['altitude_m']
            observed = with_fault[step]['altitude_signal_m'] - with_fault[step]['altitude_m']
            self.assertAlmostEqual(expected, observed)

    def test_saturation_and_free_fall_are_explicit(self):
        cfg = dict(self.config, steps=1, altitude_noise_std_m=0, altitude_bias=None,
                   altitude_dropout={'start': 0, 'end': 1}, initial_velocity_m_s=0, wifi_dropout=None, bluetooth_dropout=None, gps_dropout=None)
        result = simulate(cfg)
        self.assertAlmostEqual(result['trace'][0]['acceleration_m_s2'], -9.81)
        self.assertAlmostEqual(result['final']['velocity_m_s'], -0.981)
        cfg = dict(cfg, altitude_dropout=None, target_altitude_m=1000)
        self.assertEqual(simulate(cfg)['trace'][0]['thrust_n'], cfg['max_thrust_n'])

    def test_integral_is_held_during_saturation_and_signal_loss(self):
        cfg = dict(self.config, steps=3, target_altitude_m=1000, altitude_noise_std_m=0,
                   altitude_bias=None, altitude_dropout={'start': 1, 'end': 2},
                   wifi_dropout=None, bluetooth_dropout=None, gps_dropout=None)
        trace = simulate(cfg)['trace']
        self.assertTrue(all(row['integral_error_m_s'] == 0 for row in trace))
        self.assertEqual(trace[0]['thrust_n'], cfg['max_thrust_n'])
        self.assertEqual(trace[1]['state'], 'missing altitude')

    def test_ideal_pressure_and_imu(self):
        self.assertAlmostEqual(pressure_from_altitude(0), 101325)
        self.assertLess(pressure_from_altitude(1000), pressure_from_altitude(0))
        self.assertAlmostEqual(altitude_from_pressure(pressure_from_altitude(1000)), 1000)
        self.assertAlmostEqual(ideal_imu(0, 9.81)['specific_force_z_m_s2'], 9.81)
        self.assertAlmostEqual(ideal_imu(-9.81, 9.81)['specific_force_z_m_s2'], 0)
        with self.assertRaises(ValueError): altitude_from_pressure(0)

    def test_simulated_link_outages_are_independent(self):
        trace = simulate(self.config)['trace']
        self.assertEqual([r['step'] for r in trace if not r['links']['wifi_available']], [10, 11, 12])
        self.assertEqual([r['step'] for r in trace if not r['links']['bluetooth_available']], [25, 26])
        self.assertTrue(all(r['barometer_pressure_pa'] > 0 for r in trace))
        self.assertTrue(all(r['imu']['angular_rate_z_rad_s'] == 0 for r in trace))

    def test_gps_samples_and_outages(self):
        trace = simulate(self.config)['trace']
        observed = [r['step'] for r in trace if r['gps_altitude_m'] is not None]
        self.assertEqual(observed, [0, 5, 10, 15, 30, 35, 40, 45])

    def test_link_outages_do_not_change_the_physics(self):
        baseline = simulate(dict(self.config, wifi_dropout=None, bluetooth_dropout=None))['trace']
        faulty = simulate(self.config)['trace']
        for left, right in zip(baseline, faulty):
            self.assertEqual(left['altitude_m'], right['altitude_m'])
            self.assertEqual(left['thrust_n'], right['thrust_n'])

    def test_seed_changes_the_noisy_signal(self):
        first = simulate(self.config)['trace']
        second = simulate(dict(self.config, seed=self.config['seed'] + 1))['trace']
        self.assertNotEqual(first[0]['altitude_signal_m'], second[0]['altitude_signal_m'])

    def test_bad_configuration_is_rejected(self):
        for name, value in [('mass_kg', 0), ('dt_seconds', -1), ('steps', 0), ('seed', True),
                            ('max_thrust_n', -1), ('gps_interval_steps', 0), ('gps_altitude_noise_std_m', -1), ('ki_n_per_m_second', -1), ('altitude_noise_std_m', float('nan')),
                            ('altitude_dropout', {'start': 5, 'end': 4})]:
            with self.subTest(name=name), self.assertRaises(SimulationError): simulate(dict(self.config, **{name: value}))

    def test_command_runs_from_clean_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            output = Path(tmp) / 'trace.json'
            run = subprocess.run([sys.executable, '-m', 'drone_archive', 'simulate', str(input_path('signal-scenario.json')), '--output', str(output)], cwd=tmp, env=env, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(report['trace']), 50)
            self.assertIn('Not the original aircraft or firmware', report['limitations'])
            bad = subprocess.run([sys.executable, '-m', 'drone_archive', 'validate', str(input_path('empty-register.json'))], cwd=tmp, env=env, text=True, capture_output=True)
            self.assertEqual(bad.returncode, 0, bad.stderr)
            self.assertIn('Human approval', bad.stdout)
            empty = subprocess.run([sys.executable, '-m', 'drone_archive', 'verify', str(input_path('empty-register.json')), '--root', tmp], cwd=tmp, env=env, text=True, capture_output=True)
            self.assertEqual(empty.returncode, 1)


if __name__ == '__main__': unittest.main()
