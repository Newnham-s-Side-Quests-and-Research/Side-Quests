import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.battery import BatteryError, power_example

class BatteryTests(unittest.TestCase):
    def test_three_cell_reference_and_known_power(self):
        report = power_example(11.1, 8.0, 1500, 0.05, 300)
        self.assertEqual(report['cells_in_series'], 3)
        self.assertAlmostEqual(report['nominal_voltage_v'], 11.1)
        self.assertAlmostEqual(report['full_charge_voltage_v'], 12.6)
        self.assertAlmostEqual(report['nominal_energy_wh'], 16.65)
        self.assertAlmostEqual(report['trace'][0]['power_w'], 88.8)
        self.assertAlmostEqual(report['trace'][0]['charge_used_mah'], 0)
        self.assertAlmostEqual(report['trace'][200]['charge_used_mah'], 8 * 10 * 1000 / 3600)
        self.assertAlmostEqual(report['trace'][200]['energy_used_wh'], 11.1 * 8 * 10 / 3600)
        self.assertAlmostEqual(report['trace'][200]['remaining_capacity_mah'], 1500 - 8 * 10 * 1000 / 3600)
        self.assertIn('Current is not linked to simulated thrust or motor behaviour', report['limitations'])

    def test_zero_draw_and_exhausted_capacity(self):
        zero = power_example(11.1, 0, 1000, 1, 3)
        self.assertEqual(zero['trace'][-1]['charge_used_mah'], 0)
        exhausted = power_example(11.1, 3600, 1000, 1, 3)
        self.assertTrue(exhausted['trace'][1]['capacity_exhausted'])
        self.assertEqual(exhausted['trace'][2]['remaining_capacity_mah'], 0)
        self.assertGreater(exhausted['trace'][2]['charge_used_mah'], 1000)

    def test_invalid_measurements_are_rejected(self):
        cases=[(0,8,1500,0.05,3),(11.1,-1,1500,0.05,3),(11.1,8,0,0.05,3),
               (11.1,8,1500,0,3),(float('nan'),8,1500,0.05,3),(11.1,True,1500,0.05,3),
               (11.1,8,1500,0.05,0),(11.1,8,1500,0.05,5001),(1e308,1e308,1500,0.05,3)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(BatteryError): power_example(*args)

if __name__=='__main__': unittest.main()
