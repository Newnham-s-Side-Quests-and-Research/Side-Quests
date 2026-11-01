import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.vision import VisionError, detect_regions

class VisionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / 'fixtures' / 'image-scenario.json').read_text(encoding='utf-8'))

    def test_detects_known_region_and_discards_small_noise(self):
        result = detect_regions(self.fixture['pixels'], 200, 3)
        self.assertEqual(result, [{'area_pixels': 4, 'centroid_x': 2.5, 'centroid_y': 1.5,
                                   'bounds': {'left': 2, 'top': 1, 'right': 3, 'bottom': 2}}])
        self.assertEqual(detect_regions(self.fixture['pixels'], 200, 3), result)

    def test_separate_regions_and_threshold_boundary(self):
        self.assertEqual(len(detect_regions([[200,0],[0,200]], 200, 1)), 2)
        self.assertEqual(detect_regions([[199,199]], 200, 1), [])
        self.assertEqual(detect_regions([[200,200]], 200, 3), [])

    def test_bad_images_and_parameters_are_rejected(self):
        cases = [([], 100, 1), ([[1],[1,2]],100,1), ([[True]],100,1), ([[256]],100,1),
                 ([[0]],-1,1), ([[0]],100,0), ([[0]],True,1)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(VisionError): detect_regions(*args)

    def test_cli_reports_only_synthetic_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            output = Path(tmp) / 'vision.json'
            result = subprocess.run([sys.executable, '-m', 'drone_archive', 'vision', str(ROOT / 'fixtures' / 'image-scenario.json'), '--output', str(output)], cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(report['regions']), 1)
            self.assertIn('Not validated on real imagery', report['limitations'])

if __name__ == '__main__': unittest.main()
