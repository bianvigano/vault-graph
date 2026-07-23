# vault-graph

> Personal project by [@bianvigano](https://github.com/bianvigano). MIT license.

Turn Vault `.md` files + Trae memory into interactive D3.js knowledge graph.

---

## Install

### Linux / macOS

```bash
git clone https://github.com/bianvigano/vault-graph
cd vault-graph
bash install.sh
vault-graph build
```

### Windows

```cmd
git clone https://github.com/bianvigano/vault-graph
cd vault-graph
install.bat
vault-graph build
```

Run from anywhere. No `cd` needed after install.

**Requirements:** Python 3.10+, `pip install networkx matplotlib`

---

## Usage

```bash
vault-graph build                    # build knowledge graph
vault-graph god                      # top 15 most-connected nodes
vault-graph search <term>            # search by name
vault-graph explain <node>           # detail + connections
vault-graph path <A> <B>             # shortest path
vault-graph communities              # community summary
vault-graph isolated                 # nodes with no connections
vault-graph stats                    # graph statistics
vault-graph query "question"         # natural language
vault-graph watch                    # auto-rebuild on changes
vault-graph serve                    # MCP server (Hermes/Trae)
```

No path arguments — auto-detects from `~/.config/vault-graph/config.json`.

---

## Config

`~/.config/vault-graph/config.json` (auto-created):

```json
{
  "vault": "/home/user/.hermes/vault",
  "out": "vault-out"
}
```

On Windows: `%APPDATA%/vault-graph/config.json`

---

## Sources

| Source | What |
|---|---|
| Vault `.md` | `[[wiki-links]]` → EXTRACTED, headings → INFERRED |
| Trae `~/.trae/memory/` | `project_memory.md`, `session_memory_*.jsonl` |

---

## Output

| File | Description |
|---|---|
| `graph.html` | D3.js interactive (zoom, pan, drag, search, query bar) |
| `graph.json` | Raw data for MCP/CLI |
| `graph.svg` | Static SVG |
| `mermaid.html` | Flowchart |
| `GRAPH_REPORT.md` | Analysis |

---

## License

MIT
