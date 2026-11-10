"""Module: export — output graph.html, graph.json, graph.svg, GRAPH_REPORT.md."""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx


def export(G: nx.Graph, analysis: dict, out_dir: Path, report_text: str):
    """Export all output artifacts."""
    out_dir.mkdir(parents=True, exist_ok=True)

    from vault_graph.storage import save_graph
    save_graph(G, out_dir / "graph.db")
    _export_json(G, out_dir)
    _export_html(G, out_dir)
    _export_svg(G, out_dir)
    _export_report(report_text, out_dir)

    print(f"\nOutput: {out_dir}/")
    for f in sorted(out_dir.glob("*")):
        size = len(f.read_bytes()) if f.is_file() else 0
        print(f"  {f.name:25s} {size:>8,} bytes")


def _export_json(G: nx.Graph, out_dir: Path):
    graph_data = {
        "nodes": [
            {"id": n, **{k: v for k, v in G.nodes[n].items()}}
            for n in G.nodes()
        ],
        "edges": [
            {"source": u, "target": v, **{k: v for k, v in G[u][v].items()}}
            for u, v in G.edges()
        ],
    }
    (out_dir / "graph.json").write_text(json.dumps(graph_data, indent=2, ensure_ascii=False))


def _export_html(G: nx.Graph, out_dir: Path):
    nodes_json = json.dumps([
        {"id": n, **{k: v for k, v in G.nodes[n].items() if k not in ("headings",)}}
        for n in G.nodes()
    ])
    edges_json = json.dumps([
        {"source": u, "target": v, **{k: v for k, v in G[u][v].items()}}
        for u, v in G.edges()
    ])

    html = _build_d3_html(nodes_json, edges_json)
    (out_dir / "graph.html").write_text(html)


def _export_svg(G: nx.Graph, out_dir: Path):
    """Generate static SVG (no D3). Fallback when no browser."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(16, 10), facecolor="#1a1a2e")
        ax.set_facecolor("#1a1a2e")

        pos = nx.spring_layout(G, seed=42)
        type_colors = {
            "wiki": "#4ecdc4", "session": "#ff6b6b", "concept": "#ffe66d",
            "discord": "#a29bfe", "minecraft": "#fd79a8", "linux": "#00b894",
            "trae-project": "#e17055", "trae-session": "#fab1a0",
            "trae-profile": "#d63031",
            "other": "#55efc4",
        }

        node_colors = [type_colors.get(G.nodes[n].get("type", "other"), "#55efc4") for n in G.nodes()]

        nx.draw_networkx_edges(G, pos, alpha=0.15, edge_color="#3a3a5a", ax=ax)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=60, alpha=0.9, ax=ax)
        labels = {}
        for n in G.nodes():
            raw = G.nodes[n].get("label", n)[:20]
            labels[n] = raw.encode("ascii", errors="ignore").decode() or n[:20]
        nx.draw_networkx_labels(G, pos, labels,
                                font_size=5, font_color="#ccccdd", ax=ax)

        ax.set_title(f"Vault Knowledge Graph ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)",
                     color="#ccccdd", fontsize=10)
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(out_dir / "graph.svg", dpi=150, facecolor="#1a1a2e", edgecolor="none")
        plt.close(fig)
    except ImportError:
        print("  (matplotlib not installed — skipping graph.svg)")
    except Exception as e:
        print(f"  (graph.svg failed: {e})")


def _export_report(text: str, out_dir: Path):
    (out_dir / "GRAPH_REPORT.md").write_text(text)


def _build_d3_html(nodes_json: str, edges_json: str) -> str:
    template = Path(__file__).with_name("graph.html").read_text(encoding="utf-8")
    return template
# Data stays in graph.json so the HTML remains small and independently editable.


