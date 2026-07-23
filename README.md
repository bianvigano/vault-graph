# vault-graph

> Personal project by [@bianvigano](https://github.com/bianvigano). Built for Vault knowledge graph visualization. Not an official Graphify product — inspired by its architecture.

Turn any Vault into an interactive D3.js knowledge graph. Graphify-style modular pipeline: detect → extract → build → cluster → analyze → report → export.

Auto-detects:
- **Vault:** `.md` files with `[[wiki-links]]` and headings
- **Trae:** `~/.trae/memory/projects/` — session summaries, project memory

---

## Quick Start

```bash
git clone https://github.com/bianvigano/vault-graph
cd vault-graph
bash install.sh
```

Installs:
- `vault-graph` → `~/.local/bin/vault-graph` (build + query + serve + watch)
- `vq` → `~/.local/bin/vq` (legacy query shortcut, still works)
- Skill + MCP server for Hermes and Trae
- Auto-adds `~/.local/bin` to PATH

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
vault-graph --query vault-out/graph.json god              # top 15 most-connected nodes
vault-graph --query vault-out/graph.json path "Docker" "LXC"
vault-graph --query vault-out/graph.json explain "nginx"
vault-graph --query vault-out/graph.json search "spark"
vault-graph --query vault-out/graph.json communities
vault-graph --query vault-out/graph.json isolated
vault-graph --query vault-out/graph.json stats
vault-graph --query vault-out/graph.json query "what connects Docker to Minecraft?"
```

Legacy: `vq vault-out/graph.json god` still works.

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

## Sources

| Source | What | How |
|---|---|---|
| **Vault** | `.md` files | `[[wiki-links]]` → EXTRACTED, heading mentions → INFERRED |
| **Trae** | `~/.trae/memory/projects/` | `project_memory.md`, `session_memory_*.jsonl`, `topics.md` |
| **Hermes** | `~/.hermes/vault/` | Same as Vault |

Trae integration: auto-detected if `~/.trae/memory/` exists. Produces nodes of type `trae-project` + `trae-session`, edges to concept nodes via topic extraction.

---

## Pipeline

```
detect    → scan .md files (skip hidden, git, scripts) + auto-detect Trae
extract   → parse [[wiki-links]], headings, session topics, Trae jsonl
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
| **EXTRACTED** | `[[wiki-link]]` in markdown, Trae session → project edges |
| **INFERRED** | Heading mention matching another file's heading |
| **INFERRED** | Session topic detected from filename/headings |
| **INFERRED** | Trae session → concept edges (topic extraction) |

In D3 graph: solid edges = EXTRACTED, dashed edges = INFERRED.

---

## Modules

| Module | Purpose |
|---|---|
| `detect.py` | Scan .md files |
| `extract.py` | Parse [[wiki-links]], headings |
| `trae.py` | Scan + parse Trae memory (~/.trae/memory/) |
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

## Install for new PC

```bash
git clone https://github.com/bianvigano/vault-graph
cd vault-graph
bash install.sh
# Build first graph:
vault-graph ~/.hermes/vault
```

`install.sh` auto-detects:
- Hermes (skill + MCP at `~/.hermes/`)
- Trae (skill + MCP at `~/.trae/`)
- Installs `vault-graph` + `vq` to `~/.local/bin/`
- Adds `~/.local/bin` to PATH if missing

---

## License

MIT
