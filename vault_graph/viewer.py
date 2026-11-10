"""Preview lokal dari snapshot SQLite, tanpa mengubah sumber Vault."""
from __future__ import annotations

import functools
import http.server
import webbrowser
from pathlib import Path


def serve_preview(out_dir: Path, port: int = 0, open_browser: bool = True) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out_dir))
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
