"""Illustrative point mass motion with four independently specified thrust inputs.

The vehicle remains level. This module must not be used to control aircraft.
"""
import math
from .simulation import SimulationError


def _finite(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SimulationError(f'{name} must be a finite number')
    try:
        valid = math.isfinite(value) and (minimum is None or value >= minimum)
    except OverflowError:
        valid = False
    if not valid:
        raise SimulationError(f'{name} must be a finite number in range')
    return float(value)


def _vector(value, name):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise SimulationError(f'{name} must have three coordinates')
    return [_finite(component, name) for component in value]


def simulate_point_mass(config):
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise SimulationError('Point mass configuration must use schema version 1')
    steps = config.get('steps')
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 100000:
        raise SimulationError('steps must be an integer between 1 and 100000')
    dt = _finite(config.get('dt_seconds'), 'dt_seconds', 0)
    mass = _finite(config.get('mass_kg'), 'mass_kg', 0)
    if dt == 0 or mass == 0:
        raise SimulationError('Time step and mass must be positive')
    gravity = _finite(config.get('gravity_m_s2'), 'gravity_m_s2', 0)
    drag = _finite(config.get('drag_n_per_m_s'), 'drag_n_per_m_s', 0)
    wind = _vector(config.get('wind_m_s'), 'wind_m_s')
    position = _vector(config.get('initial_position_m'), 'initial_position_m')
    velocity = _vector(config.get('initial_velocity_m_s'), 'initial_velocity_m_s')
    if position[2] <= 0:
        raise SimulationError('Initial altitude must be above the ground')
    motors = config.get('motor_thrust_n')
    if not isinstance(motors, list) or len(motors) != 4:
        raise SimulationError('Four motor thrust values are required')
    motors = [_finite(value, 'motor_thrust_n', 0) for value in motors]
    fault = config.get('motor_outage')
    if fault is not None:
        if not isinstance(fault, dict):
            raise SimulationError('Motor outage must be an object')
        motor, start, end = fault.get('motor'), fault.get('start'), fault.get('end')
        if any(isinstance(x, bool) or not isinstance(x, int) for x in (motor, start, end)) or not (0 <= motor < 4 and 0 <= start < end <= steps):
            raise SimulationError('Motor outage must specify a valid motor and step interval')
    trace = []
    contact = None
    for step in range(steps):
        actual = motors.copy()
        if fault is not None and start <= step < end:
            actual[motor] = 0.0
        acceleration = [-drag * (velocity[i] - wind[i]) / mass for i in range(3)]
        acceleration[2] += sum(actual) / mass - gravity
        trace.append({'step': step, 'time_s': step * dt, 'position_m': position.copy(),
                      'velocity_m_s': velocity.copy(), 'acceleration_m_s2': acceleration,
                      'motor_thrust_n': actual})
        next_position = [position[i] + velocity[i] * dt for i in range(3)]
        next_velocity = [velocity[i] + acceleration[i] * dt for i in range(3)]
        if not all(math.isfinite(x) for x in next_position + next_velocity):
            raise SimulationError(f'Nonfinite state at step {step}')
        if next_position[2] <= 0:
            fraction = position[2] / (position[2] - next_position[2])
            position = [position[i] + fraction * (next_position[i] - position[i]) for i in range(3)]
            velocity = [velocity[i] + fraction * (next_velocity[i] - velocity[i]) for i in range(3)]
            position[2] = 0.0
            contact = {'type': 'ground_contact', 'time_s': (step + fraction) * dt, 'after_step': step}
            break
        position, velocity = next_position, next_velocity
    return {'model': 'synthetic level point mass', 'configuration': config, 'trace': trace,
            'final': {'position_m': position, 'velocity_m_s': velocity}, 'terminal_event': contact,
            'limitations': ['Level point mass with prescribed thrust only',
                            'No attitude, torque, motor response, sensors or controller',
                            'Motor failure does not model aircraft rotation or actual failure behaviour',
                            'Wind and linear drag are assumed rather than measured',
                            'Ground contact stops the model without impact dynamics',
                            'Not suitable for controlling or validating an aircraft']}
