"""Module: detect — file discovery and classification."""
from __future__ import annotations

from pathlib import Path

MD_EXTENSIONS = {".md"}
SKIP_DIRS = {".git", ".vscode", "_meta", "memory-archive", "scripts", "vault-out"}


def collect_files(root: Path) -> list[Path]:
    """Return all .md files in vault, skipping hidden/system dirs."""
    files = []
    for md_file in root.rglob("*.md"):
        if _should_skip(md_file, root):
            continue
        files.append(md_file)
    return files


def _should_skip(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    if any(p.startswith(".") for p in parts):
        return True
    if any(p in SKIP_DIRS for p in parts):
        return True
    return False
