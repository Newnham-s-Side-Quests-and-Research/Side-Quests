import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.telemetry_frames import FrameError, MAX_FRAME_BYTES, TelemetryMonitor, parse_frame


def sample():
    return {'schema_version': 1, 'device_id': 'drone_1', 'sequence': 4, 'timestamp_ms': 1000,
            'sensors': {'pressure_pa': 101325, 'altitude_m': None, 'acceleration_m_s2': [0, 0, 9.81]},
            'motors': {'front_left': {'rpm': 1200}, 'front_right': None,
                       'rear_left': {'rpm': None}, 'rear_right': {'rpm': 0}},
            'battery': {'voltage_v': 11.1, 'current_a': 2.5, 'charge_percent': 70},
            'position': {'latitude_deg': 0, 'longitude_deg': 0, 'altitude_m': None}}


def encode(value):
    return json.dumps(value).encode('utf-8')


class FrameTests(unittest.TestCase):
    def test_valid_frame_preserves_unknowns_and_zero_coordinates(self):
        frame = parse_frame(encode(sample()))
        self.assertIsNone(frame['sensors']['altitude_m'])
        self.assertIsNone(frame['motors']['front_right'])
        self.assertIsNone(frame['motors']['rear_left']['rpm'])
        self.assertEqual(frame['motors']['rear_right']['rpm'], 0)
        self.assertEqual(frame['position']['latitude_deg'], 0)
        self.assertEqual(frame['battery']['voltage_v'], 11.1)

    def test_invalid_json_and_duplicate_fields_are_rejected(self):
        for payload in (b'\xff', b'{', b'{"schema_version":1,"schema_version":1}',
                        b'{"value":NaN}', b'x' * (MAX_FRAME_BYTES + 1), 'not bytes'):
            with self.subTest(payload=str(payload)[:20]), self.assertRaises(FrameError):
                parse_frame(payload)

    def test_invalid_values_and_unknown_fields_are_rejected(self):
        variants = []
        for field, value in [('schema_version', True), ('device_id', 'invalid device'),
                             ('sequence', -1), ('timestamp_ms', 2**53), ('unexpected', 1)]:
            obj = sample(); obj[field] = value; variants.append(obj)
        for group, field, value in [('sensors', 'pressure_pa', 0), ('sensors', 'acceleration_m_s2', [1, 2]),
                                    ('battery', 'charge_percent', 101), ('position', 'latitude_deg', 91),
                                    ('motors', 'front_left', {'rpm': -1})]:
            obj = sample(); obj[group][field] = value; variants.append(obj)
        for obj in variants:
            with self.subTest(obj=obj), self.assertRaises(FrameError):
                parse_frame(encode(obj))

    def test_unavailable_battery_and_position_are_explicit(self):
        obj = sample(); obj['battery'] = None; obj['position'] = None
        obj['sensors'] = {'pressure_pa': None, 'altitude_m': None, 'acceleration_m_s2': None}
        result = parse_frame(encode(obj))
        self.assertIsNone(result['battery'])
        self.assertIsNone(result['position'])
        self.assertIsNone(result['sensors']['pressure_pa'])

    def test_command_validates_frame_and_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'frame.json'
            env = os.environ.copy(); env['PYTHONPATH'] = str(ROOT / 'src')
            command = [sys.executable, '-m', 'drone_archive', 'validate-frame', str(path)]
            path.write_bytes(encode(sample()))
            result = subprocess.run(command, cwd=temporary, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['motors']['front_left']['rpm'], 1200)
            path.write_bytes(b'{"device_id":"a","device_id":"b"}')
            result = subprocess.run(command, cwd=temporary, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Duplicate field', result.stderr)


class MonitorTests(unittest.TestCase):
    def test_freshness_order_and_copy_isolation(self):
        monitor = TelemetryMonitor('drone_1', 2)
        self.assertEqual(monitor.snapshot(0)['state'], 'unavailable')
        monitor.accept(encode(sample()), 10)
        self.assertEqual(monitor.snapshot(12)['state'], 'current')
        snapshot = monitor.snapshot(12.1)
        self.assertEqual(snapshot['state'], 'stale')
        snapshot['frame']['motors']['front_left']['rpm'] = -1
        self.assertEqual(monitor.snapshot(12.1)['frame']['motors']['front_left']['rpm'], 1200)
        with self.assertRaises(FrameError): monitor.accept(encode(sample()), 13)
        with self.assertRaises(FrameError): monitor.snapshot(9)
        changed = sample(); changed['sequence'] = 5
        with self.assertRaises(FrameError): monitor.accept(encode(changed), 9)
        self.assertEqual(monitor.snapshot(12.1)['frame']['sequence'], 4)
        monitor.accept(encode(changed), 13)
        self.assertEqual(monitor.snapshot(13)['state'], 'current')

    def test_other_devices_and_invalid_time_do_not_replace_state(self):
        monitor = TelemetryMonitor('drone_1', 1)
        monitor.accept(encode(sample()), 2)
        other = sample(); other['device_id'] = 'other'; other['sequence'] = 99
        with self.assertRaises(FrameError): monitor.accept(encode(other), 3)
        with self.assertRaises(FrameError): monitor.accept(encode(sample()), math.inf)
        self.assertEqual(monitor.snapshot(2)['frame']['sequence'], 4)

    def test_concurrent_duplicate_frames_only_accept_once(self):
        monitor = TelemetryMonitor('drone_1', 1)
        accepted = []
        def submit():
            try:
                monitor.accept(encode(sample()), 1)
                accepted.append(True)
            except FrameError:
                pass
        threads = [threading.Thread(target=submit) for _ in range(8)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(len(accepted), 1)


if __name__ == '__main__':
    unittest.main()
