from test_inputs import input_path
import copy
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.metrics import MetricsError, summarise
from drone_archive.scenarios import build_scenarios
from drone_archive.simulation import SimulationError

class MetricTests(unittest.TestCase):
    def test_summary_matches_hand_calculated_values(self):
        rows = []
        for i, (truth, estimate) in enumerate(((1,1.5), (2,2), (3,2.5))):
            rows.append({'step': i, 'time_s': i * 0.5, 'truth': {'altitude_m':truth},
                         'estimate': {'altitude_m':estimate},
                         'control': {'state':'degraded' if i==1 else 'tracking', 'thrust_n':i+1},
                         'sensors': {'pressure_pa':100 if i<2 else None, 'gps_altitude_m':1 if i==0 else None,
                                     'imu_acceleration_m_s2':None if i==1 else 0},
                         'updates': {'pressure': {'accepted':i==0} if i<2 else None,
                                     'gps': {'accepted':True} if i==0 else None}})
        report={'trace':rows,'configuration':{'target_altitude_m':2,'gps_interval_steps':2},'final':{'altitude_m':4}}
        result=summarise(report)
        self.assertAlmostEqual(result['tracking_rmse_m'], math.sqrt(2/3))
        self.assertAlmostEqual(result['estimation_rmse_m'], math.sqrt(0.5/3))
        self.assertEqual(result['maximum_absolute_tracking_error_m'], 1)
        self.assertEqual(result['degraded_steps'], 1)
        self.assertEqual((result['pressure_accepted'],result['pressure_rejected'],result['pressure_missing']),(1,1,1))
        self.assertEqual((result['gps_scheduled'],result['gps_accepted'],result['gps_rejected'],result['gps_missing_on_schedule']),(2,1,0,1))
        self.assertEqual(result['imu_missing'],1)
        self.assertEqual(result['final_altitude_m'],4)

    def test_empty_trace_fails(self):
        with self.assertRaises(MetricsError): summarise({'trace': []})

class ScenarioTests(unittest.TestCase):
    def test_scenarios_are_reproducible_and_preserve_input(self):
        config=json.loads((input_path('closed-loop-scenario.json')).read_text(encoding='utf-8'))
        original=copy.deepcopy(config)
        scenarios=build_scenarios(config)
        self.assertEqual(config,original)
        self.assertEqual(scenarios,build_scenarios(config))
        self.assertEqual([item['id'] for item in scenarios],['baseline','gps_outage','pressure_outage','position_outage','imu_outage','pressure_bias'])
        self.assertEqual(scenarios[0]['metrics']['degraded_steps'],0)
        self.assertEqual(scenarios[1]['metrics']['gps_missing_on_schedule'],6)
        self.assertEqual(scenarios[1]['metrics']['degraded_steps'],0)
        self.assertEqual(scenarios[2]['metrics']['pressure_missing'],30)
        self.assertEqual(scenarios[2]['metrics']['degraded_steps'],0)
        for scenario in scenarios[3:5]:
            self.assertEqual(scenario['report']['terminal_event']['type'], 'ground_contact')
            self.assertGreater(scenario['metrics']['degraded_steps'], 0)
            self.assertLess(scenario['metrics']['sample_count'], config['steps'])
            self.assertTrue(all(row['truth']['altitude_m'] > 0 for row in scenario['report']['trace']))
        self.assertEqual(scenarios[5]['metrics']['pressure_rejected'],30)
        for scenario in scenarios:
            self.assertEqual(scenario['metrics']['sample_count'],len(scenario['report']['trace']))
            self.assertEqual(scenario['battery_example']['cells_in_series'], 3)
            self.assertEqual(len(scenario['battery_example']['trace']), len(scenario['report']['trace']))
            for row, battery in zip(scenario['report']['trace'], scenario['battery_example']['trace']):
                self.assertEqual(row['step'], battery['step'])
                self.assertAlmostEqual(battery['charge_used_mah'], 8 * row['time_s'] * 1000 / 3600)
            self.assertIn('No original aircraft behaviour or physical flight safety is verified',scenario['report']['limitations'])

    def test_dashboard_limits_are_explicit(self):
        for value in (None,19,5001,True):
            with self.subTest(value=value), self.assertRaises(SimulationError): build_scenarios({'steps':value})

if __name__=='__main__': unittest.main()
