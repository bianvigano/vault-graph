"""Module: cache — hash-based cache to skip unchanged files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_cache(cache_path: Path) -> dict:
    """Load cache from JSON file."""
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except Exception:
            pass
    return {}


def save_cache(cache_path: Path, cache: dict):
    """Save cache to JSON file."""
    cache_path.write_text(json.dumps(cache, indent=2))


def file_hash(path: Path) -> str:
    """SHA256 hash of file contents."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def split_files(files: list, cache: dict, root: Path) -> tuple[list, list, dict]:
    """Split files into cached (unchanged) and uncached (changed/new).
    
    Returns: (cached_files, uncached_files, updated_cache)
    """
    cached = []
    uncached = []
    new_cache = {}

    for f in files:
        rel = str(f.relative_to(root))
        h = file_hash(f)
        new_cache[rel] = h
        
        if rel in cache and cache[rel] == h:
            cached.append(f)
        else:
            uncached.append(f)

    return cached, uncached, new_cache
