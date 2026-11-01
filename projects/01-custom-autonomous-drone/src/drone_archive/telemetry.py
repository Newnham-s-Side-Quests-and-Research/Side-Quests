"""Build read only telemetry snapshots from the synthetic model."""
import math

class TelemetryError(ValueError):
    pass

def _number(value, name, allow_missing=False):
    if value is None and allow_missing:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise TelemetryError(f'{name} must be finite')
    return float(value)

def build_snapshot(sample):
    if not isinstance(sample, dict):
        raise TelemetryError('Sample must be an object')
    stamp = _number(sample.get('time_s'), 'Time')
    if stamp < 0:
        raise TelemetryError('Time must not be negative')
    links = sample.get('links')
    imu = sample.get('imu')
    if not isinstance(links, dict) or not isinstance(imu, dict):
        raise TelemetryError('Link and motion signals are required')
    wifi, bluetooth = links.get('wifi_available'), links.get('bluetooth_available')
    if not isinstance(wifi, bool) or not isinstance(bluetooth, bool):
        raise TelemetryError('Link availability must be boolean')
    pressure = _number(sample.get('barometer_pressure_pa'), 'Pressure')
    if pressure <= 0:
        raise TelemetryError('Pressure must be positive')
    altitude = _number(sample.get('altitude_signal_m'), 'Altitude signal', allow_missing=True)
    gps = _number(sample.get('gps_altitude_m'), 'GPS altitude', allow_missing=True)
    acceleration = _number(imu.get('specific_force_z_m_s2'), 'Vertical specific force')
    return {'source': 'synthetic simulation', 'time_s': stamp,
            'signals': {'altitude_m': altitude, 'pressure_pa': pressure, 'gps_altitude_m': gps,
                        'specific_force_z_m_s2': acceleration},
            'links': {'wifi_available': wifi, 'bluetooth_available': bluetooth},
            'motors': {name: 'not modelled' for name in ('front_left', 'front_right', 'rear_left', 'rear_right')},
            'battery': 'not modelled', 'position': 'not modelled'}
