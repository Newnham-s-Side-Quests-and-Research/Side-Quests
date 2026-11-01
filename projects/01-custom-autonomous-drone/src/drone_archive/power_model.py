"""Illustrative electrical accounting driven by simulated rotor thrust.

Parameters are assumptions. This model is not a battery protection system.
"""
import math
from .point_mass import _finite
from .simulation import SimulationError


class PowerModel:
    def __init__(self, config):
        if not isinstance(config, dict) or config.get('schema_version') != 1:
            raise SimulationError('Power configuration must use schema version 1')
        if config.get('cells_in_series') != 3 or isinstance(config.get('cells_in_series'), bool):
            raise SimulationError('This example requires three cells in series')
        self.capacity = _finite(config.get('capacity_mah'), 'capacity_mah', 0)
        fraction = _finite(config.get('initial_charge_fraction'), 'initial_charge_fraction', 0)
        self.full = _finite(config.get('full_cell_voltage_v'), 'full_cell_voltage_v', 0)
        self.empty = _finite(config.get('empty_cell_voltage_v'), 'empty_cell_voltage_v', 0)
        self.resistance = _finite(config.get('pack_resistance_ohm'), 'pack_resistance_ohm', 0)
        self.idle = _finite(config.get('idle_current_a'), 'idle_current_a', 0)
        self.coefficient = _finite(config.get('current_per_thrust_a_per_n'), 'current_per_thrust_a_per_n', 0)
        if self.capacity <= 0 or fraction > 1 or not 0 < self.empty < self.full:
            raise SimulationError('Invalid capacity, initial charge or voltage assumptions')
        self.remaining = self.capacity * fraction
        self.energy_wh = 0.0

    def advance(self, motor_thrust, seconds):
        if not isinstance(motor_thrust, (tuple, list)) or len(motor_thrust) != 4:
            raise SimulationError('Four motor thrust values are required for power accounting')
        motors = [_finite(value, 'motor thrust', 0) for value in motor_thrust]
        duration = _finite(seconds, 'power duration', 0)
        if duration <= 0:
            raise SimulationError('Power duration must be positive')
        start = self.remaining
        fraction = start / self.capacity
        open_voltage = 3 * (self.empty + (self.full - self.empty) * fraction)
        requested_current = self.idle + self.coefficient * sum(motors)
        if not math.isfinite(requested_current):
            raise SimulationError('Nonfinite current')
        current = requested_current if start > 0 else 0.0
        loaded_voltage = max(0.0, open_voltage - current * self.resistance) if current else (open_voltage if start > 0 else 0.0)
        voltage_collapsed = current > 0 and loaded_voltage <= 0
        if voltage_collapsed:
            current = 0.0
        powered_seconds = min(duration, start * 3.6 / current) if current else (duration if start > 0 and not voltage_collapsed else 0.0)
        used = min(start, current * powered_seconds / 3.6)
        self.remaining = max(0.0, start - used)
        energy = loaded_voltage * current * powered_seconds / 3600.0
        self.energy_wh += energy
        if not all(math.isfinite(value) for value in (loaded_voltage, energy, self.energy_wh)):
            raise SimulationError('Nonfinite electrical accounting')
        return {'start_charge_mah': start, 'end_charge_mah': self.remaining,
                'charge_fraction': fraction, 'open_circuit_voltage_v': open_voltage if start > 0 else 0.0,
                'loaded_voltage_v': loaded_voltage, 'requested_current_a': requested_current, 'current_a': current,
                'powered_seconds': powered_seconds, 'step_seconds': duration,
                'energy_wh': energy, 'total_energy_wh': self.energy_wh,
                'charge_exhausted': self.remaining <= 0, 'voltage_collapsed': voltage_collapsed}
