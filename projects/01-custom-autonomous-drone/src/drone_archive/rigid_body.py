"""Synthetic rigid body quadrotor model. Never connect this model to hardware."""
import math
from .point_mass import _finite, _vector
from .simulation import SimulationError


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _quaternion(value):
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise SimulationError('Attitude must be a four element quaternion')
    q = [_finite(item, 'quaternion') for item in value]
    norm = math.hypot(*q)
    if not math.isfinite(norm) or norm < 1e-12:
        raise SimulationError('Quaternion norm must be finite and nonzero')
    return [item / norm for item in q]


def _body_z(q):
    w, x, y, z = q
    return [2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)]


def _attitude_step(q, omega, dt):
    w, x, y, z = q
    p, r, s = omega
    derivative = [-x * p - y * r - z * s, w * p + y * s - z * r,
                  w * r + z * p - x * s, w * s + x * r - y * p]
    return _quaternion([q[i] + 0.5 * dt * derivative[i] for i in range(4)])


def _window(value, steps):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise SimulationError('Motor outage must be an object')
    motor, start, end = value.get('motor'), value.get('start'), value.get('end')
    if any(isinstance(item, bool) or not isinstance(item, int) for item in (motor, start, end)):
        raise SimulationError('Motor outage values must be integers')
    if not (0 <= motor < 4 and 0 <= start < end <= steps):
        raise SimulationError('Motor outage is outside the supported range')
    return motor, start, end


