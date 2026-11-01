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
from drone_archive.estimation import EstimationError, VerticalFilter
from drone_archive.replay import estimate_scenario
from drone_archive.sensors import pressure_from_altitude, SCALE_HEIGHT_M

class EstimatorTests(unittest.TestCase):
    def test_predict_matches_hand_calculation(self):
        estimator = VerticalFilter(0, 2, 4, 9)
        estimator.predict(2, 1, 0)
        self.assertAlmostEqual(estimator.altitude_m, 3)
        self.assertAlmostEqual(estimator.velocity_m_s, 4)
        self.assertEqual(estimator.covariance, ((13.0, 9.0), (9.0, 9.0)))

    def test_linear_measurement_matches_hand_calculation(self):
        estimator = VerticalFilter(0, 0, 4, 1)
        result = estimator.update_altitude(10, 1)
        self.assertTrue(result['accepted'])
        self.assertAlmostEqual(estimator.altitude_m, 8)
        self.assertAlmostEqual(estimator.covariance[0][0], 0.8)
        self.assertAlmostEqual(result['normalised_innovation_squared'], 20)

    def test_pressure_jacobian_and_update_direction(self):
        height = 100.0; delta = 0.01
        numeric = (pressure_from_altitude(height + delta) - pressure_from_altitude(height - delta)) / (2 * delta)
        analytic = -pressure_from_altitude(height) / SCALE_HEIGHT_M
        self.assertAlmostEqual(numeric, analytic, places=6)
        estimator = VerticalFilter(0, 0, 100, 1)
        self.assertTrue(estimator.update_pressure(pressure_from_altitude(5), 25)['accepted'])
        self.assertGreater(estimator.altitude_m, 0)
        self.assertLess(estimator.covariance[0][0], 100)

    def test_outlier_is_rejected_without_state_change(self):
        estimator = VerticalFilter(0, 0, 1, 1)
        before = (estimator.altitude_m, estimator.velocity_m_s, estimator.covariance)
        result = estimator.update_altitude(100, 1, innovation_limit=9)
        self.assertFalse(result['accepted'])
        self.assertEqual((estimator.altitude_m, estimator.velocity_m_s, estimator.covariance), before)

    def test_invalid_inputs_do_not_modify_state(self):
        estimator = VerticalFilter(0, 0, 1, 1)
        before = (estimator.altitude_m, estimator.velocity_m_s, estimator.covariance)
        for operation in (lambda: estimator.predict(0, 0, 1), lambda: estimator.predict(float('nan'), 1, 1),
                          lambda: estimator.update_pressure(0, 1), lambda: estimator.update_altitude(1, 0)):
            with self.assertRaises(EstimationError): operation()
            self.assertEqual((estimator.altitude_m, estimator.velocity_m_s, estimator.covariance), before)

    def test_invalid_small_covariance_is_rejected(self):
        estimator = VerticalFilter(0, 0, 1, 1)
        before = estimator.covariance
        with self.assertRaises(EstimationError): estimator._commit(0, 0, 1e-20, 1e-7, 1e-20)
        self.assertEqual(estimator.covariance, before)

    def test_repeated_updates_preserve_covariance(self):
        estimator = VerticalFilter(2, 0, 10, 4)
        for i in range(200):
            estimator.predict(0.01, 0.1, 0.1)
            estimator.update_altitude(2 + 0.001 * i, 0.25)
            p = estimator.covariance
            self.assertEqual(p[0][1], p[1][0])
            self.assertGreaterEqual(p[0][0] * p[1][1] - p[0][1] ** 2, -1e-12)
            self.assertTrue(all(math.isfinite(x) for row in p for x in row))

    def test_synthetic_replay_is_repeatable_and_records_gps_gaps(self):
        config = json.loads((ROOT / 'fixtures' / 'signal-scenario.json').read_text(encoding='utf-8'))
        result = estimate_scenario(config)
        self.assertEqual(result, estimate_scenario(config))
        self.assertEqual(len(result['trace']), 50)
        self.assertEqual([x['step'] for x in result['trace'] if x['gps_update'] is not None], [0,5,10,15,30,35,40,45])
        error = math.sqrt(sum((row['estimated_altitude_m'] - row['reference_altitude_m']) ** 2 for row in result['trace']) / len(result['trace']))
        self.assertLess(error, 0.25)
        self.assertIn('This result is not evidence of flight readiness', result['limitations'])

    def test_cli_estimation_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            out = Path(tmp) / 'estimate.json'
            run = subprocess.run([sys.executable, '-m', 'drone_archive', 'estimate', str(ROOT / 'fixtures' / 'signal-scenario.json'), '--output', str(out)], cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(len(json.loads(out.read_text(encoding='utf-8'))['trace']), 50)

if __name__ == '__main__': unittest.main()
