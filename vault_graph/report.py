"""Module: report — render GRAPH_REPORT.md from graph + analysis."""
from __future__ import annotations

import networkx as nx
from datetime import datetime


def render_report(G: nx.Graph, analysis: dict) -> str:
    """Generate GRAPH_REPORT.md markdown string."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Vault Knowledge Graph Report",
        f"",
        f"Generated: {now}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Nodes | {analysis['node_count']} |",
        f"| Edges | {analysis['edge_count']} |",
        f"| Density | {analysis['density']} |",
        f"| Communities | {analysis['community_count']} |",
        f"| Isolated nodes | {len(analysis['isolated_nodes'])} |",
    ]

    ec = analysis["edge_confidence"]
    if ec:
        lines.append(f"")
        lines.append(f"## Edge Confidence")
        lines.append(f"| Confidence | Count |")
        lines.append(f"|---|---|")
        for conf, count in sorted(ec.items()):
            lines.append(f"| {conf} | {count} |")

    if analysis["god_nodes"]:
        lines.append(f"")
        lines.append(f"## God Nodes (Top 10)")
        lines.append(f"| Node | Type | Degree |")
        lines.append(f"|---|---|---|")
        for gn in analysis["god_nodes"][:10]:
            lines.append(f"| {gn['label'][:50]} | {gn['type']} | {gn['degree']} |")

    if analysis["community_stats"]:
        lines.append(f"")
        lines.append(f"## Communities")
        lines.append(f"| Community | Size | Representative |")
        lines.append(f"|---|---|---|")
        for comm_id, info in sorted(analysis["community_stats"].items()):
            lines.append(f"| {comm_id} | {info['size']} | {info['representative'][:50]} |")

    if analysis["isolated_nodes"]:
        isolated_by_type = {}
        for n in analysis["isolated_nodes"]:
            t = n.get("type", "other")
            isolated_by_type.setdefault(t, []).append(n["node"])
        lines.append(f"")
        lines.append(f"## Isolated Nodes ({len(analysis['isolated_nodes'])})")
        lines.append(f"")
        lines.append(f"Files with no connections. Candidate for cross-linking.")
        lines.append(f"")
        for t, nodes in sorted(isolated_by_type.items()):
            lines.append(f"**{t}** ({len(nodes)}):")
            for node in sorted(nodes)[:10]:
                lines.append(f"- `{node}`")
            if len(nodes) > 10:
                lines.append(f"- ... and {len(nodes) - 10} more")

    if analysis["surprises"]:
        lines.append(f"")
        lines.append(f"## Surprising Connections ({len(analysis['surprises'])})")
        lines.append(f"")
        lines.append(f"Inferred relationships from heading mentions:")
        for s in analysis["surprises"][:20]:
            lines.append(f"- **{s['source']}** → **{s['target']}** ({s['relation']})")

    lines.append(f"")
    lines.append(f"## Suggested Questions")
    lines.append(f"")
    lines.append(f"Try asking about these:")
    for gn in analysis["god_nodes"][:5]:
        lines.append(f"- \"How does `{gn['label'][:30]}` connect to other concepts?\"")
    lines.append(f"- \"What are the paths between `wiki` and `minecraft`?\"")
    lines.append(f"- \"Which community has the most nodes?\"")

    return "\n".join(lines)
