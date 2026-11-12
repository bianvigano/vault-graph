"""Preview lokal dari snapshot SQLite, tanpa mengubah sumber Vault."""
from __future__ import annotations

import functools
import http.server
import json
import os
import tempfile
import threading
import urllib.parse
import webbrowser
from pathlib import Path


class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    vault_dir: Path
    write_lock = threading.Lock()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/file":
            self._send_file(parsed.query)
            return
        super().do_GET()

    def do_PUT(self):
        if urllib.parse.urlparse(self.path).path != "/api/file":
            self.send_error(404)
            return
        try:
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            if host != f"127.0.0.1:{self.server.server_port}" or (origin and origin != f"http://{host}"):
                raise ValueError("asal permintaan tidak diizinkan")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 6_000_000:
                raise ValueError("ukuran permintaan tidak valid")
            payload = json.loads(self.rfile.read(length))
            requested = Path(str(payload["path"]))
            relative = self._vault_relative(requested)
            content = payload["content"]
            target = (self.vault_dir / relative).resolve()
            if self.vault_dir.resolve() not in target.parents:
                raise ValueError("path di luar Vault")
            if target.suffix.lower() != ".md":
                raise ValueError("hanya file Markdown yang boleh disimpan")
            if not isinstance(content, str) or len(content) > 5_000_000:
                raise ValueError("isi file tidak valid atau terlalu besar")
            expected = payload.get("mtime_ns")
            with self.write_lock:
                if expected is None or target.stat().st_mtime_ns != int(expected):
                    raise RuntimeError("file berubah di luar editor; muat ulang dahulu")
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as stream:
                        temporary = stream.name
                        stream.write(content)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.chmod(temporary, target.stat().st_mode & 0o777)
                    os.replace(temporary, target)
                finally:
                    if temporary and os.path.exists(temporary):
                        os.unlink(temporary)
            self._json({"ok": True, "mtime_ns": str(target.stat().st_mtime_ns)})
        except Exception as exc:
            self._json({"ok": False, "error": str(exc)}, 409 if "berubah" in str(exc) else 400)

    def _vault_relative(self, requested):
        target = (self.vault_dir / requested).resolve()
        return target.relative_to(self.vault_dir.resolve())

    def _send_file(self, query):
        try:
            relative = self._vault_relative(Path(urllib.parse.parse_qs(query)["path"][0]))
            target = (self.vault_dir / relative).resolve()
            if relative.is_absolute() or self.vault_dir.resolve() not in target.parents or target.suffix.lower() != ".md":
                raise ValueError("path Markdown tidak valid")
            stat = target.stat()
            self._json({"ok": True, "path": str(relative), "content": target.read_text(encoding="utf-8"), "mtime_ns": str(stat.st_mtime_ns)})
        except Exception as exc:
            self._json({"ok": False, "error": str(exc)}, 404)

    def _json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_preview(out_dir: Path, vault_dir: Path | None = None, port: int = 0, open_browser: bool = True) -> None:
    PreviewHandler.vault_dir = (vault_dir or out_dir).resolve()
    handler = functools.partial(PreviewHandler, directory=str(out_dir))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}/graph.html"
        print(f"Preview Vault Graph: {url}", flush=True)
        print("Tekan Ctrl+C untuk berhenti.", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nPreview berhenti.")
