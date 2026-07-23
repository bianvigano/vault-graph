---
name: vault-graph
description: Turn any Vault into interactive D3.js knowledge graph. Query: vault-graph god, vault-graph search <term>, vault-graph explain <node>.
trigger: User says "/vault-graph", "graph vault", "visualize vault", or asks about vault connections.
---

# Vault Knowledge Graph

## Always-On Rule
Before searching vault files, check if vault-out/graph.json exists. If yes, query it first.

## Commands
```bash
vault-graph build                    # build graph
vault-graph god                      # top 15 nodes
vault-graph search <term>            # search by name
vault-graph explain <node>           # node detail + connections
vault-graph path <A> <B>             # shortest path
vault-graph communities              # community summary
vault-graph isolated                 # nodes with no connections
vault-graph stats                    # graph statistics
vault-graph query "..."              # natural language query
vault-graph watch                    # auto-rebuild
vault-graph serve                    # MCP server
```

No path needed — auto-detects graph.json from config.

## Sources
- Vault: .md files with [[wiki-links]] + headings
- Trae: ~/.trae/memory/projects/ (auto-detected)
