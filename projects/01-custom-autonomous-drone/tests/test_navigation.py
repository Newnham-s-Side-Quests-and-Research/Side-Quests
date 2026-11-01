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
from drone_archive.navigation import _intersects_box, run_navigation
from drone_archive.simulation import SimulationError


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'fixtures' / 'navigation-scenario.json').read_text(encoding='utf-8'))

    def test_segment_collision_detection_catches_crossing_between_samples(self):
        low, high = [0, 0, 0], [1, 1, 1]
        self.assertTrue(_intersects_box([-1, 0.5, 0.5], [2, 0.5, 0.5], low, high))
        self.assertTrue(_intersects_box([-1, 0, 0], [0, 0, 0], low, high))
        self.assertFalse(_intersects_box([-1, 2, 0.5], [2, 2, 0.5], low, high))
        self.assertFalse(_intersects_box([2, 0.5, 0.5], [2, 0.5, 0.5], low, high))

    def test_planned_route_is_flown_and_events_match_waypoints(self):
        original = copy.deepcopy(self.config)
        report = run_navigation(self.config)
        self.assertEqual(self.config, original)
        self.assertEqual(report['status'], 'complete')
        self.assertEqual(report['route'][0], self.config['grid']['start'])
        self.assertEqual(report['route'][-1], self.config['grid']['goal'])
        self.assertEqual(len(report['waypoint_events']), len(report['route']) - 1)
        self.assertTrue(all(event['cell'] == report['route'][event['waypoint_index']] for event in report['waypoint_events']))
        self.assertLess(math.dist(report['flight']['final']['position_m'], report['waypoints_m'][-1]), 0.18)
        self.assertIsNone(report['flight']['terminal_event'])
        targets = {tuple(row['controller']['target_position_m']) for row in report['flight']['trace']}
        self.assertEqual(targets, {tuple(point) for point in report['waypoints_m'][1:]})

    def test_wind_contact_stops_the_run(self):
        config = copy.deepcopy(self.config)
        config['flight']['plant']['wind_m_s'] = [10, 0, 0]
        report = run_navigation(config)
        self.assertEqual(report['status'], 'obstacle_contact')
        self.assertEqual(report['flight']['terminal_event']['cell'], [1, 0, 0])
        self.assertLess(len(report['flight']['trace']), config['flight']['plant']['steps'])

    def test_geofence_exit_and_no_route_are_explicit(self):
        config = copy.deepcopy(self.config)
        config['flight']['plant']['initial_velocity_m_s'] = [-10, 0, 0]
        self.assertEqual(run_navigation(config)['status'], 'geofence_exit')
        config = copy.deepcopy(self.config)
        config['grid']['blocked'] = [[1, y, z] for y in range(3) for z in range(3)]
        report = run_navigation(config)
        self.assertEqual(report['status'], 'no route')
        self.assertIsNone(report['flight'])

    def test_invalid_start_and_tolerance_are_rejected(self):
        config = copy.deepcopy(self.config)
        config['flight']['plant']['initial_position_m'] = [0, 0, 3]
        with self.assertRaises(SimulationError):
            run_navigation(config)
        config = copy.deepcopy(self.config)
        config['waypoint_tolerance_m'] = 0.5
        with self.assertRaises(SimulationError):
            run_navigation(config)

    def test_command_exports_a_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(ROOT / 'src')
            output = Path(tmp) / 'mission.json'
            result = subprocess.run([sys.executable, '-m', 'drone_archive', 'navigation',
                                     str(ROOT / 'fixtures' / 'navigation-scenario.json'), '--output', str(output)],
                                    cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['status'], 'complete')
            self.assertTrue(report['flight']['trace'])


if __name__ == '__main__':
    unittest.main()