def simulate_rigid_body(config, controller=None):
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise SimulationError('Rigid body configuration must use schema version 1')
    steps = config.get('steps')
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 100000:
        raise SimulationError('steps must be an integer between 1 and 100000')
    dt = _finite(config.get('dt_seconds'), 'dt_seconds', 0)
    mass = _finite(config.get('mass_kg'), 'mass_kg', 0)
    tau = _finite(config.get('motor_time_constant_s'), 'motor_time_constant_s', 0)
    if min(dt, mass, tau) <= 0:
        raise SimulationError('Timestep, mass and motor time constant must be positive')
    gravity = _finite(config.get('gravity_m_s2'), 'gravity_m_s2', 0)
    drag = _finite(config.get('drag_n_per_m_s'), 'drag_n_per_m_s', 0)
    yaw_factor = _finite(config.get('yaw_moment_per_thrust_m'), 'yaw_moment_per_thrust_m', 0)
    inertia = _vector(config.get('inertia_kg_m2'), 'inertia_kg_m2')
    if min(inertia) <= 0 or any(inertia[i] > inertia[(i + 1) % 3] + inertia[(i + 2) % 3] for i in range(3)):
        raise SimulationError('Inertia must be positive and satisfy the triangle inequalities')
    positions = config.get('rotor_positions_m')
    if not isinstance(positions, list) or len(positions) != 4:
        raise SimulationError('Four rotor positions are required')
    positions = [_vector(item, 'rotor position') for item in positions]
    spins = config.get('rotor_spin_signs')
    if not isinstance(spins, list) or len(spins) != 4 or any(type(sign) is not int or sign not in (-1, 1) for sign in spins):
        raise SimulationError('Four rotor spin signs of minus one or one are required')
    def thrusts(key):
        value = config.get(key)
        if not isinstance(value, list) or len(value) != 4:
            raise SimulationError(f'{key} must contain four thrust values')
        return [_finite(item, key, 0) for item in value]
    command, thrust = thrusts('command_thrust_n'), thrusts('initial_thrust_n')
    wind = _vector(config.get('wind_m_s'), 'wind_m_s')
    position = _vector(config.get('initial_position_m'), 'initial_position_m')
    velocity = _vector(config.get('initial_velocity_m_s'), 'initial_velocity_m_s')
    omega = _vector(config.get('initial_body_rate_rad_s'), 'initial_body_rate_rad_s')
    attitude = _quaternion(config.get('initial_quaternion_wxyz'))
    if position[2] <= 0:
        raise SimulationError('Initial altitude must be above ground')
    outage = _window(config.get('motor_outage'), steps)
    alpha = -math.expm1(-dt / tau)
    trace = []
    contact = None
    previous_acceleration = None
    for step in range(steps):
        applied_command = command.copy()
        controller_record = None
        if controller is not None:
            controller_state = {'step': step, 'time_s': step * dt, 'position_m': position.copy(),
                                'velocity_m_s': velocity.copy(), 'quaternion_wxyz': attitude.copy(),
                                'body_rate_rad_s': omega.copy(),
                                'previous_acceleration_m_s2': None if previous_acceleration is None else previous_acceleration.copy()}
            response = controller(controller_state)
            if not isinstance(response, tuple) or len(response) != 2:
                raise SimulationError('Controller must return commands and a record')
            values, controller_record = response
            if not isinstance(values, (tuple, list)) or len(values) != 4:
                raise SimulationError('Controller must supply four motor commands')
            applied_command = [_finite(item, 'controller motor command', 0) for item in values]
            if not isinstance(controller_record, dict):
                raise SimulationError('Controller record must be an object')
        if outage and outage[1] <= step < outage[2]:
            applied_command[outage[0]] = 0.0
        direction = _body_z(attitude)
        total = sum(thrust)
        force = [total * direction[i] - drag * (velocity[i] - wind[i]) for i in range(3)]
        force[2] -= mass * gravity
        acceleration = [item / mass for item in force]
        moment = [sum(positions[j][1] * thrust[j] for j in range(4)),
                  -sum(positions[j][0] * thrust[j] for j in range(4)),
                  yaw_factor * sum(spins[j] * thrust[j] for j in range(4))]
        angular_momentum = [inertia[i] * omega[i] for i in range(3)]
        gyroscopic = _cross(omega, angular_momentum)
        angular_acceleration = [(moment[i] - gyroscopic[i]) / inertia[i] for i in range(3)]
        trace.append({'step': step, 'time_s': step * dt, 'position_m': position.copy(),
                      'velocity_m_s': velocity.copy(), 'quaternion_wxyz': attitude.copy(),
                      'body_rate_rad_s': omega.copy(), 'motor_thrust_n': thrust.copy(),
                      'motor_command_n': applied_command, 'force_world_n': force,
                      'moment_body_nm': moment, 'acceleration_m_s2': acceleration,
                      'angular_acceleration_rad_s2': angular_acceleration, 'controller': controller_record})
        next_position = [position[i] + velocity[i] * dt for i in range(3)]
        next_velocity = [velocity[i] + acceleration[i] * dt for i in range(3)]
        next_omega = [omega[i] + angular_acceleration[i] * dt for i in range(3)]
        next_attitude = _attitude_step(attitude, omega, dt)
        next_thrust = [thrust[i] + alpha * (applied_command[i] - thrust[i]) for i in range(4)]
        if not all(math.isfinite(item) for item in next_position + next_velocity + next_omega + next_thrust):
            raise SimulationError(f'Nonfinite rigid body state at step {step}')
        if next_position[2] <= 0:
            fraction = position[2] / (position[2] - next_position[2])
            position = [position[i] + fraction * (next_position[i] - position[i]) for i in range(3)]
            velocity = [velocity[i] + fraction * (next_velocity[i] - velocity[i]) for i in range(3)]
            position[2] = 0.0
            contact = {'type': 'ground_contact', 'time_s': (step + fraction) * dt, 'after_step': step}
            # The terminal attitude and motors are not interpolated.
            break
        position, velocity, omega, attitude, thrust = next_position, next_velocity, next_omega, next_attitude, next_thrust
        previous_acceleration = acceleration
    limitations = ['Synthetic parameters are not measured from the original aircraft',
                   'No battery, propeller aerodynamics or impact dynamics',
                   'Motor thrust follows an assumed first order response',
                   'Explicit Euler integration and linear drag approximate the dynamics',
                   'Terminal attitude and motor state are not interpolated at ground contact',
                   'Not suitable for controlling or validating an aircraft']
    if controller is None:
        limitations.insert(1, 'No controller or sensors')
    return {'model': 'synthetic rigid body with prescribed motor commands' if controller is None else 'synthetic rigid body with supplied controller', 'configuration': config,
            'trace': trace, 'final': {'position_m': position, 'velocity_m_s': velocity},
            'terminal_event': contact,
            'limitations': limitations}
