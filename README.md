# vault-graph

>  Personal project by [@bianvigano](https://github.com/bianvigano). Built for Vault knowledge graph visualization. Not an official Graphify product — inspired by its architecture.

Turn any Hermes Vault into an interactive D3.js knowledge graph. Graphify-style modular pipeline.

## One-command install

```bash
bash install.sh
```

Detects Hermes + Trae, registers `/vault-graph` skill, adds `vault-graph` alias.

## Usage

```bash
vault-graph /path/to/vault
```

Output in `vault-out/`:
- `graph.html` — D3.js interactive (zoom, pan, query bar)
- `graph.json` — raw graph data
- `graph.svg` — static SVG fallback
- `mermaid.html` — Mermaid flowchart
- `foam-vault/` — Foam-compatible [[wiki-linked]] pages
- `GRAPH_REPORT.md` — analysis summary

## Commands

```bash
vault-graph /path/to/vault              # build graph
vault-graph /path/to/vault --watch      # auto-rebuild on changes
vault-graph --serve vault-out/graph.json  # MCP server
```

## Pipeline

```
detect -> extract -> build -> cluster -> analyze -> report -> export
```

## Features

- **Confidence tiers**: EXTRACTED ([[wiki-links]]) / INFERRED (heading mentions)
- **Community detection**: greedy modularity clustering
- **God nodes**: most-connected concepts
- **Query bar**: `path A to B`, `explain node`, `community N`
- **MCP server**: 5 tools via stdio
- **Security**: label sanitization, path validation
- **Cache**: SHA256-based, skip unchanged files
- **Watch**: auto-rebuild on vault file changes

## Requirements

```bash
pip install networkx matplotlib
```
