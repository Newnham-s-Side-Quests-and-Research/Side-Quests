"""Closed loop vertical simulation using synthetic sensors and state estimation.

This model is not suitable for controlling an aircraft.
"""
import math
import random
from .estimation import EstimationError, VerticalFilter
from .sensors import pressure_from_altitude
from .simulation import SimulationError, _active, _number, _window


def simulate_closed_loop(config):
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise SimulationError('Closed loop configuration must use schema version 1')
    steps = config.get('steps')
    seed = config.get('seed')
    interval = config.get('gps_interval_steps')
    max_stale = config.get('max_unobserved_steps')
    for value, name, minimum, maximum in ((steps, 'steps', 1, 100000), (interval, 'gps_interval_steps', 1, 100000),
                                          (max_stale, 'max_unobserved_steps', 0, 100000)):
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            raise SimulationError(f'{name} must be an integer in the supported range')
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise SimulationError('seed must be an integer')
    dt = _number(config, 'dt_seconds', strictly_positive=True)
    mass = _number(config, 'mass_kg', strictly_positive=True)
    gravity = _number(config, 'gravity_m_s2', minimum=0)
    drag = _number(config, 'drag_n_per_m_s', minimum=0)
    max_thrust = _number(config, 'max_thrust_n', minimum=0)
    kp = _number(config, 'kp_n_per_m', minimum=0)
    ki = _number(config, 'ki_n_per_m_second', minimum=0)
    kd = _number(config, 'kd_n_per_m_s', minimum=0)
    pressure_noise = _number(config, 'pressure_noise_std_pa', strictly_positive=True)
    gps_noise = _number(config, 'gps_noise_std_m', strictly_positive=True)
    imu_noise = _number(config, 'imu_noise_std_m_s2', minimum=0)
    process_variance = _number(config, 'acceleration_variance_m2_s4', strictly_positive=True)
    gate = _number(config, 'innovation_limit', strictly_positive=True)
    altitude = _number(config, 'initial_altitude_m')
    velocity = _number(config, 'initial_velocity_m_s')
    target = _number(config, 'target_altitude_m')
    estimator = VerticalFilter(_number(config, 'estimate_altitude_m'), _number(config, 'estimate_velocity_m_s'),
                               _number(config, 'estimate_altitude_variance_m2', strictly_positive=True),
                               _number(config, 'estimate_velocity_variance_m2_s2', strictly_positive=True))
    pressure_outage = _window(config.get('pressure_dropout'), 'pressure_dropout', steps)
    gps_outage = _window(config.get('gps_dropout'), 'gps_dropout', steps)
    imu_outage = _window(config.get('imu_dropout'), 'imu_dropout', steps)
    pressure_bias = _window(config.get('pressure_bias'), 'pressure_bias', steps, bias=True)
    gps_bias = _window(config.get('gps_bias'), 'gps_bias', steps, bias=True)
    prng, grng, irng = random.Random(f'{seed}:pressure'), random.Random(f'{seed}:gps'), random.Random(f'{seed}:imu')
    stale = 0
    has_observation = False
    integral = 0.0
    trace = []
    for step in range(steps):
        p_noise, g_noise, i_noise = prng.gauss(0, pressure_noise), grng.gauss(0, gps_noise), irng.gauss(0, imu_noise)
        try:
            pressure = pressure_from_altitude(altitude) + p_noise + (pressure_bias[2] if _active(pressure_bias, step) else 0.0)
        except ValueError as exc:
            raise SimulationError(f'Pressure model failed at step {step}: {exc}') from exc
        pressure = None if _active(pressure_outage, step) or pressure <= 0 else pressure
        gps = None if step % interval != 0 or _active(gps_outage, step) else altitude + g_noise + (gps_bias[2] if _active(gps_bias, step) else 0.0)
        try:
            pressure_update = estimator.update_pressure(pressure, pressure_noise ** 2, gate) if pressure is not None else None
            gps_update = estimator.update_altitude(gps, gps_noise ** 2, gate) if gps is not None else None
            accepted = any(update is not None and update['accepted'] for update in (pressure_update, gps_update))
            stale = 0 if accepted else stale + 1
            has_observation = has_observation or accepted
            imu_missing = _active(imu_outage, step)
            state = 'tracking' if has_observation and stale <= max_stale and not imu_missing else 'degraded'
            integral_before = integral
            error = proposed = desired = None
            if state == 'tracking':
                error = target - estimator.altitude_m
                proposed = integral + error * dt
                desired = mass * gravity + kp * error + ki * proposed - kd * estimator.velocity_m_s
                if not all(math.isfinite(x) for x in (proposed, desired)):
                    raise SimulationError(f'Nonfinite controller state at step {step}')
                if not ((desired > max_thrust and error > 0) or (desired < 0 and error < 0)):
                    integral = proposed
                thrust = max(0.0, min(max_thrust, desired))
            else:
                thrust = 0.0
            acceleration = (thrust - mass * gravity - drag * velocity) / mass
            imu_acceleration = None if imu_missing else acceleration + i_noise
            trace.append({'step': step, 'time_s': step * dt,
                          'truth': {'altitude_m': altitude, 'velocity_m_s': velocity},
                          'sensors': {'pressure_pa': pressure, 'gps_altitude_m': gps, 'imu_acceleration_m_s2': imu_acceleration},
                          'estimate': {'altitude_m': estimator.altitude_m, 'velocity_m_s': estimator.velocity_m_s,
                                       'covariance': estimator.covariance, 'unobserved_steps': stale},
                          'updates': {'pressure': pressure_update, 'gps': gps_update},
                          'control': {'state': state, 'thrust_n': thrust, 'integral_error_m_s': integral,
                                      'error_m': error, 'integral_before_m_s': integral_before,
                                      'proposed_integral_m_s': proposed, 'unclamped_thrust_n': desired}})
            if imu_acceleration is None:
                # Zero mean acceleration is an explicit degraded model assumption.
                estimator.predict(0.0, dt, process_variance * 100.0)
            else:
                estimator.predict(imu_acceleration, dt, process_variance)
            altitude, velocity = altitude + velocity * dt, velocity + acceleration * dt
            if not all(math.isfinite(x) for x in (altitude, velocity)):
                raise SimulationError(f'Nonfinite simulated state at step {step}')
        except (ValueError, EstimationError) as exc:
            raise SimulationError(f'Invalid signal or estimate at step {step}: {exc}') from exc
    return {'model': 'synthetic closed loop vertical simulation', 'configuration': config, 'trace': trace,
            'final': {'altitude_m': altitude, 'velocity_m_s': velocity},
            'limitations': ['One dimensional synthetic model only', 'No attitude, motors, camera or real GPS coordinates',
                            'Zero thrust during stale observations is only a simulation convention',
                            'No original aircraft behaviour or physical flight safety is verified']}
