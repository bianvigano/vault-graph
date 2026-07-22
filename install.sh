#!/bin/bash
# vault-graph install — auto-detect Hermes/Trae and register skill
# Usage: bash install.sh
set -e

VAULT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_SRC="$VAULT_DIR/vault_graph/skill.md"
ALIAS_SRC="$VAULT_DIR/vault_graph/alias.sh"

# Create skill if missing
if [ ! -f "$SKILL_SRC" ]; then
    cat > "$SKILL_SRC" << 'SKILLEOF'
---
name: vault-graph
description: Turn any Hermes Vault into interactive D3.js knowledge graph. Graphify-style pipeline with confidence tiers, query system, communities.
trigger: User says "/vault-graph", "graph vault", "visualize vault", or wants knowledge graph of vault.
---

# Vault Knowledge Graph

Turn any vault into interactive graph. Works with Hermes + Trae.

## Quick Run

```bash
cd /path/to/vault && python3 -m vault_graph.main . --out vault-out
```

Or with alias:
```bash
vault-graph /path/to/vault
```

Open `vault-out/graph.html` in browser.

## Pipeline

detect -> extract -> build -> cluster -> analyze -> report -> export

## Output

- graph.html (D3 interactive + query bar: path, explain, community)
- graph.json (raw data)
- graph.svg (static fallback)
- mermaid.html (Mermaid flowchart)
- foam-vault/ ([[wiki-linked]] pages)
- GRAPH_REPORT.md (analysis)

## Commands

```bash
# Build graph from any vault
vault-graph /path/to/vault

# Watch mode
vault-graph /path/to/vault --watch

# MCP server
vault-graph --serve vault-out/graph.json
```
SKILLEOF
fi

INSTALL_COUNT=0

# ---- Hermes ----
HERMES_SKILL="$HOME/.hermes/skills/vault/vault-graph/SKILL.md"
if [ -d "$HOME/.hermes" ]; then
    mkdir -p "$(dirname "$HERMES_SKILL")"
    cp "$SKILL_SRC" "$HERMES_SKILL"
    echo "  [✓] Hermes: $HERMES_SKILL"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))
fi

# ---- Trae ----
TRAE_SKILL="$HOME/.trae/builtin_skills/vault-graph/SKILL.md"
if [ -d "$HOME/.trae" ]; then
    mkdir -p "$(dirname "$TRAE_SKILL")"
    cp "$SKILL_SRC" "$TRAE_SKILL"
    echo "  [✓] Trae:   $TRAE_SKILL"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))
fi

# ---- Alias ----
if [ -f "$HOME/.bash_aliases" ]; then
    if ! grep -q "vault-graph" "$HOME/.bash_aliases"; then
        echo "alias vault-graph=\"cd '$VAULT_DIR' && python3 -m vault_graph.main\"" >> "$HOME/.bash_aliases"
        echo "  [✓] Alias:  vault-graph added to ~/.bash_aliases"
    else
        echo "  [✓] Alias:  vault-graph already in ~/.bash_aliases"
    fi
fi

echo ""
echo "Done! $INSTALL_COUNT assistants registered."
echo "Run: source ~/.bash_aliases   (or open new terminal)"
echo "Use:  vault-graph /path/to/vault"
