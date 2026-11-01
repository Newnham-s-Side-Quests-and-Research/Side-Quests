import json
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from drone_archive.dashboard import LocalDashboard

class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = json.loads((ROOT / 'fixtures' / 'closed-loop-scenario.json').read_text(encoding='utf-8'))
        cls.server = LocalDashboard(config)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2)

    def test_local_read_only_endpoints(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        with urlopen(self.url + '/', timeout=3) as response:
            self.assertEqual(response.status, 200)
            self.assertIn('text/html', response.headers['Content-Type'])
            self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])
            self.assertIn(b'Synthetic data', response.read())
        with urlopen(self.url + '/api/scenarios', timeout=3) as response:
            scenarios = json.load(response)
            self.assertEqual(len(scenarios), 4)
            self.assertEqual(scenarios[1]['metrics']['pressure_missing'], 30)
            self.assertEqual(scenarios[1]['metrics']['gps_missing_on_schedule'], 6)
        with urlopen(self.url + '/api/trace', timeout=3) as response:
            report = json.load(response)
            self.assertEqual(len(report['trace']), 300)
            self.assertIn('No original aircraft behaviour or physical flight safety is verified', report['limitations'])
        for path in ('/app.js', '/style.css', '/api/health'):
            with urlopen(self.url + path, timeout=3) as response: self.assertEqual(response.status, 200)

    def test_unknown_paths_and_writes_are_not_supported(self):
        with self.assertRaises(HTTPError) as missing:
            urlopen(self.url + '/../../fixtures/closed-loop-scenario.json', timeout=3)
        self.assertEqual(missing.exception.code, 404)
        with self.assertRaises(HTTPError) as method:
            urlopen(Request(self.url + '/api/trace', method='POST', data=b'{}'), timeout=3)
        self.assertEqual(method.exception.code, 501)

if __name__ == '__main__': unittest.main()
