"""Process a supplied observation sequence without controlling hardware."""
from .monitor import MonitoringError, ResidualMonitor
from .supervisor import Supervisor


def evaluate_run(data):
    if not isinstance(data, dict) or set(data) != {'schema_version', 'monitor', 'supervisor', 'observations'}:
        raise MonitoringError('Input must contain the declared run fields')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise MonitoringError('Unsupported schema version')
    monitor_config = data['monitor']
    supervisor_config = data['supervisor']
    if not isinstance(monitor_config, dict) or set(monitor_config) != {'method', 'threshold'}:
        raise MonitoringError('Invalid monitor configuration')
    if not isinstance(supervisor_config, dict) or set(supervisor_config) != {'alarms_to_degrade', 'clears_to_recover', 'max_gap_seconds'}:
        raise MonitoringError('Invalid supervisor configuration')
    observations = data['observations']
    if not isinstance(observations, list) or not 1 <= len(observations) <= 100000:
        raise MonitoringError('Observations must be a nonempty bounded list')
    monitor = ResidualMonitor(monitor_config['method'], monitor_config['threshold'])
    supervisor = Supervisor(**supervisor_config)
    rows = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict) or set(observation) != {'timestamp_s', 'residual', 'variance'}:
            raise MonitoringError(f'Invalid observation at index {index}')
        assessment = monitor.evaluate(observation['residual'], observation['variance'])
        state = supervisor.update(observation['timestamp_s'], assessment['decision'])
        rows.append({'timestamp_s': observation['timestamp_s'], 'observation': observation.copy(),
                     'assessment': assessment, 'supervisor': state})
    return {'schema_version': 1, 'monitor': monitor_config.copy(), 'supervisor': supervisor_config.copy(),
            'observations_processed': len(rows), 'trace': rows,
            'limitations': ['No aircraft control or safety action', 'Thresholds require validation for the intended sensors',
                            'Output depends on the supplied measurements and variance',
                            'No physical safety or certification is established']}
