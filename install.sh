#!/bin/bash
# vault-graph install — CLI wrapper, skills, MCP. No pip needed.
# Usage: bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GRAPH_JSON_DEFAULT="$HOME/.hermes/vault/vault-out/graph.json"
INSTALL_COUNT=0

echo "vault-graph install"
echo "==================="
echo "  repo: $SCRIPT_DIR"
echo ""

# ---- 1. CLI wrapper (~/.local/bin) ----
echo "--- CLI ---"
mkdir -p "$HOME/.local/bin"

cat > "$HOME/.local/bin/vault-graph" << VGEOF
#!/bin/bash
export PYTHONPATH="$SCRIPT_DIR:\${PYTHONPATH}"
exec python3 -m vault_graph.main "\$@"
VGEOF
chmod +x "$HOME/.local/bin/vault-graph"
echo "  [✓] vault-graph → ~/.local/bin/vault-graph"

# Pastikan ~/.local/bin di PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    if [ -f "$HOME/.bashrc" ]; then
        if ! grep -q '.local/bin' "$HOME/.bashrc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo "  [✓] PATH        → ~/.local/bin added to ~/.bashrc"
        fi
    fi
fi

# ---- 2. Config default ----
CFG="$HOME/.config/vault-graph/config.json"
if [ ! -f "$CFG" ]; then
    mkdir -p "$(dirname "$CFG")"
    VAULT_PATH="$HOME/.hermes/vault"
    if [ ! -d "$VAULT_PATH" ]; then
        VAULT_PATH="."
    fi
    cat > "$CFG" << CFGEOF
{
  "vault": "$VAULT_PATH",
  "out": "vault-out"
}
CFGEOF
    echo "  [✓] config:  $CFG"
fi
echo ""

# ---- 3. Skill for assistants ----
SKILL_MD="$SCRIPT_DIR/skill.md"
cat > "$SKILL_MD" << 'SKILLEOF'
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
SKILLEOF

echo "--- Skills ---"

# ---- Hermes ----
if [ -d "$HOME/.hermes" ]; then
    DST="$HOME/.hermes/skills/vault/vault-graph/SKILL.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    echo "  [✓] Hermes:  $DST"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))

    # ---- Hermes MCP ----
    MCP_JSON="$HOME/.hermes/mcp.json"
    if [ ! -f "$MCP_JSON" ]; then
        PYTHONPATH_LINE="export PYTHONPATH=\"$SCRIPT_DIR:\$PYTHONPATH\" &&"
        cat > "$MCP_JSON" << MCPEOF
{
  "mcpServers": {
    "vault-graph": {
      "command": "bash",
      "args": [
        "-c",
        "$PYTHONPATH_LINE exec python3 -m vault_graph.serve $GRAPH_JSON_DEFAULT"
      ],
      "cwd": "$SCRIPT_DIR"
    }
  }
}
MCPEOF
        echo "  [✓] MCP:     $MCP_JSON"
    else
        echo "  [✓] MCP:     already exists"
    fi
else
    echo "  [ ] Hermes:  SKIP (no ~/.hermes)"
fi

# ---- Trae ----
if [ -d "$HOME/.trae" ]; then
    DST="$HOME/.trae/builtin_skills/vault-graph/SKILL.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    echo "  [✓] Trae:    $DST"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))

    # ---- Trae MCP ----
    TMC="$HOME/.trae/mcps/vault-graph"
    mkdir -p "$TMC/solo_agent/vault-graph/tools"
    echo '{"server_name":"vault-graph"}' > "$TMC/solo_agent/vault-graph/SERVER_METADATA.json"
    echo '{"name":"graph_stats","description":"Graph statistics: node count, edge count, density, edge confidence breakdown","inputSchema":{"type":"object","properties":{}}}' > "$TMC/solo_agent/vault-graph/tools/graph_stats.json"
    echo '{"name":"graph_search","description":"Search nodes and edges by name or path","inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}' > "$TMC/solo_agent/vault-graph/tools/graph_search.json"
    echo '{"name":"graph_path","description":"Find shortest path between two nodes","inputSchema":{"type":"object","properties":{"from":{"type":"string"},"to":{"type":"string"}},"required":["from","to"]}}' > "$TMC/solo_agent/vault-graph/tools/graph_path.json"
    echo '{"name":"graph_explain","description":"Explain a node: type, connections, related nodes","inputSchema":{"type":"object","properties":{"node":{"type":"string"}},"required":["node"]}}' > "$TMC/solo_agent/vault-graph/tools/graph_explain.json"
    echo '{"name":"graph_god_nodes","description":"Top 15 most-connected nodes in the graph","inputSchema":{"type":"object","properties":{}}}' > "$TMC/solo_agent/vault-graph/tools/graph_god_nodes.json"
    echo '{"name":"graph_communities","description":"Community detection summaries with representative nodes","inputSchema":{"type":"object","properties":{}}}' > "$TMC/solo_agent/vault-graph/tools/graph_communities.json"
    echo "  [✓] MCP:     $TMC"
else
    echo "  [ ] Trae:    SKIP (no ~/.trae)"
fi

# ---- Done ----
echo ""
echo "vault-graph ready! $INSTALL_COUNT assistants registered."
echo ""
echo "Commands (run from anywhere):"
echo "  vault-graph build                    ← build graph"
echo "  vault-graph god                      ← top nodes"
echo "  vault-graph search <term>            ← search"
echo "  vault-graph explain <node>           ← node detail"
echo "  vault-graph path <A> <B>             ← shortest path"
echo "  vault-graph watch                    ← auto-rebuild"
echo "  vault-graph serve                    ← MCP server"
echo ""
echo "First run: vault-graph build"
echo ""
