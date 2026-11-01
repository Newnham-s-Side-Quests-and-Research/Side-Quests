"""Validate versioned aircraft telemetry without opening a connection.

This module accepts measurements supplied by a caller. It does not authenticate
their source or send commands to an aircraft.
"""
import json
import math
import threading


class FrameError(ValueError):
    pass


MOTOR_POSITIONS = ('front_left', 'front_right', 'rear_left', 'rear_right')
MAX_FRAME_BYTES = 65536


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FrameError(f'Duplicate field: {key}')
        result[key] = value
    return result


def _reject_constant(value):
    raise FrameError(f'Invalid numeric constant: {value}')


def _fields(value, required, optional, name):
    if not isinstance(value, dict):
        raise FrameError(f'{name} must be an object')
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing or extra:
        raise FrameError(f'{name} has missing or unexpected fields')


def _number(value, name, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FrameError(f'{name} must be a finite number')
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise FrameError(f'{name} is outside the supported range')
    return float(value)


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**53 - 1:
        raise FrameError(f'{name} must be a nonnegative safe integer')
    return value


def _optional_number(value, name, minimum=None, maximum=None):
    return None if value is None else _number(value, name, minimum, maximum)


def parse_frame(payload):
    if not isinstance(payload, (bytes, bytearray)) or len(payload) > MAX_FRAME_BYTES:
        raise FrameError('Frame must be UTF8 bytes within the size limit')
    try:
        data = json.loads(bytes(payload).decode('utf-8'), object_pairs_hook=_object, parse_constant=_reject_constant)
    except FrameError:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise FrameError('Frame is not valid UTF8 JSON') from exc
    _fields(data, {'schema_version', 'device_id', 'sequence', 'timestamp_ms', 'sensors', 'motors', 'battery', 'position'}, set(), 'Frame')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise FrameError('Unsupported telemetry schema')
    device = data['device_id']
    if not isinstance(device, str) or not 1 <= len(device) <= 64 or any(not (c.isascii() and (c.isalnum() or c in '_-')) for c in device):
        raise FrameError('Invalid device identifier')
    sequence = _integer(data['sequence'], 'Sequence')
    timestamp = _integer(data['timestamp_ms'], 'Timestamp')
    sensors = data['sensors']
    _fields(sensors, {'pressure_pa', 'altitude_m', 'acceleration_m_s2'}, set(), 'Sensors')
    pressure = _optional_number(sensors['pressure_pa'], 'Pressure', minimum=0)
    if pressure == 0:
        raise FrameError('Pressure must be positive when present')
    altitude = _optional_number(sensors['altitude_m'], 'Altitude')
    acceleration = sensors['acceleration_m_s2']
    if acceleration is not None:
        if not isinstance(acceleration, list) or len(acceleration) != 3:
            raise FrameError('Acceleration must contain three axes or be null')
        acceleration = [_number(axis, 'Acceleration') for axis in acceleration]
    motors = data['motors']
    _fields(motors, set(MOTOR_POSITIONS), set(), 'Motors')
    motor_result = {}
    for key in MOTOR_POSITIONS:
        motor = motors[key]
        if motor is None:
            motor_result[key] = None
            continue
        _fields(motor, {'rpm'}, set(), f'Motor {key}')
        motor_result[key] = {'rpm': _optional_number(motor['rpm'], 'Motor speed', minimum=0)}
    battery = data['battery']
    if battery is not None:
        _fields(battery, {'voltage_v', 'current_a', 'charge_percent'}, set(), 'Battery')
        battery = {'voltage_v': _optional_number(battery['voltage_v'], 'Battery voltage', minimum=0),
                   'current_a': _optional_number(battery['current_a'], 'Battery current'),
                   'charge_percent': _optional_number(battery['charge_percent'], 'Battery charge', 0, 100)}
    position = data['position']
    if position is not None:
        _fields(position, {'latitude_deg', 'longitude_deg', 'altitude_m'}, set(), 'Position')
        position = {'latitude_deg': _number(position['latitude_deg'], 'Latitude', -90, 90),
                    'longitude_deg': _number(position['longitude_deg'], 'Longitude', -180, 180),
                    'altitude_m': _optional_number(position['altitude_m'], 'Position altitude')}
    return {'schema_version': 1, 'device_id': device, 'sequence': sequence, 'timestamp_ms': timestamp,
            'sensors': {'pressure_pa': pressure, 'altitude_m': altitude, 'acceleration_m_s2': acceleration},
            'motors': motor_result, 'battery': battery, 'position': position}


class TelemetryMonitor:
    """Keep the newest accepted frame for one configured device in memory."""
    def __init__(self, device_id, stale_after_seconds):
        if not isinstance(device_id, str) or not 1 <= len(device_id) <= 64 or any(not (c.isascii() and (c.isalnum() or c in '_-')) for c in device_id):
            raise FrameError('Invalid device identifier')
        self.device_id = device_id
        self.stale_after = _number(stale_after_seconds, 'Stale interval', minimum=0)
        if self.stale_after <= 0:
            raise FrameError('Stale interval must be positive')
        self._frame = None
        self._received = None
        self._lock = threading.Lock()

    def accept(self, payload, received_monotonic):
        frame = parse_frame(payload)
        received = _number(received_monotonic, 'Receive time', minimum=0)
        if frame['device_id'] != self.device_id:
            raise FrameError('Frame is for a different device')
        with self._lock:
            if self._frame is not None and (frame['sequence'] <= self._frame['sequence'] or received < self._received):
                raise FrameError('Frame is out of order')
            self._frame = frame
            self._received = received

    def snapshot(self, now_monotonic):
        now = _number(now_monotonic, 'Current time', minimum=0)
        with self._lock:
            if self._frame is None:
                return {'state': 'unavailable', 'age_seconds': None, 'frame': None}
            if now < self._received:
                raise FrameError('Current time precedes the last receive time')
            age = now - self._received
            # Return a copy so callers cannot change the accepted frame.
            frame = json.loads(json.dumps(self._frame, allow_nan=False))
            return {'state': 'stale' if age > self.stale_after else 'current', 'age_seconds': age, 'frame': frame}
