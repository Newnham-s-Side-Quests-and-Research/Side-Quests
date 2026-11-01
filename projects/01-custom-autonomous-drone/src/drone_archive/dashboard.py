"""Serve a read only synthetic dashboard on the local machine."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from .scenarios import build_scenarios

ASSETS = Path(__file__).resolve().parents[2] / 'dashboard'

class LocalDashboard(ThreadingHTTPServer):
    def __init__(self, config, port=0):
        scenarios = build_scenarios(config)
        self.trace = json.dumps(scenarios[0]['report'], allow_nan=False).encode('utf-8')
        self.scenarios = json.dumps(scenarios, allow_nan=False).encode('utf-8')
        super().__init__(('127.0.0.1', port), DashboardHandler)

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        routes = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                  '/style.css': ('style.css', 'text/css; charset=utf-8')}
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
