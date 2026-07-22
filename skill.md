---
name: vault-graph
description: Turn any Hermes Vault into interactive D3.js knowledge graph. Graphify-style pipeline with confidence tiers, query CLI, MCP server, always-on.
trigger: User says "/vault-graph", "graph vault", "visualize vault", "vq query", or asks questions about vault contents.
---

# Vault Knowledge Graph

## Always-On Rule

Before searching or reading vault files directly, check if /path/to/vault/vault-out/graph.json exists. If yes, query it first:
- `python -m vault_graph.query graph.json query "the question"`
- `python -m vault_graph.query graph.json path A B`
- `python -m vault_graph.query graph.json explain NODE`

## Build Graph

```bash
cd /path/to/vault && python3 -m vault_graph.main . --out vault-out
```

Or with alias:
```bash
vault-graph /path/to/vault
```

## Query CLI

```bash
vq /path/to/graph.json query "what connects Docker to Minecraft?"
vq /path/to/graph.json path "Docker" "LXC"
vq /path/to/graph.json explain "nginx"
vq /path/to/graph.json search "spark"
vq /path/to/graph.json god
vq /path/to/graph.json communities
vq /path/to/graph.json isolated
vq /path/to/graph.json stats
```

## MCP Server

```bash
python -m vault_graph.serve graph.json
```

## Output

- graph.html (D3 interactive + query bar)
- graph.json (raw data)
- mermaid.html (Mermaid flowchart)
- foam-vault/ ([[wiki-linked]] pages)
- GRAPH_REPORT.md (analysis)
