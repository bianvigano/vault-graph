"""Module: security — input validation and sanitization."""
from __future__ import annotations

import re
from pathlib import Path

MAX_LABEL_LEN = 256
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_label(text: str) -> str:
    """Strip control chars, cap length. No HTML escaping (handled by json.dumps/D3)."""
    text = CONTROL_CHAR_RE.sub("", text)
    text = text[:MAX_LABEL_LEN]
    return text.strip()


def validate_path(path: str, vault_root: Path) -> Path | None:
    """Validate a path is inside vault root. Returns resolved Path or None."""
    try:
        resolved = (vault_root / path).resolve()
        if not str(resolved).startswith(str(vault_root.resolve())):
            return None
        return resolved
    except Exception:
        return None


def validate_graph_path(path: str, out_dir: Path) -> Path | None:
    """Validate a graph output path is inside output dir."""
    try:
        resolved = out_dir / path
        if not str(resolved.resolve()).startswith(str(out_dir.resolve())):
            return None
        return resolved
    except Exception:
        return None
