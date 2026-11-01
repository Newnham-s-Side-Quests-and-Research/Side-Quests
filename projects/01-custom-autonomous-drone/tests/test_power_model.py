import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.power_model import PowerModel
from drone_archive.rigid_body import simulate_rigid_body
from drone_archive.simulation import SimulationError


class PowerModelTests(unittest.TestCase):
    def setUp(self):
        flight = json.loads((ROOT / 'fixtures' / 'controlled-flight-scenario.json').read_text(encoding='utf-8'))
        self.config = flight['plant']['power_model']
        self.plant = flight['plant']

    def test_current_voltage_and_charge_for_known_load(self):
        pack = PowerModel(self.config)
        row = pack.advance([1, 1, 1, 1], 3.6)
        self.assertAlmostEqual(row['current_a'], 8.5)
        self.assertAlmostEqual(row['open_circuit_voltage_v'], 12.6)
        self.assertAlmostEqual(row['loaded_voltage_v'], 12.6 - 8.5 * 0.06)
        self.assertAlmostEqual(row['start_charge_mah'] - row['end_charge_mah'], 8.5)
        self.assertAlmostEqual(row['energy_wh'], row['loaded_voltage_v'] * 8.5 * 3.6 / 3600)

    def test_depletion_is_limited_to_available_charge(self):
        config = dict(self.config, capacity_mah=1, idle_current_a=2, current_per_thrust_a_per_n=0)
        pack = PowerModel(config)
        row = pack.advance([0, 0, 0, 0], 3.6)
        self.assertAlmostEqual(row['powered_seconds'], 1.8)
        self.assertEqual(row['end_charge_mah'], 0)
        self.assertTrue(row['charge_exhausted'])
        self.assertAlmostEqual(row['energy_wh'], 12.48 * 2 * 1.8 / 3600)
        after = pack.advance([0, 0, 0, 0], 3.6)
        self.assertEqual(after['current_a'], 0)
        self.assertEqual(after['loaded_voltage_v'], 0)
        self.assertEqual(after['total_energy_wh'], row['energy_wh'])

    def test_zero_current_and_voltage_sag_are_explicit(self):
        pack = PowerModel(dict(self.config, idle_current_a=0, current_per_thrust_a_per_n=0))
        row = pack.advance([0, 0, 0, 0], 1)
        self.assertEqual(row['powered_seconds'], 1)
        self.assertEqual(row['start_charge_mah'], row['end_charge_mah'])
        self.assertAlmostEqual(row['loaded_voltage_v'], 12.6)
        pack = PowerModel(dict(self.config, pack_resistance_ohm=100))
        collapsed = pack.advance([1, 1, 1, 1], 1)
        self.assertEqual(collapsed['loaded_voltage_v'], 0)
        self.assertTrue(collapsed['voltage_collapsed'])
        self.assertEqual(collapsed['current_a'], 0)
        self.assertEqual(collapsed['powered_seconds'], 0)

    def test_invalid_configuration_and_load_are_rejected(self):
        for key, value in [('cells_in_series', 4), ('initial_charge_fraction', 1.1),
                           ('capacity_mah', 0), ('empty_cell_voltage_v', 4.3), ('pack_resistance_ohm', -1)]:
            with self.subTest(key=key), self.assertRaises(SimulationError):
                PowerModel(dict(self.config, **{key: value}))
        with self.assertRaises(SimulationError):
            PowerModel(self.config).advance([1, 1, 1], 1)

    def test_ground_contact_accounts_only_for_elapsed_fraction(self):
        plant = copy.deepcopy(self.plant)
        plant.update(steps=10, dt_seconds=0.5, gravity_m_s2=2, drag_n_per_m_s=0,
                     initial_position_m=[0, 0, 1], initial_thrust_n=[0, 0, 0, 0],
                     command_thrust_n=[0, 0, 0, 0])
        report = simulate_rigid_body(plant)
        self.assertAlmostEqual(report['terminal_event']['time_s'], 1.25)
        self.assertAlmostEqual(sum(row['power']['step_seconds'] for row in report['trace']), 1.25)
        self.assertAlmostEqual(report['trace'][-1]['power']['step_seconds'], 0.25)
        self.assertIn('Electrical accounting is illustrative and does not affect thrust or stop the vehicle', report['limitations'])


if __name__ == '__main__':
    unittest.main()
