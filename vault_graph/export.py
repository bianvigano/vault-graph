"""Module: export — output graph.html, graph.json, graph.svg, GRAPH_REPORT.md."""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx


def export(G: nx.Graph, analysis: dict, out_dir: Path, report_text: str):
    """Export all output artifacts."""
    out_dir.mkdir(parents=True, exist_ok=True)

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
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vault Knowledge Graph</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #1a1a2e; font-family: 'Segoe UI', system-ui, sans-serif; overflow: hidden; }}
  svg {{ width: 100vw; height: 100vh; }}
  .node circle {{ cursor: pointer; stroke: #2a2a4a; stroke-width: 2px; transition: r 0.3s; }}
  .node text {{ font-size: 10px; fill: #ccccdd; pointer-events: none; }}
  .edge {{ stroke: #3a3a5a; stroke-opacity: 0.4; }}
  .edge.inferred {{ stroke-dasharray: 5,5; }}
  #panel {{ position: fixed; top: 20px; right: 20px; background: rgba(26,26,46,0.95); border: 1px solid #3a3a5a; border-radius: 8px; padding: 12px 16px; color: #ccc; font-size: 12px; z-index: 10; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
  .legend-color {{ width: 12px; height: 12px; border-radius: 50%; }}
  #search {{ position: fixed; top: 20px; left: 20px; z-index: 10; }}
  #search input {{ background: rgba(26,26,46,0.95); border: 1px solid #3a3a5a; border-radius: 6px; color: #ccc; padding: 8px 12px; font-size: 13px; width: 240px; outline: none; }}
  #tooltip {{ position: fixed; background: rgba(26,26,46,0.95); border: 1px solid #4ecdc4; border-radius: 6px; padding: 10px 14px; color: #ccc; font-size: 11px; pointer-events: none; opacity: 0; transition: opacity 0.2s; max-width: 350px; z-index: 20; }}
  #tooltip b {{ color: #4ecdc4; }}
  .confidence-tag {{ font-size: 9px; padding: 1px 4px; border-radius: 3px; margin-left: 4px; }}
  .confidence-tag.EXTRACTED {{ color: #4ecdc4; }}
  .confidence-tag.INFERRED {{ color: #ffe66d; }}
  #query-bar {{ position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 10; display: flex; gap: 8px; }}
  #query-bar input {{ background: rgba(26,26,46,0.95); border: 1px solid #3a3a5a; border-radius: 6px; color: #ccc; padding: 8px 14px; font-size: 13px; width: 300px; outline: none; }}
  #query-bar button {{ background: #4ecdc4; border: none; border-radius: 6px; color: #1a1a2e; padding: 8px 14px; font-size: 13px; cursor: pointer; font-weight: 600; }}
  #query-bar button:hover {{ background: #45b7aa; }}
</style>
</head>
<body>
<div id="search"><input type="text" placeholder="Search node..." id="search-input"></div>
<div id="panel">
  <div class="legend-item"><span class="legend-color" style="background:#4ecdc4"></span> Wiki</div>
  <div class="legend-item"><span class="legend-color" style="background:#ff6b6b"></span> Session</div>
  <div class="legend-item"><span class="legend-color" style="background:#ffe66d"></span> Concept</div>
  <div class="legend-item"><span class="legend-color" style="background:#a29bfe"></span> Discord</div>
  <div class="legend-item"><span class="legend-color" style="background:#fd79a8"></span> Minecraft</div>
  <div class="legend-item"><span class="legend-color" style="background:#55efc4"></span> Other</div>
  <div style="margin-top:8px;font-size:10px;opacity:0.6">
    <span id="stats">Loading...</span><br>
    <span style="font-size:9px">— solid edge: EXTRACTED<br>— dashed edge: INFERRED</span>
  </div>
</div>
<div id="tooltip"></div>
<div id="query-bar">
  <input type="text" placeholder="Query: 'path A to B' or 'explain node' or 'community N'" id="query-input">
  <button onclick="runQuery()">Query</button>
</div>
<svg id="graph"></svg>
<script>
  const data = {{
    nodes: {nodes_json},
    edges: {edges_json}
  }};

  document.getElementById('stats').textContent = `${{data.nodes.length}} nodes · ${{data.edges.length}} edges`;

  const colorByType = {{
    wiki: '#4ecdc4', session: '#ff6b6b', concept: '#ffe66d',
    discord: '#a29bfe', minecraft: '#fd79a8', linux: '#00b894',
    other: '#55efc4'
  }};

  const svg = d3.select('#graph');
  const width = window.innerWidth, height = window.innerHeight;

  const container = svg.append('g');
  const zoom = d3.zoom().scaleExtent([0.1, 5]).on('zoom', e => container.attr('transform', e.transform));
  svg.call(zoom);

  const simulation = d3.forceSimulation(data.nodes)
    .force('link', d3.forceLink(data.edges).id(d => d.id).distance(130))
    .force('charge', d3.forceManyBody().strength(-500))
    .force('center', d3.forceCenter(width/2, height/2))
    .force('collision', d3.forceCollide().radius(35));

  // Edges
  const edge = container.append('g').selectAll('line').data(data.edges)
    .join('line')
    .attr('class', d => 'edge ' + ((d.confidence === 'INFERRED') ? 'inferred' : ''))
    .attr('stroke-width', d => d.confidence === 'INFERRED' ? 0.8 : 1.2);

  // Nodes
  const node = container.append('g').selectAll('g').data(data.nodes)
    .join('g').attr('class', 'node')
    .call(d3.drag()
      .on('start', (e, d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
      .on('drag', (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
      .on('end', (e, d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}));

  node.append('circle')
    .attr('r', d => Math.max(d.size || 5, 5))
    .attr('fill', d => colorByType[d.type] || '#55efc4');

  node.append('text')
    .text(d => (d.label || d.id).substring(0, 28))
    .attr('dy', d => -Math.max(d.size || 5, 5) - 4)
    .attr('text-anchor', 'middle')
    .style('font-size', '9px');

  // Tooltip
  const tooltip = d3.select('#tooltip');
  node.on('mouseenter', (e, d) => {{
    const connected = data.edges.filter(ed => ed.source === d.id || ed.target === d.id);
    tooltip.style('opacity', 1)
      .style('left', (e.pageX + 14) + 'px')
      .style('top', (e.pageY - 14) + 'px')
      .html(`<b>${{esc(d.label || d.id)}}</b><br>
             <span style="opacity:0.6">${{d.type}}{{d.community !== undefined ? ' · community ' + d.community : ''}}</span><br>
             <span style="opacity:0.5;font-size:10px">${{d.id.substring(0, 70)}}</span><br>
             <span style="font-size:10px">${{connected.length}} connections</span>`);
  }}).on('mouseleave', () => tooltip.style('opacity', 0));

  // Search
  d3.select('#search-input').on('input', () => {{
    const q = d3.select('#search-input').property('value').toLowerCase();
    node.select('circle')
      .attr('fill', d => {{
        const match = (d.label || '').toLowerCase().includes(q) || (d.id || '').toLowerCase().includes(q);
        return match ? '#fff' : (colorByType[d.type] || '#55efc4');
      }})
      .attr('r', d => {{
        const match = (d.label || '').toLowerCase().includes(q) || (d.id || '').toLowerCase().includes(q);
        return match ? Math.max((d.size || 5) * 2.2, 14) : Math.max(d.size || 5, 5);
      }});
  }});

  // Query system
  window.runQuery = function() {{
    const q = document.getElementById('query-input').value.trim().toLowerCase();

    if (q.startsWith('path ')) {{
      const parts = q.replace('path ', '').split(' to ');
      if (parts.length === 2) findPath(parts[0].trim(), parts[1].trim());
      else alert("Format: path A to B");
    }} else if (q.startsWith('explain ')) {{
      explainNode(q.replace('explain ', '').trim());
    }} else if (q.startsWith('community ')) {{
      highlightCommunity(q.replace('community ', '').trim());
    }} else if (q) {{
      d3.select('#search-input').property('value', q);
      d3.select('#search-input').dispatch('input');
    }}
  }};

  function findPath(a, b) {{
    const nodeMap = {{}}; data.nodes.forEach(n => nodeMap[n.id] = n);
    const adj = {{}};
    data.edges.forEach(e => {{
      if (!adj[e.source]) adj[e.source] = [];
      if (!adj[e.target]) adj[e.target] = [];
      adj[e.source].push(e.target);
      adj[e.target].push(e.source);
    }});
    const startId = findMatchingNode(a);
    const endId = findMatchingNode(b);
    if (!startId || !endId) {{ alert('Node not found: ' + a + ' / ' + b); return; }}
    const visited = new Set();
    const queue = [[startId]];
    while (queue.length) {{
      const path = queue.shift();
      const last = path[path.length - 1];
      if (last === endId) {{
        highlightPath(path);
        alert('Path (' + (path.length - 1) + ' hops): ' + path.map(id => nodeMap[id]?.label || id).join(' → '));
        return;
      }}
      if (visited.has(last)) continue;
      visited.add(last);
      for (const neighbor of (adj[last] || [])) {{
        if (!visited.has(neighbor)) queue.push([...path, neighbor]);
      }}
    }}
    alert('No path found between ' + a + ' and ' + b);
  }}

  function explainNode(query) {{
    const id = findMatchingNode(query);
    if (!id) {{ alert('Node not found: ' + query); return; }}
    const node = data.nodes.find(n => n.id === id);
    const edges = data.edges.filter(e => e.source === id || e.target === id);
    const connected = edges.map(e => e.source === id ? e.target : e.source);
    const byType = {{}};
    connected.forEach(cid => {{
      const cn = data.nodes.find(n => n.id === cid);
      const t = cn?.type || 'other';
      byType[t] = (byType[t] || 0) + 1;
    }});
    let msg = `Node: ${{node?.label || id}}\\nType: ${{node?.type}}\\nConnections: ${{edges.length}}\\n`;
    for (const [t, c] of Object.entries(byType)) msg += `  ${{t}}: ${{c}}\\n`;
    msg += '\\nEdges:\\n';
    edges.slice(0, 15).forEach(e => {{
      const other = e.source === id ? e.target : e.source;
      const on = data.nodes.find(n => n.id === other);
      msg += `  → ${{on?.label || other}} [${{e.relation}}] [${{e.confidence}}]\\n`;
    }});
    alert(msg);
  }}

  function highlightCommunity(commId) {{
    node.select('circle').attr('fill', d => {{
      if (String(d.community) === commId) return '#fff';
      return 'rgba(30,30,50,0.3)';
    }}).attr('r', d => {{
      if (String(d.community) === commId) return Math.max(d.size || 5, 5) * 2.5;
      return Math.max(d.size || 5, 5) * 0.6;
    }});
  }}

  function highlightPath(path) {{
    const pathSet = new Set(path);
    node.select('circle').attr('fill', d => pathSet.has(d.id) ? '#ffe66d' : 'rgba(30,30,50,0.3)');
    edge.attr('stroke', d => pathSet.has(d.source) && pathSet.has(d.target) ? '#ffe66d' : '#3a3a5a')
        .attr('stroke-width', d => pathSet.has(d.source) && pathSet.has(d.target) ? 3 : 0.5);
  }}

  function findMatchingNode(q) {{
    const exact = data.nodes.find(n => n.id === q || n.label === q);
    if (exact) return exact.id;
    const partial = data.nodes.find(n => (n.id || '').toLowerCase().includes(q) || (n.label || '').toLowerCase().includes(q));
    return partial?.id;
  }}

  function esc(s) {{ return (s || '').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}

  simulation.on('tick', () => {{
    edge.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
  }});
</script>
</body>
</html>"""
