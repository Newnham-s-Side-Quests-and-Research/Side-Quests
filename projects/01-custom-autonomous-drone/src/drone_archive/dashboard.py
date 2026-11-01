"""Serve a read only synthetic dashboard on the local machine."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from copy import deepcopy
from pathlib import Path
from .scenarios import build_scenarios
from .mission3d import run_mission
from .navigation import run_navigation

ASSETS = Path(__file__).resolve().parents[2] / 'dashboard'

class LocalDashboard(ThreadingHTTPServer):
    def __init__(self, config, port=0):
        scenarios = build_scenarios(config)
        self.trace = json.dumps(scenarios[0]['report'], allow_nan=False).encode('utf-8')
        self.scenarios = json.dumps(scenarios, allow_nan=False).encode('utf-8')
        mission_file = ASSETS.parent / 'fixtures' / 'mission3d-scenario.json'
        mission_config = json.loads(mission_file.read_text(encoding='utf-8'))
        self.mission = json.dumps(run_mission(mission_config), allow_nan=False).encode('utf-8')
        nav_file = ASSETS.parent / 'fixtures' / 'navigation-scenario.json'
        nav_config = json.loads(nav_file.read_text(encoding='utf-8'))
        examples = []
        for name, wind in (('calm', 0), ('wind', 10)):
            settings = deepcopy(nav_config)
            settings['flight']['plant']['wind_m_s'] = [wind, 0, 0]
            result = run_navigation(settings)
            rows = result['flight']['trace']
            selected = rows[::20]
            if rows and selected[-1]['step'] != rows[-1]['step']:
                selected.append(rows[-1])
            samples = [{'step': row['step'], 'time_s': row['time_s'], 'position_m': row['position_m'],
                        'target_m': row['controller']['target_position_m'],
                        'estimated_altitude_m': row['controller']['estimated_altitude_m'],
                        'motor_thrust_n': row['motor_thrust_n']} for row in selected]
            examples.append({'id': name, 'wind_m_s': wind, 'status': result['status'],
                             'route': result['route'], 'waypoints_m': result['waypoints_m'],
                             'waypoint_events': result['waypoint_events'], 'samples': samples,
                             'terminal_event': result['flight']['terminal_event'],
                             'grid': settings['grid'], 'origin_m': settings['origin_m'],
                             'cell_size_m': settings['cell_size_m']})
        self.navigation = json.dumps(examples, allow_nan=False).encode('utf-8')
        super().__init__(('127.0.0.1', port), DashboardHandler)

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        routes = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                  '/style.css': ('style.css', 'text/css; charset=utf-8'),
                  '/calculations': ('calculations.html', 'text/html; charset=utf-8'),
                  '/calculations.css': ('calculations.css', 'text/css; charset=utf-8'),
                  '/navigation.js': ('navigation.js', 'text/javascript; charset=utf-8')}
        if self.path == '/api/navigation':
            return self.respond(200, 'application/json; charset=utf-8', self.server.navigation)
        if self.path == '/api/mission':
            return self.respond(200, 'application/json; charset=utf-8', self.server.mission)
        if self.path == '/api/scenarios':
            return self.respond(200, 'application/json; charset=utf-8', self.server.scenarios)
        if self.path == '/api/trace':
            return self.respond(200, 'application/json; charset=utf-8', self.server.trace)
        if self.path == '/api/health':
            return self.respond(200, 'application/json; charset=utf-8', b'{"status":"ok"}')
        if self.path in routes:
            name, content_type = routes[self.path]
            try:
                return self.respond(200, content_type, (ASSETS / name).read_bytes())
            except OSError:
                return self.respond(500, 'text/plain; charset=utf-8', b'Asset unavailable')
        return self.respond(404, 'text/plain; charset=utf-8', b'Not found')

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.respond(400, 'text/plain; charset=utf-8', b'Invalid content length')
        if length < 0 or length > 65536:
            return self.respond(413, 'text/plain; charset=utf-8', b'Request too large')
        if length:
            self.rfile.read(length)
        return self.respond(405, 'text/plain; charset=utf-8', b'Method not allowed')

    def respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
