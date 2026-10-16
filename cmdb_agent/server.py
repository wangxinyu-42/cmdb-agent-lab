"""Local single-user HTTP/SSE demo. Not a production ASGI server."""
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from .providers import DemoProvider, LlamaProvider, model_configured
from .runtime import run
from .tools import execute_tool
from .evaluation import REPORT

STATIC = Path(__file__).resolve().parent.parent / 'web' / 'dist'

class Server(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address):
        super().__init__(address, Handler)
        self.model_gate = threading.BoundedSemaphore(1)

class Handler(BaseHTTPRequestHandler):
    server_version = 'CMDBLab/1.0'

    def log_message(self, fmt, *args):
        pass  # No question, credentials or raw provider errors in access logs.

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        super().end_headers()

    def json_response(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def allowed_host(self):
        port = self.server.server_port
        return self.headers.get('Host') in (f'127.0.0.1:{port}', f'localhost:{port}')

    def do_GET(self):
        if not self.allowed_host():
            self.json_response(403, {'error': 'invalid_host'})
            return
        parsed = urlparse(self.path)
        if parsed.path == '/api/health':
            self.json_response(200, {'status': 'ok', 'data': 'synthetic', 'version': '1.0.0'})
        elif parsed.path == '/api/config':
            self.json_response(200, {'llama_configured': model_configured(), 'default_mode': 'demo'})
        elif parsed.path == '/api/assets':
            params = parse_qs(parsed.query, keep_blank_values=True)
            if any(len(v) != 1 for v in params.values()):
                self.json_response(400, {'error': 'invalid_arguments'})
                return
            result = execute_tool('list_assets', {k: v[0] for k, v in params.items()})
            self.json_response(400 if 'error' in result else 200, result)
        elif parsed.path == '/api/evals':
            self.json_response(200, json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.exists()
                               else {'error': 'report_missing'})
        else:
            path = (STATIC / unquote(parsed.path).lstrip('/')).resolve()
            if not path.is_relative_to(STATIC.resolve()):
                self.json_response(404, {'error': 'not_found'})
                return
            if parsed.path == '/':
                path = STATIC / 'index.html'
            if not path.is_file():
                self.json_response(404, {'error': 'not_found', 'hint': 'Build web with npm run build'})
                return
            data = path.read_bytes()
            self.send_response(200)
            mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
            if path.suffix == '.js':
                mime = 'application/javascript'
            self.send_header('Content-Type', mime + ('; charset=utf-8' if mime.startswith('text/') or path.suffix == '.js' else ''))
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def do_POST(self):
        port = self.server.server_port
        origins = (f'http://127.0.0.1:{port}', f'http://localhost:{port}')
        if not self.allowed_host() or self.headers.get('Origin') not in (None, *origins):
            self.json_response(403, {'error': 'invalid_origin'})
            return
        if self.path != '/api/chat':
            self.json_response(404, {'error': 'not_found'})
            return
        if self.headers.get_content_type() != 'application/json' or self.headers.get('Transfer-Encoding'):
            self.json_response(415, {'error': 'json_required'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192:
                raise ValueError('size')
            self.connection.settimeout(5)
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict) or set(body) - {'question', 'mode'}:
                raise ValueError('shape')
            q = body.get('question')
            mode = body.get('mode', 'demo')
            if not isinstance(q, str) or not q.strip() or len(q) > 2000 or mode not in ('demo', 'llama'):
                raise ValueError('input')
        except (ValueError, TimeoutError, UnicodeDecodeError):
            self.json_response(400, {'error': 'invalid_request'})
            return
        if mode == 'llama' and not model_configured():
            self.json_response(409, {'error': 'model_not_configured'})
            return
        gated = mode == 'llama'
        if gated and not self.server.model_gate.acquire(blocking=False):
            self.json_response(429, {'error': 'model_busy'})
            return
        try:
            provider = LlamaProvider() if gated else DemoProvider()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True
            for event in run(q, provider):
                data = f"event: {event['event']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                self.wfile.write(data.encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass
        finally:
            if gated:
                self.server.model_gate.release()
