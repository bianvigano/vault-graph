"""Run: uv run python check_editor.py (uses a disposable Vault)."""
import functools
import http.client
import http.server
import json
import tempfile
import threading
from pathlib import Path
from vault_graph.viewer import PreviewHandler

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    doc = root / 'test.md'
    doc.write_text('# Awal', encoding='utf-8')
    PreviewHandler.vault_dir = root
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(PreviewHandler, directory=folder))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(method, path, payload=None, origin=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        connection.request(method, path, json.dumps(payload) if payload else None, headers)
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result
    try:
        status, data = request('GET', '/api/file?path=test.md')
        assert status == 200 and data['content'] == '# Awal'
        payload = {'path': 'test.md', 'content': '# Baru', 'mtime_ns': data['mtime_ns']}
        assert request('PUT', '/api/file', payload)[0] == 200
        assert doc.read_text() == '# Baru'
        assert request('PUT', '/api/file', payload)[0] == 409
        assert request('GET', '/api/file?path=../outside.md')[0] == 404
        assert request('PUT', '/api/file', payload, 'https://evil.example')[0] == 400
        print('PASS: read, save, stale conflict, traversal, cross-origin rejection')
    finally:
        server.shutdown()
        server.server_close()
