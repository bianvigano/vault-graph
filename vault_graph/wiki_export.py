"""Module: wiki_export — generate Obsidian/Foam-compatible vault with auto [[wiki-links]]."""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx


def export_wiki(G: nx.Graph, out_dir: Path, vault_root: Path):
    """Generate a Foam/Obsidian vault from graph nodes and edges.
    
    Creates markdown files for each node with [[wiki-links]] to connected nodes.
    Grouped by type into folders.
    """
    wiki_dir = out_dir / "foam-vault"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    
    # Group nodes by type
    by_type = {}
    for n in G.nodes():
        t = G.nodes[n].get("type", "other")
        by_type.setdefault(t, []).append(n)
    
    node_count = 0
    
    for node_type, nodes in by_type.items():
        type_dir = wiki_dir / node_type
        type_dir.mkdir(exist_ok=True)
        
        for node_id in nodes:
            label = G.nodes[node_id].get("label", node_id)
            safe_name = _safe_filename(label) or _safe_filename(node_id)
            file_path = type_dir / f"{safe_name}.md"
            
            # Build content
            lines = [f"# {label}", "", f"Type: {node_type}", f"ID: `{node_id}`", ""]
            
            # Connected nodes
            connected = list(G.neighbors(node_id))
            if connected:
                lines.append("## Connections")
                lines.append("")
                # Group by confidence
                extracted = []
                inferred = []
                for nb in connected:
                    edge = G[node_id][nb]
                    nb_label = G.nodes[nb].get("label", nb)
                    nb_type = G.nodes[nb].get("type", "other")
                    nb_safe = _safe_filename(nb_label) or _safe_filename(nb)
                    link = f"- [[../{nb_type}/{nb_safe}|{nb_label}]] ({edge.get('relation', '')}) [{edge.get('confidence', '')}]"
                    if edge.get("confidence") == "EXTRACTED":
                        extracted.append(link)
                    else:
                        inferred.append(link)
                
                if extracted:
                    lines.append("### EXTRACTED")
                    lines.extend(extracted)
                    lines.append("")
                if inferred:
                    lines.append("### INFERRED")
                    lines.extend(inferred)
                    lines.append("")
            else:
                lines.append("## Isolated")
                lines.append("No connections to other vault documents.")
                lines.append("")
            
            file_path.write_text("\n".join(lines))
            node_count += 1
    
    # Write index
    index_lines = ["# Vault Graph Index", "", f"Generated from {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.", ""]
    for t, nodes in sorted(by_type.items()):
        index_lines.append(f"## {t.title()} ({len(nodes)})")
        for n in sorted(nodes)[:20]:
            label = G.nodes[n].get("label", n)
            safe = _safe_filename(label) or _safe_filename(n)
            index_lines.append(f"- [[{t}/{safe}|{label}]]")
        if len(nodes) > 20:
            index_lines.append(f"- ... and {len(nodes) - 20} more")
        index_lines.append("")
    
    (wiki_dir / "index.md").write_text("\n".join(index_lines))
    
    print(f"  foam-vault: {node_count} pages in {wiki_dir}")
    return wiki_dir


def _safe_filename(name: str) -> str:
    """Convert label to safe filename."""
    import re
    name = name.replace("/", "-").replace("\\", "-").replace(":", "-")
    name = re.sub(r"[^\w\-\. ]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    name = name[:64].strip("-")
    return name or "untitled"
