"""One-command, no-pip-required local launcher (Python 3.11+)."""
import argparse
import sys
import threading
import webbrowser
from cmdb_agent.server import Server, STATIC

def main():
    parser = argparse.ArgumentParser(description='CMDB Agent Lab · synthetic read-only demo')
    parser.add_argument('--port', type=int, default=8091)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error('Python 3.11 or newer is required')
    if not 1 <= args.port <= 65535:
        parser.error('port must be 1-65535')
    if not (STATIC / 'index.html').exists():
        parser.error('Missing prebuilt web/dist. Run npm ci && npm run build in web/')
    try:
        server = Server(('127.0.0.1', args.port))
    except OSError:
        parser.error(f'Port {args.port} unavailable; try --port 8092')
    url = f'http://127.0.0.1:{server.server_port}'
    print('CMDB Agent Lab: ' + url + '\nSynthetic data / read-only / Ctrl+C to stop', flush=True)
    if not args.no_browser:
        timer = threading.Timer(0.6, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
