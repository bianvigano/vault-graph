"""Module: watch — auto-rebuild graph on vault file changes."""
from __future__ import annotations

import hashlib
import os
import sys
import time
from pathlib import Path


def watch(root: Path, out_dir: Path, interval: float = 30.0):
    """Watch vault directory for changes with polling. Auto-rebuild on change.
    
    Usage: python3 -m vault_graph.main --watch
    """
    print(f"Watching: {root}")
    print(f"Output:  {out_dir}")
    print(f"Polling every {interval}s. Ctrl+C to stop.\n")

    # Initial snapshot
    state = _snapshot(root)

    try:
        while True:
            time.sleep(interval)
            new_state = _snapshot(root)
            
            if new_state != state:
                changed = set(new_state.keys()) ^ set(state.keys())
                if not changed:
                    changed = {k for k in new_state if new_state[k] != state.get(k)}
                
                n = len(changed)
                print(f"[{time.strftime('%H:%M:%S')}] {n} file(s) changed — rebuilding graph...")
                
                # Run rebuild
                from vault_graph.main import rebuild
                rebuild(root, out_dir)
                
                state = new_state
                print(f"  Done. {out_dir / 'graph.html'}")
    except KeyboardInterrupt:
        print("\nWatcher stopped.")


def _snapshot(root: Path) -> dict[str, str]:
    """Hash snapshot of all tracked files."""
    snap = {}
    from vault_graph.detect import collect_files
    for f in collect_files(root):
        try:
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            snap[str(f.relative_to(root))] = h
        except Exception:
            pass
    return snap
