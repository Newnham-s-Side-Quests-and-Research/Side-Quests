"""Persist validated telemetry frames to a local SQLite database.

The caller must authenticate sources and protect access to the database. This
module does not open a radio connection, encrypt records or control aircraft.
"""
import hashlib
import json
import sqlite3
from .telemetry_frames import FrameError, _integer, parse_frame


class TelemetryArchive:
    def __init__(self, path):
        self.path = str(path)
        if self.path == ':memory:':
            raise FrameError('A persistent database path is required')
        connection = self._connect()
        try:
            connection.execute('''CREATE TABLE IF NOT EXISTS telemetry_frames (
                device_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                received_at_ms INTEGER NOT NULL,
                payload_hash TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY(device_id, sequence)
            )''')
        finally:
            connection.close()

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10, isolation_level=None)

    def ingest(self, payload, received_at_ms):
        frame = parse_frame(payload)
        received = _integer(received_at_ms, 'Receive timestamp')
        canonical = json.dumps(frame, sort_keys=True, separators=(',', ':'), allow_nan=False)
        digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        connection = self._connect()
        try:
            connection.execute('BEGIN IMMEDIATE')
            prior = connection.execute('SELECT payload_hash FROM telemetry_frames WHERE device_id = ? AND sequence = ?',
                                       (frame['device_id'], frame['sequence'])).fetchone()
            if prior is not None:
                if prior[0] != digest:
                    raise FrameError('Sequence was already used for different telemetry')
                connection.commit()
                return {'device_id': frame['device_id'], 'sequence': frame['sequence'], 'status': 'duplicate'}
            latest = connection.execute('SELECT sequence, received_at_ms FROM telemetry_frames WHERE device_id = ? ORDER BY sequence DESC LIMIT 1',
                                        (frame['device_id'],)).fetchone()
            if latest is not None and (frame['sequence'] <= latest[0] or received < latest[1]):
                raise FrameError('Telemetry is out of order')
            connection.execute('INSERT INTO telemetry_frames VALUES (?, ?, ?, ?, ?)',
                               (frame['device_id'], frame['sequence'], received, digest, canonical))
            connection.commit()
            return {'device_id': frame['device_id'], 'sequence': frame['sequence'], 'status': 'recorded'}
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def latest(self, device_id, now_ms, stale_after_ms):
        if not isinstance(device_id, str) or not 1 <= len(device_id) <= 64 or any(not (c.isascii() and (c.isalnum() or c in '_-')) for c in device_id):
            raise FrameError('Invalid device identifier')
        now = _integer(now_ms, 'Current timestamp')
        stale_after = _integer(stale_after_ms, 'Stale interval')
        if stale_after == 0:
            raise FrameError('Stale interval must be positive')
        connection = self._connect()
        try:
            row = connection.execute('SELECT received_at_ms, payload_json FROM telemetry_frames WHERE device_id = ? ORDER BY sequence DESC LIMIT 1',
                                     (device_id,)).fetchone()
        finally:
            connection.close()
        if row is None:
            return {'state': 'unavailable', 'age_ms': None, 'frame': None}
        if now < row[0]:
            raise FrameError('Current timestamp precedes the recorded receive time')
        age = now - row[0]
        return {'state': 'stale' if age > stale_after else 'current', 'age_ms': age, 'frame': json.loads(row[1])}
