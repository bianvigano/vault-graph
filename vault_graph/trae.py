"""Module: trae — scan and parse Trae AI IDE memory data.

Trae stores session summaries + project memory in ~/.trae/memory/:
  projects/<encoded-path>/
    project_memory.md          — constraints, conventions, features, lessons
    <YYYYMMDD>/
      session_memory_<id>.jsonl — one JSON per line: intent, actions, outcome, learned
      topics.md                 — [session_id: id | time] summary

This module converts Trae data into vault-graph extraction dicts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

TRAE_MEMORY_DIR = Path.home() / ".trae" / "memory"

SESSION_TOPIC_RE = re.compile(
    r"(minecraft|discord|vault|hermes|java|python|docker|lxc|systemd|"
    r"web|server|plugin|bot|backup|spark|tabby|node|js|maven|velocity|"
    r"paper|fabric|mod|proxy|nginx|sqlite|postgres|api|cli|yaml|toml)",
    re.IGNORECASE,
)


def trae_available() -> bool:
    """Check if Trae memory directory exists."""
    return (TRAE_MEMORY_DIR / "projects").is_dir()


def collect_trae_extractions() -> list[dict]:
    """Collect nodes + edges from Trae memory.

    Returns list of {"nodes": [...], "edges": [...]} dicts.
    """
    extractions: list[dict] = []

    projects_dir = TRAE_MEMORY_DIR / "projects"
    if not projects_dir.is_dir():
        return extractions

    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        project_name = _decode_project_name(project_dir.name)
        extractions.append(_process_project(project_dir, project_name))

    # User profile
    profile_path = TRAE_MEMORY_DIR / "user_profile.md"
    if profile_path.exists():
        extractions.append(_process_user_profile(profile_path))

    return extractions


def _process_project(project_dir: Path, name: str) -> dict:
    """Extract nodes/edges for one Trae project."""
    safe_name = name.replace("/", "-").replace(" ", "-").lower()
    node_id = f"trae:project:{safe_name}"

    nodes = [
        {
            "id": node_id,
            "label": name,
            "type": "trae-project",
            "headings": [],
            "size": 8,
        }
    ]
    edges: list[dict] = []

    # project_memory.md
    pm_path = project_dir / "project_memory.md"
    if pm_path.exists():
        pm_text = pm_path.read_text(encoding="utf-8")
        headings = _extract_headings(pm_text)
        nodes[0]["headings"] = headings
        nodes[0]["size"] = min(len(pm_text) / 100, 30)

        # Link to concepts from project memory topics
        topics = set(re.findall(SESSION_TOPIC_RE, pm_text))
        for topic in topics:
            edges.append(
                {
                    "source": node_id,
                    "target": f"concept:{topic}",
                    "relation": "trae-knows-about",
                    "confidence": "INFERRED",
                }
            )

    # Session files
    session_count = 0
    for date_dir in sorted(project_dir.iterdir()):
        if not date_dir.is_dir():
            continue

        date_str = date_dir.name  # YYYYMMDD
        jsonl_files = sorted(date_dir.glob("session_memory_*.jsonl"))

        for jf in jsonl_files:
            sid = jf.stem.replace("session_memory_", "")
            session_id = f"trae:session:{safe_name}/{date_str}/{sid}"

            sessions_data = _parse_jsonl(jf)
            if not sessions_data:
                continue

            # Session node
            session_labels = [s.get("intent", "")[:80] for s in sessions_data]
            primary_intent = session_labels[0] if session_labels else "unknown"

            nodes.append(
                {
                    "id": session_id,
                    "label": primary_intent[:70],
                    "type": "trae-session",
                    "headings": [],
                    "size": min(len(sessions_data) * 2, 25),
                }
            )

            # Project → session edge
            edges.append(
                {
                    "source": node_id,
                    "target": session_id,
                    "relation": "has-session",
                    "confidence": "EXTRACTED",
                }
            )

            # Session → topics from all messages
            all_text = " ".join(
                s.get("intent", "")
                + " "
                + s.get("outcome", "")
                + " "
                + " ".join(s.get("learned", []))
                for s in sessions_data
            )
            topics = set(re.findall(SESSION_TOPIC_RE, all_text))
            for topic in topics:
                edges.append(
                    {
                        "source": session_id,
                        "target": f"concept:{topic}",
                        "relation": "mentions-topic",
                        "confidence": "INFERRED",
                    }
                )

            session_count += 1

    nodes[0]["size"] = max(nodes[0]["size"], session_count)
    return {"nodes": nodes, "edges": edges}


def _process_user_profile(profile_path: Path) -> dict:
    """Extract user profile as a graph node."""
    text = profile_path.read_text(encoding="utf-8")
    headings = _extract_headings(text)
    topics = set(re.findall(SESSION_TOPIC_RE, text))

    node = {
        "id": "trae:user-profile",
        "label": "User Profile",
        "type": "trae-profile",
        "headings": headings,
        "size": min(len(text) / 100, 15),
    }

    edges = []
    for topic in topics:
        edges.append(
            {
                "source": "trae:user-profile",
                "target": f"concept:{topic}",
                "relation": "user-interested-in",
                "confidence": "INFERRED",
            }
        )

    return {"nodes": [node], "edges": edges}


def _parse_jsonl(path: Path) -> list[dict]:
    """Parse a JSONL session memory file. Returns list of message dicts."""
    results: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                results.append(obj)
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return results


def _extract_headings(text: str) -> list[str]:
    """Extract ## headings from markdown text."""
    heading_re = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)
    return heading_re.findall(text)


def _decode_project_name(dirname: str) -> str:
    """Decode Trae's URL-encoded project directory names.

    Pattern: -home-the-meh-Desktop-Projak-plugin-MC-servermanager
    → ~/Desktop/Projak-plugin-MC/servermanager
    """
    # Replace - with / for directory separators
    # Trae uses - as path separator, prefix encodes the root
    parts = dirname.lstrip("-").split("-")
    # Reconstruct: first parts form the path
    if parts and parts[0] == "home":
        # /home/<user>/... pattern
        path_parts = ["/" + parts[0]]
        i = 1
        while i < len(parts):
            path_parts.append(parts[i])
            i += 1
        return "/".join(path_parts)
    return dirname
