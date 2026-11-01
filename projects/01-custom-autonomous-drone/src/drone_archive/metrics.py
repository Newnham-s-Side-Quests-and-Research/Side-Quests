"""Summarise a synthetic closed loop run with explicit denominators."""
import math

class MetricsError(ValueError):
    pass

def summarise(report):
    if not isinstance(report, dict) or not isinstance(report.get('trace'), list) or not report['trace']:
        raise MetricsError('A nonempty simulation trace is required')
    rows = report['trace']
    config = report['configuration']
    target = config['target_altitude_m']
    tracking_errors = [row['truth']['altitude_m'] - target for row in rows]
    estimation_errors = [row['estimate']['altitude_m'] - row['truth']['altitude_m'] for row in rows]
    def count_update(sensor, accepted):
        return sum(1 for row in rows if row['updates'][sensor] is not None and row['updates'][sensor]['accepted'] is accepted)
    scheduled_gps = [row for row in rows if row['step'] % config['gps_interval_steps'] == 0]
    return {'sample_count': len(rows), 'elapsed_seconds': rows[-1]['time_s'], 'target_altitude_m': target,
            'tracking_rmse_m': math.sqrt(sum(x * x for x in tracking_errors) / len(rows)),
            'estimation_rmse_m': math.sqrt(sum(x * x for x in estimation_errors) / len(rows)),
            'maximum_absolute_tracking_error_m': max(abs(x) for x in tracking_errors),
            'final_altitude_m': report['final']['altitude_m'],
            'maximum_thrust_n': max(row['control']['thrust_n'] for row in rows),
            'degraded_steps': sum(row['control']['state'] == 'degraded' for row in rows),
            'pressure_accepted': count_update('pressure', True), 'pressure_rejected': count_update('pressure', False),
            'pressure_missing': sum(row['sensors']['pressure_pa'] is None for row in rows),
            'gps_scheduled': len(scheduled_gps), 'gps_accepted': count_update('gps', True),
            'gps_rejected': count_update('gps', False),
            'gps_missing_on_schedule': sum(row['sensors']['gps_altitude_m'] is None for row in scheduled_gps),
            'imu_missing': sum(row['sensors']['imu_acceleration_m_s2'] is None for row in rows)}
