"""Compute an illustrative three cell power budget from supplied readings."""
import math

class BatteryError(ValueError):
    pass

def _nonnegative(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise BatteryError(f'{name} must be a finite number')
    if value < 0 or (positive and value == 0):
        raise BatteryError(f'{name} is outside the supported range')
    return float(value)

def power_example(voltage_v, current_a, capacity_mah, dt_seconds, samples):
    voltage = _nonnegative(voltage_v, 'Voltage', positive=True)
    current = _nonnegative(current_a, 'Current')
    capacity = _nonnegative(capacity_mah, 'Capacity', positive=True)
    dt = _nonnegative(dt_seconds, 'Timestep', positive=True)
    if isinstance(samples, bool) or not isinstance(samples, int) or not 1 <= samples <= 5000:
        raise BatteryError('Samples must be between 1 and 5000')
    power = voltage * current
    charge_step = current * dt * 1000.0 / 3600.0
    energy_step = power * dt / 3600.0
    if not all(math.isfinite(x) for x in (power, charge_step, energy_step)):
        raise BatteryError('Power calculation is not finite')
    trace = []
    for step in range(samples):
        used = charge_step * step
        energy = energy_step * step
        if not all(math.isfinite(x) for x in (used, energy)):
            raise BatteryError('Accumulated power calculation is not finite')
        trace.append({'step': step, 'voltage_v': voltage, 'current_a': current, 'power_w': power,
                      'charge_used_mah': used, 'energy_used_wh': energy,
                      'remaining_capacity_mah': max(0.0, capacity - used), 'capacity_exhausted': used >= capacity})
    return {'cells_in_series': 3, 'capacity_mah': capacity, 'assumed_initial_charge_mah': capacity,
            'voltage_v': voltage, 'current_a': current, 'dt_seconds': dt,
            'nominal_voltage_v': 3 * 3.7, 'full_charge_voltage_v': 3 * 4.2,
            'nominal_energy_wh': capacity / 1000.0 * (3 * 3.7),
            'trace': trace,
            'limitations': ['Fixed example voltage and current, not measurements',
                            'Current is not linked to simulated thrust or motor behaviour',
                            'No cell imbalance, voltage sag, temperature or discharge curve',
                            'Remaining capacity starts from the assumed capacity and uses ideal counting',
                            'No low voltage protection or physical flight safety is represented']}
