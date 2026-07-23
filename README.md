# vault-graph

> Personal project by [@bianvigano](https://github.com/bianvigano). Built for Vault knowledge graph visualization. MIT license.

Turn any Vault into an interactive D3.js knowledge graph. Auto-detects Vault `.md` files + Trae `~/.trae/memory/` data.

---

## Quick Start

```bash
git clone https://github.com/bianvigano/vault-graph
cd vault-graph
bash install.sh
vault-graph build
```

**Requirements:** `pip install networkx matplotlib` (Python 3.10+)

---

## Usage

### Build

```bash
vault-graph build                    # uses config (~/.config/vault-graph/config.json)
vault-graph build /path/to/vault     # custom path, auto-saves to config
```

Output in `<vault>/vault-out/`:

| File | Description |
|---|---|
| `graph.html` | D3.js interactive graph (zoom, pan, drag, search, query bar) |
| `graph.json` | Raw graph data |
| `graph.svg` | Static SVG fallback |
| `mermaid.html` | Mermaid flowchart |
| `GRAPH_REPORT.md` | Analysis: god nodes, communities |

### Query

```bash
vault-graph god                      # top 15 most-connected nodes
vault-graph search nginx             # search by name
vault-graph explain Docker           # node detail + connections
vault-graph path "Docker" "LXC"      # shortest path
vault-graph communities              # community summary
vault-graph isolated                 # nodes with no connections
vault-graph stats                    # graph statistics
vault-graph query "how does Docker connect to Minecraft?"
```

No path needed — auto-resolves graph.json from `~/.config/vault-graph/config.json`.

### Watch

```bash
vault-graph watch
```

Auto-rebuild every 30s when files change. Ctrl+C to stop.

### MCP server

```bash
vault-graph serve
```

6 MCP tools for Hermes/Trae integration.

---

## Config

`~/.config/vault-graph/config.json` (auto-created on first `vault-graph build`):

```json
{
  "vault": "/home/user/.hermes/vault",
  "out": "vault-out"
}
```

---

## Sources

| Source | Path | How |
|---|---|---|
| Vault | `.md` files | `[[wiki-links]]` → EXTRACTED, headings → INFERRED |
| Trae | `~/.trae/memory/` | `project_memory.md`, `session_memory_*.jsonl` |

---

## New PC

```bash
git clone https://github.com/bianvigano/vault-graph
cd vault-graph && bash install.sh
vault-graph build
```

Auto-detects Hermes + Trae, installs CLI + skills + MCP.

---

## License

MIT
