"""Module: extract — deterministic extraction from markdown files.

Extracts:
  - Nodes: file path, title, headings, type (wiki/session/concept/discord/other)
  - Edges: [[wiki-links]], heading mentions (INFERRED), URL references (EXTRACTED)

Returns {nodes, edges} dict per file.
"""
from __future__ import annotations

import re
from pathlib import Path
from collections import defaultdict

WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HEADING_RE = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)
FRONTMATTER_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)

EXTERNAL_URL_RE = re.compile(r"https?://[^\s\)]+")

# Topics untuk session classification
SESSION_TOPIC_RE = re.compile(r"(minecraft|discord|vault|hermes|java|python|docker|lxc|systemd|web|server|plugin|bot|backup|spark|tabby)", re.IGNORECASE)


def extract(path: Path, all_heading_set: set | None = None) -> dict:
    """Extract nodes and edges from a single markdown file.

    Returns: {"nodes": [...], "edges": [...]}
    """
    rel_path = str(path)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {"nodes": [], "edges": []}

    text_clean = CODE_BLOCK_RE.sub("", text)
    title = _extract_title(text) or Path(path).stem
    headings = HEADING_RE.findall(text_clean)
    file_size = len(text)

    node_type = _classify_type(rel_path, title, text_clean)

    # Node: the file itself
    nodes = [{
        "id": rel_path,
        "label": title,
        "type": node_type,
        "headings": headings,
        "size": min(file_size / 100, 30),
    }]

    edges = []

    # Edges: [[wiki-links]] → EXTRACTED
    for target, alias in WIKI_LINK_RE.findall(text_clean):
        resolved = _resolve_path(rel_path, target)
        edges.append({
            "source": rel_path,
            "target": resolved,
            "relation": "wiki-link",
            "confidence": "EXTRACTED",
        })

    # Edges: heading mentions → INFERRED (only for meaningful headings >= 8 chars)
    if all_heading_set:
        meaningful = [h for h in headings if len(h) >= 8]
        for heading in meaningful:
            heading_lower = heading.lower()
            matched = False
            for other_path, other_headings in all_heading_set.items():
                if other_path == rel_path:
                    continue
                for oh in other_headings:
                    if len(oh) >= 8 and oh.lower() in heading_lower and heading_lower != oh.lower():
                        edges.append({
                            "source": rel_path,
                            "target": other_path,
                            "relation": "heading-mention",
                            "confidence": "INFERRED",
                        })
                        matched = True
                        break
                if matched:
                    break

    # Edges: session topics → concept files → INFERRED
    if node_type == "session":
        topics = set(re.findall(SESSION_TOPIC_RE, " ".join(headings) + " " + title))
        for topic in topics:
            edges.append({
                "source": rel_path,
                "target": f"concept:{topic}",
                "relation": "mentions-topic",
                "confidence": "INFERRED",
            })

    return {"nodes": nodes, "edges": edges}


def _extract_title(text: str) -> str | None:
    m = FRONTMATTER_TITLE_RE.search(text)
    return m.group(1).strip() if m else None


def _classify_type(path: str, title: str, text: str) -> str:
    parts = Path(path).parts
    if parts and parts[0] == "wiki":
        return "wiki"
    if "sessions" in parts:
        return "session"
    if "concepts" in parts:
        return "concept"
    if "discord" in parts:
        return "discord"
    if "minecraft" in parts:
        return "minecraft"
    if "linux" in parts:
        return "linux"
    return "other"


def _resolve_path(source: str, target: str) -> str:
    """Resolve [[wiki/docker/overview]] → wiki/docker/overview.md or as-is."""
    if target.endswith(".md"):
        return target
    # Try relative to wiki/ folder
    if "/" in target and not target.startswith("wiki/"):
        candidate = f"wiki/{target}.md"
        return candidate
    if not target.endswith(".md"):
        return f"{target}.md"
    return target
