import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.mission import run_demonstration

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'fixtures' / 'signal-scenario.json').read_text(encoding='utf-8'))
        self.grid = json.loads((ROOT / 'fixtures' / 'grid-scenario.json').read_text(encoding='utf-8'))
        self.image = json.loads((ROOT / 'fixtures' / 'image-scenario.json').read_text(encoding='utf-8'))

    def test_modules_share_the_same_simulated_samples(self):
        result = run_demonstration(self.config, self.grid, self.image)
        self.assertEqual(result, run_demonstration(self.config, self.grid, self.image))
        self.assertEqual(len(result['simulation_trace']), 50)
        self.assertEqual(len(result['estimation']), 50)
        self.assertEqual(len(result['telemetry']), 50)
        self.assertEqual(result['route'][0], (0,0)); self.assertEqual(result['route'][-1], (4,0))
        self.assertEqual(result['image_regions'][0]['area_pixels'], 4)
        for raw, estimate, snapshot in zip(result['simulation_trace'], result['estimation'], result['telemetry']):
            self.assertEqual(raw['step'], estimate['step'])
            self.assertEqual(raw['altitude_m'], estimate['reference_altitude_m'])
            self.assertEqual(raw['altitude_signal_m'], snapshot['signals']['altitude_m'])
            self.assertEqual(raw['links'], snapshot['links'])
        self.assertIn('Components are not connected in a closed flight control loop', result['limitations'])

    def test_no_route_and_no_detection_remain_visible(self):
        grid = copy.deepcopy(self.grid); grid['blocked'].append([2,4])
        image = copy.deepcopy(self.image); image['minimum_area'] = 100
        result = run_demonstration(self.config, grid, image)
        self.assertIsNone(result['route']); self.assertEqual(result['image_regions'], [])

    def test_command_writes_reproducible_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src'); output = Path(tmp) / 'demo.json'
            args = [sys.executable, '-m', 'drone_archive', 'demo', '--scenario', str(ROOT / 'fixtures' / 'signal-scenario.json'),
                    '--grid', str(ROOT / 'fixtures' / 'grid-scenario.json'), '--image', str(ROOT / 'fixtures' / 'image-scenario.json'), '--output', str(output)]
            result = subprocess.run(args, cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(report['telemetry']), 50)
            self.assertIn('python_version', report)
            self.assertEqual(report['configuration']['seed'], 42)

if __name__ == '__main__': unittest.main()
