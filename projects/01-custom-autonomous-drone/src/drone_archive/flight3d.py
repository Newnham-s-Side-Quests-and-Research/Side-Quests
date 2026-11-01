"""Connect a synthetic controller and altitude filter to the rigid body model.

This is an engineering demonstration and cannot control physical aircraft.
"""
import math
import random
from .estimation import VerticalFilter
from .point_mass import _finite, _vector
from .rigid_body import simulate_rigid_body
from .sensors import pressure_from_altitude
from .simulation import SimulationError


def _solve(matrix, values):
    rows = [list(row) + [float(value)] for row, value in zip(matrix, values)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda row: abs(rows[row][col]))
        if abs(rows[pivot][col]) < 1e-12:
            raise SimulationError('Rotor allocation matrix is singular')
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        rows[col] = [item / divisor for item in rows[col]]
        for row in range(4):
            if row != col:
                factor = rows[row][col]
                rows[row] = [rows[row][i] - factor * rows[col][i] for i in range(5)]
    return [row[4] for row in rows]


def _euler(q):
    w, x, y, z = q
    roll = math.atan2(2 * (w*x + y*z), 1 - 2 * (x*x + y*y))
    pitch = math.asin(max(-1, min(1, 2 * (w*y - z*x))))
    yaw = math.atan2(2 * (w*z + x*y), 1 - 2 * (y*y + z*z))
    return roll, pitch, yaw


def run_controlled_flight(config, position_controller=None):
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise SimulationError('Controlled flight configuration must use schema version 1')
    plant = config.get('plant')
    settings = config.get('controller')
    if not isinstance(plant, dict) or not isinstance(settings, dict):
        raise SimulationError('Plant and controller configurations are required')
    target = _vector(settings.get('target_position_m'), 'target_position_m')
    if target[2] <= 0:
        raise SimulationError('Target altitude must be above ground')
    kp = _vector(settings.get('position_gain'), 'position_gain')
    kd = _vector(settings.get('velocity_gain'), 'velocity_gain')
    attitude_kp = _vector(settings.get('attitude_gain'), 'attitude_gain')
    attitude_kd = _vector(settings.get('rate_gain'), 'rate_gain')
    if min(kp + kd + attitude_kp + attitude_kd) < 0:
        raise SimulationError('Controller gains must be nonnegative')
    tilt = _finite(settings.get('max_tilt_rad'), 'max_tilt_rad', 0)
    max_thrust = _finite(settings.get('max_motor_thrust_n'), 'max_motor_thrust_n', 0)
    noise = _finite(settings.get('pressure_noise_std_pa'), 'pressure_noise_std_pa', 0)
    imu_noise = _finite(settings.get('acceleration_noise_std_m_s2'), 'acceleration_noise_std_m_s2', 0)
    if not 0 < tilt < 0.5 or max_thrust <= 0 or noise <= 0:
        raise SimulationError('Tilt, maximum thrust and pressure noise must be positive and within range')
    seed = settings.get('seed')
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise SimulationError('Sensor seed must be an integer')
    positions = plant.get('rotor_positions_m')
    spins = plant.get('rotor_spin_signs')
    if not isinstance(positions, list) or len(positions) != 4 or not isinstance(spins, list) or len(spins) != 4:
        raise SimulationError('Four rotor positions and signs are required')
    positions = [_vector(item, 'rotor position') for item in positions]
    if any(type(sign) is not int or sign not in (-1, 1) for sign in spins):
        raise SimulationError('Rotor signs must be minus one or one')
    yaw_factor = _finite(plant.get('yaw_moment_per_thrust_m'), 'yaw moment per thrust', 0)
    matrix = [[1.0] * 4, [pos[1] for pos in positions], [-pos[0] for pos in positions],
              [yaw_factor * sign for sign in spins]]
    _solve(matrix, [1, 0, 0, 0])
    mass = _finite(plant.get('mass_kg'), 'mass_kg', 0)
    gravity = _finite(plant.get('gravity_m_s2'), 'gravity_m_s2', 0)
    dt = _finite(plant.get('dt_seconds'), 'dt_seconds', 0)
    if min(mass, gravity, dt) <= 0:
        raise SimulationError('Mass, gravity and timestep must be positive')
    initial = _vector(plant.get('initial_position_m'), 'initial_position_m')
    estimator = VerticalFilter(initial[2], 0, 1.0, 1.0)
    pressure_rng = random.Random(f'{seed}:pressure')
    imu_rng = random.Random(f'{seed}:acceleration')

    def control(state):
        previous = state['previous_acceleration_m_s2']
        measured_acceleration = None
        if previous is not None:
            measured_acceleration = previous[2] + imu_rng.gauss(0, imu_noise)
            estimator.predict(measured_acceleration, dt, max(imu_noise * imu_noise, 1e-6))
        pressure = pressure_from_altitude(state['position_m'][2]) + pressure_rng.gauss(0, noise)
        update = estimator.update_pressure(pressure, noise * noise, 25.0)
        estimated_position = [state['position_m'][0], state['position_m'][1], estimator.altitude_m]
        estimated_velocity = [state['velocity_m_s'][0], state['velocity_m_s'][1], estimator.velocity_m_s]
        if position_controller is None:
            acceleration = [kp[i] * (target[i] - estimated_position[i]) - kd[i] * estimated_velocity[i] for i in range(3)]
        else:
            acceleration = position_controller(target, estimated_position, estimated_velocity, kp, kd)
            acceleration = _vector(acceleration, 'position controller acceleration')
        roll, pitch, yaw = _euler(state['quaternion_wxyz'])
        desired_roll = max(-tilt, min(tilt, -acceleration[1] / gravity))
        desired_pitch = max(-tilt, min(tilt, acceleration[0] / gravity))
        cos_tilt = math.cos(roll) * math.cos(pitch)
        collective = mass * max(0, gravity + acceleration[2]) / max(0.2, cos_tilt)
        desired_angles = [desired_roll, desired_pitch, 0.0]
        angles = [roll, pitch, yaw]
        moments = [attitude_kp[i] * math.atan2(math.sin(desired_angles[i] - angles[i]),
                                                math.cos(desired_angles[i] - angles[i]))
                   - attitude_kd[i] * state['body_rate_rad_s'][i] for i in range(3)]
        requested = _solve(matrix, [collective] + moments)
        commands = [max(0, min(max_thrust, value)) for value in requested]
        return commands, {'pressure_pa': pressure, 'pressure_update_accepted': update['accepted'],
                          'vertical_acceleration_m_s2': measured_acceleration,
                          'estimated_altitude_m': estimator.altitude_m, 'estimated_vertical_velocity_m_s': estimator.velocity_m_s,
                          'estimated_altitude_variance_m2': estimator.covariance[0][0],
                          'target_position_m': target.copy(), 'desired_attitude_rad': desired_angles,
                          'attitude_rad': list(angles), 'requested_collective_n': collective,
                          'requested_moments_nm': moments, 'unclamped_motor_commands_n': requested,
                          'allocation_saturated': commands != requested}

    report = simulate_rigid_body(plant, controller=control)
    report['model'] = 'synthetic controlled rigid body with vertical pressure filter'
    report['controller_configuration'] = settings
    report['limitations'].extend(['Horizontal position, velocity and full attitude are ideal model state',
                                  'Vertical acceleration is a synthetic world frame signal rather than a body frame IMU',
                                  'Controller is a small angle simulation example with no flight safety supervisor',
                                  'No route planner, collision avoidance or physical aircraft is connected'])
    return report
