"""Module: mermaid_export — generate Mermaid diagram from vault graph."""
from __future__ import annotations

import networkx as nx
from pathlib import Path
from collections import Counter


def export_mermaid(G: nx.Graph, out_dir: Path, top_n: int = 50):
    """Generate Mermaid flowchart HTML + .mmd file from graph.

    Renders the top N most-connected nodes with their edges.
    Output: mermaid.html (interactive) + graph.mmd (raw Mermaid syntax)
    """
    # Select top N nodes by degree for readability
    degree = sorted(G.degree(), key=lambda x: x[1], reverse=True)
    top_nodes = set(n for n, _ in degree[:top_n])

    # Filter edges — only include if both ends in top nodes
    edges = [
        (u, v, d) for u, v, d in G.edges(data=True)
        if u in top_nodes and v in top_nodes
    ]

    # Limit total edges if too many
    if len(edges) > 200:
        # Keep EXTRACTED edges first, then fill with INFERRED
        extracted = [e for e in edges if e[2].get("confidence") == "EXTRACTED"]
        inferred = [e for e in edges if e[2].get("confidence") != "EXTRACTED"]
        edges = extracted + inferred[:200 - len(extracted)]

    # Generate Mermaid syntax
    mermaid_lines = ["graph TD"]
    node_ids = {}  # label -> safe_id mapping
    id_counter = 0

    for u, v, d in edges:
        # Create safe IDs
        u_label = _shorten_path(G.nodes[u].get("label", u))[:30]
        v_label = _shorten_path(G.nodes[v].get("label", v))[:30]
        
        if u_label not in node_ids:
            node_ids[u_label] = f"n{id_counter}"
            id_counter += 1
        if v_label not in node_ids:
            node_ids[v_label] = f"n{id_counter}"
            id_counter += 1

        uid = node_ids[u_label]
        vid = node_ids[v_label]
        
        # Edge styling
        if d.get("confidence") == "EXTRACTED":
            mermaid_lines.append(f"    {uid}[{_escape_mermaid(u_label)}] --> {vid}[{_escape_mermaid(v_label)}]")
        else:
            mermaid_lines.append(f"    {uid}[{_escape_mermaid(u_label)}] -.-> {vid}[{_escape_mermaid(v_label)}]")
            # Add a text node for inferred label
            # No explicit label on dashed edge — visual distinction is enough

    # Add styling for node types
    mermaid_lines.append("")
    mermaid_lines.append("    %% Node type coloring")
    mermaid_lines.append("    classDef wiki fill:#4ecdc4,stroke:#3a9d94,color:#1a1a2e")
    mermaid_lines.append("    classDef session fill:#ff6b6b,stroke:#cc5555,color:#1a1a2e")
    mermaid_lines.append("    classDef concept fill:#ffe66d,stroke:#ccb855,color:#1a1a2e")
    mermaid_lines.append("    classDef discord fill:#a29bfe,stroke:#8278cc,color:#1a1a2e")
    mermaid_lines.append("    classDef minecraft fill:#fd79a8,stroke:#cc6086,color:#1a1a2e")
    mermaid_lines.append("    classDef other fill:#55efc4,stroke:#44bf9d,color:#1a1a2e")
    mermaid_lines.append("")

    # Assign classes
    for label, nid in node_ids.items():
        # Find node type
        node_type = "other"
        for n in G.nodes():
            if G.nodes[n].get("label", n)[:40] == label:
                node_type = G.nodes[n].get("type", "other")
                break
        if node_type in ("wiki", "session", "concept", "discord", "minecraft", "other"):
            mermaid_lines.append(f"    class {nid} {node_type}")

    mermaid_text = "\n".join(mermaid_lines)

    # Write raw .mmd file
    mmd_path = out_dir / "graph.mmd"
    mmd_path.write_text(mermaid_text)
    print(f"  graph.mmd: {len(edges)} edges, {len(node_ids)} nodes")

    # Write interactive HTML
    html = _build_mermaid_html(mermaid_text, G.number_of_nodes(), G.number_of_edges(), top_n)
    html_path = out_dir / "mermaid.html"
    html_path.write_text(html)
    print(f"  mermaid.html: rendered")


def _escape_mermaid(text: str) -> str:
    """Escape Mermaid special chars."""
    text = text.replace('"', "'").replace("[", "(").replace("]", ")")
    text = text.replace("/", "-").replace(".", "-").replace(":", "-")
    text = text[:60]
    return text.strip()


def _shorten_path(text: str) -> str:
    """Shorten file paths to meaningful names only."""
    # If it looks like a file path, extract just the filename
    if "/" in text or ".md" in text:
        parts = text.replace(".md", "").replace("\\", "/").split("/")
        # Take last 1-2 meaningful parts
        meaningful = [p for p in parts if p and not p.startswith(".") and len(p) > 2]
        return "-".join(meaningful[-2:]) if len(meaningful) > 2 else parts[-1]
    return text


def _build_mermaid_html(mermaid_text: str, total_nodes: int, total_edges: int, top_n: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vault Graph - Mermaid Diagram</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #1a1a2e; font-family: 'Segoe UI', system-ui, sans-serif; padding: 20px; min-height: 100vh; }}
  h1 {{ color: #ccccdd; font-size: 18px; margin-bottom: 8px; }}
  .subtitle {{ color: #888; font-size: 12px; margin-bottom: 24px; }}
  .subtitle span {{ color: #4ecdc4; }}
  .mermaid {{ background: #111122; border: 1px solid #2a2a4a; border-radius: 10px; padding: 30px; overflow: auto; }}
  .legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; color: #ccc; font-size: 11px; }}
  .legend-color {{ width: 10px; height: 10px; border-radius: 2px; }}
  .legend-dashed {{ border: none; border-top: 1.5px dashed #ffe66d; width: 20px; height: 0; }}
</style>
</head>
<body>
<h1>Vault Knowledge Graph — Mermaid Diagram</h1>
<div class="subtitle">
  <span>{total_nodes}</span> total nodes · showing top <span>{top_n}</span> by degree · <span style="color:#4ecdc4">solid</span> = EXTRACTED · <span style="color:#ffe66d">dashed</span> = INFERRED
</div>
<div class="legend">
  <div class="legend-item"><span class="legend-color" style="background:#4ecdc4"></span> Wiki</div>
  <div class="legend-item"><span class="legend-color" style="background:#ff6b6b"></span> Session</div>
  <div class="legend-item"><span class="legend-color" style="background:#ffe66d"></span> Concept</div>
  <div class="legend-item"><span class="legend-color" style="background:#a29bfe"></span> Discord</div>
  <div class="legend-item"><span class="legend-color" style="background:#fd79a8"></span> Minecraft</div>
  <div class="legend-item"><span class="legend-color" style="background:#55efc4"></span> Other</div>
</div>
<div class="mermaid">
{mermaid_text}
</div>
<script>
mermaid.initialize({{
  startOnLoad: true,
  theme: 'dark',
  themeVariables: {{
    primaryColor: '#1a1a2e',
    primaryTextColor: '#ccccdd',
    primaryBorderColor: '#2a2a4a',
    lineColor: '#3a3a5a',
    secondaryColor: '#111122',
    tertiaryColor: '#111122',
  }},
  flowchart: {{
    useMaxWidth: false,
    htmlLabels: true,
    curve: 'basis',
    defaultRenderer: 'dagre-d3',
    nodeSpacing: 80,
    rankSpacing: 100,
  }},
}});
</script>
</body>
</html>"""
