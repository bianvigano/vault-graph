#!/bin/bash
# vault-graph install — auto-detect assistants, register skill, inject always-on
# Usage: bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_COUNT=0

echo "vault-graph install"
echo "==================="

# ---- 1. CLI query alias ----
CLI_QUERY="python3 -m vault_graph.query"
ALIAS_LINE="alias vq=\"cd '$SCRIPT_DIR' && $CLI_QUERY\""
if [ -f "$HOME/.bash_aliases" ]; then
    if ! grep -q "alias vq=" "$HOME/.bash_aliases"; then
        echo "$ALIAS_LINE" >> "$HOME/.bash_aliases"
        echo "  [✓] CLI:  vq alias added"
    else
        echo "  [✓] CLI:  vq already aliased"
    fi
fi

# ---- 2. Skill for assistants ----
SKILL_MD="$SCRIPT_DIR/skill.md"
if [ ! -f "$SKILL_MD" ]; then
    cat > "$SKILL_MD" << 'SKILLEOF'
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
SKILLEOF
fi

# ---- Hermes ----
if [ -d "$HOME/.hermes" ]; then
    DST="$HOME/.hermes/skills/vault/vault-graph/SKILL.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    echo "  [✓] Hermes: $DST"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))
fi

# ---- Trae ----
if [ -d "$HOME/.trae" ]; then
    DST="$HOME/.trae/builtin_skills/vault-graph/SKILL.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    echo "  [✓] Trae:   $DST"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))
fi

# ---- 3. Always-On: inject into AGENTS.md / HERMES.md ----
ALWAYS_ON="\n## Vault Knowledge Graph\nVault graph available. Check vault-out/graph.json before searching.\nQuery CLI: vq /path/to/graph.json query \"question\"\nBuild: vault-graph /path/to/vault\n"

for MD in "$HOME/AGENTS.md" "$HOME/HERMES.md" "."/AGENTS.md "."/HERMES.md; do
    [ -f "$MD" ] || continue
    if ! grep -q "Vault Knowledge Graph" "$MD" 2>/dev/null; then
        echo -e "$ALWAYS_ON" >> "$MD"
        echo "  [✓] Always-on: $MD"
    fi
done

# ---- Done ----
echo ""
echo "Done! $INSTALL_COUNT assistants registered."
echo ""
echo "--- Quick Start ---"
echo "  Build:  vault-graph /path/to/vault"
echo "  Query:  vq vault-out/graph.json query \"something\""
echo "  Watch:  vault-graph /path/to/vault --watch"
echo "  MCP:    python -m vault_graph.serve vault-out/graph.json"
echo ""
echo "Run 'source ~/.bash_aliases' or open new terminal."
