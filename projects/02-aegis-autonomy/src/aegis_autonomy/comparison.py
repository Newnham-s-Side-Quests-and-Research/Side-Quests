"""Compare monitoring policies on the same labelled observation sequence."""
from .monitor import MonitoringError
from .runner import evaluate_run


def compare(data):
    if not isinstance(data, dict) or set(data) != {'schema_version','supervisor','monitors','observations'}:
        raise MonitoringError('Invalid comparison fields')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise MonitoringError('Unsupported schema version')
    monitors = data['monitors']
    labelled = data['observations']
    if not isinstance(monitors, list) or not 1 <= len(monitors) <= 100:
        raise MonitoringError('Monitors must be a nonempty bounded list')
    if not isinstance(labelled, list) or not 1 <= len(labelled) <= 100000:
        raise MonitoringError('Observations must be a nonempty bounded list')
    observations = []
    labels = []
    for item in labelled:
        if not isinstance(item, dict) or set(item) != {'timestamp_s','residual','variance','label'}:
            raise MonitoringError('Invalid labelled observation')
        if item['label'] not in ('healthy','fault','unknown'):
            raise MonitoringError('Invalid observation label')
        labels.append(item['label'])
        observations.append({key:item[key] for key in ('timestamp_s','residual','variance')})
    ids = set()
    results = []
    for item in monitors:
        if not isinstance(item, dict) or set(item) != {'monitor_id','method','threshold'}:
            raise MonitoringError('Invalid monitor configuration')
        name = item['monitor_id']
        if not isinstance(name, str) or not name.strip() or len(name) > 128 or name in ids:
            raise MonitoringError('Monitor identifiers must be unique and nonempty')
        ids.add(name)
        run = evaluate_run({'schema_version':1, 'monitor':{'method':item['method'],'threshold':item['threshold']},
                            'supervisor':data['supervisor'], 'observations':observations})
        rows = run['trace']
        healthy = sum(label == 'healthy' for label in labels)
        healthy_unavailable = sum(label == 'healthy' and row['assessment']['decision'] == 'unavailable'
                                  for label, row in zip(labels, rows))
        healthy_observed = healthy - healthy_unavailable
        alarms = sum(label == 'healthy' and row['assessment']['decision'] == 'alarm'
                     for label, row in zip(labels, rows))
        fault_windows = []
        index = 0
        while index < len(labels):
            if labels[index] != 'fault':
                index += 1
                continue
            first = index
            while index < len(labels) and labels[index] == 'fault':
                index += 1
            observed = next((row for row in rows[first:index] if row['assessment']['decision'] == 'alarm'), None)
            available = sum(row['assessment']['decision'] != 'unavailable' for row in rows[first:index])
            fault_windows.append({'start_s':rows[first]['timestamp_s'], 'end_s':rows[index - 1]['timestamp_s'],
                                  'available_samples':available, 'unavailable_samples':index - first - available,
                                  'detected':observed is not None,
                                  'detection_delay_s':None if observed is None else observed['timestamp_s'] - rows[first]['timestamp_s']})
        results.append({'monitor_id':name, 'monitor':run['monitor'], 'healthy_samples':healthy,
                        'healthy_observed_samples':healthy_observed, 'healthy_unavailable_samples':healthy_unavailable,
                        'healthy_alarm_samples':alarms,
                        'healthy_alarm_fraction':alarms / healthy_observed if healthy_observed else None,
                        'fault_windows':fault_windows, 'trace':rows})
    return {'schema_version':1, 'observations_processed':len(observations), 'results':results,
            'limitations':['Labels and observations are supplied by the caller',
                           'A sample fraction is not an operational false alarm rate per hour',
                           'Contiguous fault labels define windows and unknown labels interrupt them',
                           'A monitor alarm does not establish physical safety or the cause of a fault']}
