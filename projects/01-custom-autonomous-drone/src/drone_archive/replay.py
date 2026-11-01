"""Replay synthetic sensor observations through the vertical filter."""
from .estimation import VerticalFilter
from .simulation import simulate

REPLAY_SETTINGS = {'initial_altitude_m': 0.0, 'initial_velocity_m_s': 0.0,
                   'altitude_variance_m2': 100.0, 'velocity_variance_m2_s2': 4.0,
                   'acceleration_variance_m2_s4': 0.1, 'pressure_variance_pa2': 25.0,
                   'gps_altitude_variance_m2': 0.25, 'innovation_limit': 25.0}

def estimate_scenario(config, simulation=None):
    if simulation is None:
        simulation = simulate(config)
    elif simulation.get('config') != config:
        raise ValueError('Simulation and estimation configurations do not match')
    settings = REPLAY_SETTINGS.copy()
    estimator = VerticalFilter(settings['initial_altitude_m'], settings['initial_velocity_m_s'],
                               settings['altitude_variance_m2'], settings['velocity_variance_m2_s2'])
    rows = []
    for sample in simulation['trace']:
        pressure_update = estimator.update_pressure(sample['barometer_pressure_pa'], settings['pressure_variance_pa2'], settings['innovation_limit'])
        gps_update = None
        if sample['gps_altitude_m'] is not None:
            gps_update = estimator.update_altitude(sample['gps_altitude_m'], settings['gps_altitude_variance_m2'], settings['innovation_limit'])
        rows.append({'step': sample['step'], 'time_s': sample['time_s'],
                     'reference_altitude_m': sample['altitude_m'], 'estimated_altitude_m': estimator.altitude_m,
                     'estimated_velocity_m_s': estimator.velocity_m_s, 'covariance': estimator.covariance,
                     'pressure_update': pressure_update, 'gps_update': gps_update})
        acceleration = sample['imu']['specific_force_z_m_s2'] - config['gravity_m_s2']
        estimator.predict(acceleration, config['dt_seconds'], settings['acceleration_variance_m2_s4'])
    return {'model': 'synthetic vertical state estimation', 'config': config, 'estimator_settings': settings,
            'trace': rows, 'limitations': ['Synthetic vertical position and velocity only',
              'Idealised IMU and pressure signals are not calibrated hardware',
              'Estimator output does not control the simulated aircraft',
              'No attitude, horizontal position or real GPS coordinates are estimated',
              'This result is not evidence of flight readiness']}
