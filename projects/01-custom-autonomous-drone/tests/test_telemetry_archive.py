from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.telemetry_archive import TelemetryArchive
from drone_archive.telemetry_frames import FrameError


def frame(sequence=1, device='drone_1'):
    data = {'schema_version': 1, 'device_id': device, 'sequence': sequence, 'timestamp_ms': 1000 + sequence,
            'sensors': {'pressure_pa': None, 'altitude_m': None, 'acceleration_m_s2': None},
            'motors': {'front_left': None, 'front_right': None, 'rear_left': None, 'rear_right': None},
            'battery': None, 'position': None}
    return json.dumps(data).encode('utf-8')


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'telemetry.sqlite'
        self.archive = TelemetryArchive(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_persistence_freshness_and_device_separation(self):
        self.archive.ingest(frame(), 2000)
        self.archive.ingest(frame(device='drone_2'), 2100)
        reopened = TelemetryArchive(self.path)
        self.assertEqual(reopened.latest('drone_1', 2500, 500)['state'], 'current')
        self.assertEqual(reopened.latest('drone_1', 2501, 500)['state'], 'stale')
        self.assertEqual(reopened.latest('unknown', 2500, 500)['state'], 'unavailable')
        self.assertEqual(reopened.latest('drone_2', 2500, 500)['frame']['device_id'], 'drone_2')

    def test_duplicate_does_not_refresh_and_conflicts_fail(self):
        self.archive.ingest(frame(), 2000)
        self.assertEqual(self.archive.ingest(frame(), 9000)['status'], 'duplicate')
        self.assertEqual(self.archive.latest('drone_1', 9000, 500)['state'], 'stale')
        changed = json.loads(frame()); changed['battery'] = {'voltage_v': 11, 'current_a': None, 'charge_percent': None}
        with self.assertRaises(FrameError): self.archive.ingest(json.dumps(changed).encode(), 9000)
        self.assertIsNone(self.archive.latest('drone_1', 9000, 500)['frame']['battery'])

    def test_out_of_order_or_backwards_receive_time_is_rejected(self):
        self.archive.ingest(frame(3), 2000)
        with self.assertRaises(FrameError): self.archive.ingest(frame(2), 2100)
        with self.assertRaises(FrameError): self.archive.ingest(frame(4), 1999)
        with self.assertRaises(FrameError): self.archive.latest('drone_1', 1999, 500)
        self.assertEqual(self.archive.latest('drone_1', 2000, 500)['frame']['sequence'], 3)

    def test_concurrent_duplicate_receipt_is_recorded_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.archive.ingest(frame(), 2000), range(8)))
        self.assertEqual(sum(result['status'] == 'recorded' for result in results), 1)
        self.assertEqual(sum(result['status'] == 'duplicate' for result in results), 7)

    def test_invalid_input_does_not_create_a_frame(self):
        with self.assertRaises(FrameError): self.archive.ingest(b'{invalid', 100)
        with self.assertRaises(FrameError): TelemetryArchive(':memory:')
        self.assertEqual(self.archive.latest('drone_1', 100, 500)['state'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
