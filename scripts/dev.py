"""Start the complete local app, using an isolated research database by default."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


class FrontendHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if any(part.startswith('.') for part in unquote(urlsplit(self.path).path).split('/') if part):
            self.send_error(404)
            return
        if urlsplit(self.path).path == '/config.js':
            body = ('window.PULSEBOARD_API_BASE = ' + json.dumps(self.server.api_url) + ';\n').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def log_message(self, *args):
        pass


def model_environment(environment):
    for cache, key in [('backtest-model', 'SENTIMENT_GENERAL_MODEL'), ('pidgin-model', 'SENTIMENT_PIDGIN_MODEL')]:
        manifest = ROOT / 'NLP_Service/.cache' / cache / 'manifest.json'
        if manifest.exists() and key not in environment:
            raw = json.loads(manifest.read_text())
            snapshot = Path(raw['snapshot_path'])
            if not snapshot.is_dir():
                snapshot = manifest.parent / 'hub' / ('models--' + raw['repository'].replace('/', '--')) / 'snapshots' / raw['revision']
            if snapshot.is_dir():
                environment[key] = str(snapshot)
    environment.setdefault('HF_HUB_OFFLINE', '1')
    environment.setdefault('HF_HOME', str(ROOT / 'NLP_Service/.cache/huggingface'))
    environment.setdefault('OMP_NUM_THREADS', '4')
    environment.setdefault('TOKENIZERS_PARALLELISM', 'false')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', choices=['demo', 'configured'], default='demo', help='demo uses separate SQLite; configured uses Backend/.env')
    parser.add_argument('--frontend-port', type=int, default=8080)
    parser.add_argument('--api-port', type=int, default=8001)
    parser.add_argument('--nlp-port', type=int, default=8000)
    args = parser.parse_args()
    python = ROOT / '.venv/bin/python'
    php = shutil.which('php')
    if not python.exists() or not php or not (ROOT / 'Backend/vendor/autoload.php').exists():
        raise SystemExit('Python .venv, PHP and Backend/vendor are required. See docs/TESTING_THE_APP.md.')
    ports = [args.frontend_port, args.api_port, args.nlp_port]
    if len(set(ports)) != 3:
        raise SystemExit('The three server ports must be different.')
    for port in ports:
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', port))
            except OSError:
                raise SystemExit(f'Port {port} is unavailable. Stop its existing service or choose another port.')
    if args.database == 'demo' and (ROOT / 'Backend/bootstrap/cache/config.php').exists():
        raise SystemExit('Laravel configuration is cached. Run php artisan config:clear in Backend before using the isolated demo database.')
    env = os.environ.copy()
    env['NLP_SERVICE_URL'] = f'http://127.0.0.1:{args.nlp_port}'
    env['APP_URL'] = f'http://127.0.0.1:{args.api_port}'
    env['APP_ENV'] = 'local'
    if args.database == 'demo':
        database = ROOT / 'Backend/database/research-demo.sqlite'
        database.touch(exist_ok=True)
        env.update(DB_CONNECTION='sqlite', DB_DATABASE=str(database), DB_URL='', CACHE_STORE='file', SESSION_DRIVER='file')
    subprocess.run([str(python), str(ROOT / 'Frontend/scripts/version_assets.py')], check=True)
    print(f'Preparing {args.database} database (existing data is preserved)…', flush=True)
    for command in [['migrate', '--force'], ['research:seed-itel'], ['research:prepare-workspace']]:
        subprocess.run([php, 'artisan', *command], cwd=ROOT / 'Backend', env=env, check=True)
    model_environment(env)
    logs = ROOT / '.logs'
    logs.mkdir(exist_ok=True)
    processes, handles, server = [], [], None
    try:
        for name, command, cwd in [
            ('nlp', [str(python), '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', str(args.nlp_port)], ROOT / 'NLP_Service'),
            ('backend', [php, 'artisan', 'serve', '--host=127.0.0.1', f'--port={args.api_port}', '--no-reload'], ROOT / 'Backend'),
            ('tracking', [php, 'artisan', 'products:track', '--watch', '--sleep=30'], ROOT / 'Backend'),
        ]:
            handle = (logs / f'{name}.log').open('a')
            handles.append(handle)
            processes.append(subprocess.Popen(command, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True))
        print('Loading sentiment models; server logs are in .logs/.', flush=True)
        deadline = time.monotonic() + 180
        pending = {f'http://127.0.0.1:{args.nlp_port}/health', f'http://127.0.0.1:{args.api_port}/api/status'}
        while pending:
            if any(process.poll() is not None for process in processes):
                raise RuntimeError('A service stopped. Inspect .logs/nlp.log and .logs/backend.log.')
            for url in list(pending):
                try:
                    with urlopen(url, timeout=1) as response:
                        payload = json.load(response)
                    if url.endswith('/health'):
                        print('Sentiment model status: ' + payload['mode'], flush=True)
                    pending.remove(url)
                except (OSError, ValueError):
                    pass
            if pending:
                if time.monotonic() > deadline:
                    raise RuntimeError('Services did not become ready within 180 seconds. Inspect .logs/.')
                time.sleep(.5)
        handler = partial(FrontendHandler, directory=str(ROOT / 'Frontend'))
        server = ThreadingHTTPServer(('127.0.0.1', args.frontend_port), handler)
        server.api_url = env['APP_URL'] + '/api'
        server.timeout = 1
        print(f'App ready: http://127.0.0.1:{args.frontend_port}\nSign in with demo@pulseboard.test / PulseboardDemo!2026. Open a product to import reviews. Ctrl+C stops these servers.', flush=True)
        while all(process.poll() is None for process in processes):
            server.handle_request()
    except KeyboardInterrupt:
        print('\nStopping local app…', flush=True)
    finally:
        if server:
            server.server_close()
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        for handle in handles:
            handle.close()


if __name__ == '__main__':
    main()
