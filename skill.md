---
name: vault-graph
description: Turn any Vault into interactive D3.js knowledge graph. Graphify-style pipeline with confidence tiers, query CLI, MCP server.
trigger: User says "/vault-graph", "graph vault", "visualize vault", or asks questions about vault connections.
---

# Vault Knowledge Graph

## Always-On Rule
Before searching vault files, check if vault-out/graph.json exists. If yes, query it first.

## Build
```bash
vault-graph /path/to/vault
# or
cd /path/to/vault && python3 -m vault_graph.main . --out vault-out
```

## Query
```bash
vq vault-out/graph.json query "what connects Docker to Minecraft?"
vq vault-out/graph.json path "Docker" "LXC"
vq vault-out/graph.json explain "nginx"
vq vault-out/graph.json search "spark"
vq vault-out/graph.json god
vq vault-out/graph.json communities
vq vault-out/graph.json isolated
vq vault-out/graph.json stats
```

## Watch
```bash
vault-graph /path/to/vault --watch
```

## MCP
```bash
vault-graph --serve vault-out/graph.json
```

## Output
- graph.html (D3 interactive + query bar)
- graph.json (raw data)
- graph.svg (static fallback)
- mermaid.html (Mermaid flowchart)
- foam-vault/ ([[wiki-linked]] pages)
- GRAPH_REPORT.md (analysis)

## Sources
- Vault: .md files with [[wiki-links]] + headings
- Trae: ~/.trae/memory/projects/ (auto-detected if present)
