# vault-graph

> Personal project by [@bianvigano](https://github.com/bianvigano). Built for Vault knowledge graph visualization. Not an official Graphify product — inspired by its architecture.

Turn any Vault into an interactive D3.js knowledge graph. Graphify-style modular pipeline: detect → extract → build → cluster → analyze → report → export.

---

## Quick Start

```bash
git clone https://github.com/bianvigano/vault-graph
cd vault-graph
bash install.sh
```

Installs:
- CLI executable `vault-graph` (run from anywhere)
- `vq` query shortcut
- Skill + MCP server for Hermes and Trae
- Always-on section in AGENTS.md / HERMES.md

**Requirements:** `pip install networkx matplotlib` (Python 3.10+)

> **Troubleshooting:** Kalau error `No module named 'vault_graph'`, pastikan tidak ada cache atau konflik path. Coba `hash -r` lalu `vault-graph` lagi. Jangan jalankan dari folder lama `~/.hermes/scripts/`.

---

## Usage

### Build graph

```bash
vault-graph /path/to/vault
```

Output lands in `vault-out/`:

| File | Description |
|---|---|
| `graph.html` | D3.js interactive graph (zoom, pan, drag, search, query bar) |
| `graph.json` | Raw graph data for MCP/CLI queries |
| `graph.svg` | Static SVG fallback |
| `mermaid.html` | Mermaid flowchart (paste into GitHub/Notion) |
| `graph.mmd` | Raw Mermaid syntax |
| `foam-vault/` | [[wiki-linked]] markdown pages, grouped by type |
| `GRAPH_REPORT.md` | Human-readable analysis (god nodes, communities, surprises) |

### Query CLI

```bash
vq vault-out/graph.json query "what connects Docker to Minecraft?"
vq vault-out/graph.json path "Docker" "LXC"
vq vault-out/graph.json explain "nginx"
vq vault-out/graph.json search "spark"
vq vault-out/graph.json god              # top 15 most-connected nodes
vq vault-out/graph.json communities      # community summary
vq vault-out/graph.json isolated         # nodes with no connections
vq vault-out/graph.json stats            # graph statistics
```

### Watch mode

```bash
vault-graph /path/to/vault --watch
```

Polls every 30s. Rebuilds automatically when files change. Ctrl+C to stop.

### MCP server

```bash
vault-graph --serve vault-out/graph.json
```

6 MCP tools: `graph_path`, `graph_explain`, `graph_god_nodes`, `graph_search`, `graph_communities`, `graph_stats`.

Register in `.mcp.json`:

```json
{
  "mcpServers": {
    "vault-graph": {
      "command": "python3",
      "args": ["-m", "vault_graph.serve", "vault-out/graph.json"]
    }
  }
}
```

---

## Pipeline

```
detect    → scan .md files (skip hidden, git, scripts)
extract   → parse [[wiki-links]], headings, session topics
build     → NetworkX graph
cluster   → community detection (greedy modularity)
analyze   → god nodes, isolated nodes, surprises, edge stats
report    → GRAPH_REPORT.md
export    → graph.html, graph.json, graph.svg, mermaid.html, foam-vault
```

---

## Confidence Model

| Tag | Source |
|---|---|
| **EXTRACTED** | `[[wiki-link]]` in markdown |
| **INFERRED** | Heading mention matching another file's heading |
| **INFERRED** | Session topic detected from filename/headings |

In D3 graph: solid edges = EXTRACTED, dashed edges = INFERRED.

---

## Modules

| Module | Purpose |
|---|---|
| `detect.py` | Scan .md files |
| `extract.py` | Parse [[wiki-links]], headings |
| `build.py` | NetworkX graph construction |
| `cluster.py` | Community detection |
| `analyze.py` | God nodes, isolated, edge stats |
| `report.py` | GRAPH_REPORT.md |
| `export.py` | graph.html, graph.json, graph.svg |
| `query.py` | CLI query tool |
| `serve.py` | MCP stdio server |
| `watch.py` | Auto-rebuild on changes |
| `cache.py` | SHA256 cache |
| `security.py` | Label sanitization, path validation |
| `mermaid_export.py` | Mermaid flowchart |
| `wiki_export.py` | Foam vault generation |
| `install.py` | Skill installer |
| `main.py` | Pipeline orchestrator |

---

## License

MIT
