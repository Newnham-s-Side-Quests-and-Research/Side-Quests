"""Run a one dimensional toy model with explicit signal faults.

The model is an illustrative fixture. It is not the original drone controller.
"""
import math
import random
from .sensors import ideal_imu, pressure_from_altitude

class SimulationError(ValueError):
    pass

def _number(config, name, minimum=None, strictly_positive=False):
    value = config.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SimulationError(f'{name} must be a finite number')
    if minimum is not None and value < minimum:
        raise SimulationError(f'{name} is below its minimum')
    if strictly_positive and value <= 0:
        raise SimulationError(f'{name} must be positive')
    return float(value)

def _window(value, name, steps, bias=False):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise SimulationError(f'{name} must be an object')
    start, end = value.get('start'), value.get('end')
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (start, end)) or not 0 <= start < end <= steps:
        raise SimulationError(f'{name} must use a valid half open step interval')
    amount = _number(value, 'amount') if bias else None
    return (start, end, amount)

def _active(window, step):
    return window is not None and window[0] <= step < window[1]

def simulate(config):
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise SimulationError('Simulation configuration must use schema version 1')
    steps, seed = config.get('steps'), config.get('seed')
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 100000:
        raise SimulationError('steps must be an integer between 1 and 100000')
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise SimulationError('seed must be an integer')
    dt = _number(config, 'dt_seconds', strictly_positive=True)
    mass = _number(config, 'mass_kg', strictly_positive=True)
    gravity = _number(config, 'gravity_m_s2', minimum=0)
    drag = _number(config, 'drag_n_per_m_s', minimum=0)
    max_thrust = _number(config, 'max_thrust_n', minimum=0)
    kp = _number(config, 'kp_n_per_m', minimum=0)
    kd = _number(config, 'kd_n_per_m_s', minimum=0)
    ki = _number(config, 'ki_n_per_m_second', minimum=0)
    noise = _number(config, 'altitude_noise_std_m', minimum=0)
    altitude = _number(config, 'initial_altitude_m')
    velocity = _number(config, 'initial_velocity_m_s')
    target = _number(config, 'target_altitude_m')
    bias = _window(config.get('altitude_bias'), 'altitude_bias', steps, bias=True)
    dropout = _window(config.get('altitude_dropout'), 'altitude_dropout', steps)
    wifi_dropout = _window(config.get('wifi_dropout'), 'wifi_dropout', steps)
    bluetooth_dropout = _window(config.get('bluetooth_dropout'), 'bluetooth_dropout', steps)
    rng = random.Random(seed)
    trace = []
    integral = 0.0
    for step in range(steps):
        missing = _active(dropout, step)
        noise_sample = rng.gauss(0, noise)
        measured = None if missing else altitude + noise_sample + (bias[2] if _active(bias, step) else 0.0)
        if missing:
            thrust = 0.0
            state = 'missing altitude'
        else:
            error = target - measured
            proposed_integral = integral + error * dt
            desired = mass * gravity + kp * error + ki * proposed_integral - kd * velocity
            if not math.isfinite(desired) or not math.isfinite(proposed_integral):
                raise SimulationError(f'Nonfinite controller state at step {step}')
            if not ((desired > max_thrust and error > 0) or (desired < 0 and error < 0)):
                integral = proposed_integral
            thrust = max(0.0, min(max_thrust, desired))
            state = 'tracking'
        acceleration = (thrust - mass * gravity - drag * velocity) / mass
        next_altitude = altitude + velocity * dt
        next_velocity = velocity + acceleration * dt
        if not all(math.isfinite(x) for x in (measured if measured is not None else 0.0, thrust, next_altitude, next_velocity)):
            raise SimulationError(f'Nonfinite result at step {step}')
        try:
            pressure = pressure_from_altitude(altitude)
            imu = ideal_imu(acceleration, gravity)
        except ValueError as exc:
            raise SimulationError(f'Sensor model failed at step {step}: {exc}') from exc
        trace.append({'step': step, 'time_s': step * dt, 'altitude_m': altitude,
                      'velocity_m_s': velocity, 'altitude_signal_m': measured,
                      'thrust_n': thrust, 'acceleration_m_s2': acceleration, 'state': state,
                      'integral_error_m_s': integral,
                      'barometer_pressure_pa': pressure, 'imu': imu,
                      'links': {'wifi_available': not _active(wifi_dropout, step),
                                'bluetooth_available': not _active(bluetooth_dropout, step)}})
        altitude, velocity = next_altitude, next_velocity
    return {'model': 'illustrative one dimensional model', 'config': config, 'trace': trace,
            'final': {'altitude_m': altitude, 'velocity_m_s': velocity},
            'limitations': ['Not the original aircraft or firmware', 'Velocity is an ideal simulated signal',
                            'Pressure and IMU values use idealised equations rather than a device model',
                            'Link states are synthetic and no wireless network is used',
                            'No ground, attitude, motor dynamics or physical validation',
                            'Zero thrust on missing signal is only a test convention']}
