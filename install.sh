#!/bin/bash
# vault-graph install — CLI wrapper, skills, MCP. No pip needed.
# Usage: bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GRAPH_JSON_DEFAULT="$HOME/vault/vault-out/graph.json"
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
    VAULT_PATH="$HOME/vault"
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
description: Knowledge graph for Vault + Trae memory. Always check graph before searching files.
trigger: User says "/vault-graph", "graph vault", "visualize vault", asks about vault connections, or searches vault/wiki knowledge.
always-on: true
---

# Vault Knowledge Graph

## ALWAYS-ON RULE
When user asks about vault/wiki content or connections between topics:
1. **FIRST** query the graph: `vault-graph search <term>`, `vault-graph explain <node>`, or `vault-graph query "question"`
2. **THEN** fall back to file search only if graph returns nothing

## Commands (run from anywhere)
```bash
vault-graph build               # Rebuild graph from vault + Trae memory
vault-graph god                 # Top 15 most-connected nodes
vault-graph search <term>       # Search nodes/edges by name
vault-graph explain <node>      # Node detail + all connections
vault-graph path <A> <B>        # Shortest path between two nodes
vault-graph communities         # Community detection summaries
vault-graph isolated            # Nodes with zero connections
vault-graph stats               # Graph statistics (nodes, edges, types)
vault-graph query "question"    # Natural language question
vault-graph watch               # Auto-rebuild on file changes
vault-graph serve               # MCP server (Hermes only)
```

No path needed — auto-detects graph.json from config.

## Sources
- `~/.hermes/vault/` — .md files with [[wiki-links]] + headings
- `~/.trae/memory/projects/` — project_memory.md, topics.md

## Note: Trae MCP Limitation
Trae IDE v1.0.24 doesn't support external command-based MCP servers.
The agent uses terminal commands instead. MCP works on Hermes via `~/.hermes/mcp.json`.
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
    echo "  [✓] Trae MCP: $TMC + ~/.trae/mcp.json"

    # ---- Trae mcp.json ----
    MCP_JSON="$HOME/.trae/mcp.json"
    if [ ! -f "$MCP_JSON" ] || ! grep -q "vault-graph" "$MCP_JSON" 2>/dev/null; then
        cat > "$MCP_JSON" << TMCPEOF
{
  "mcpServers": {
    "vault-graph": {
      "command": "bash",
      "args": [
        "-c",
        "export PYTHONPATH=\\"$SCRIPT_DIR:\\$PYTHONPATH\\" && exec python3 -m vault_graph.serve $GRAPH_JSON_DEFAULT"
      ],
      "cwd": "$SCRIPT_DIR"
    }
  }
}
TMCPEOF
        echo "  [✓] Trae MCP: ~/.trae/mcp.json"
    fi
else
    echo "  [ ] Trae:    SKIP (no ~/.trae)"
fi

# ---- Claude Code ----
if [ -d "$HOME/.claude" ]; then
    DST="$HOME/.claude/skills/vault-graph/SKILL.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    # Append to CLAUDE.md context
    touch "$HOME/.claude/CLAUDE.md"
    if ! grep -q "vault-graph" "$HOME/.claude/CLAUDE.md" 2>/dev/null; then
        echo "" >> "$HOME/.claude/CLAUDE.md"
        echo "## Vault Knowledge Graph" >> "$HOME/.claude/CLAUDE.md"
        echo "Always check vault-graph before searching vault/wiki files: \`vault-graph search/explain/query\`" >> "$HOME/.claude/CLAUDE.md"
        echo "Graph: ~/.hermes/vault/vault-out/graph.json" >> "$HOME/.claude/CLAUDE.md"
    fi
    echo "  [✓] Claude:  $DST + ~/.claude/CLAUDE.md"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))
else
    echo "  [ ] Claude:  SKIP (no ~/.claude)"
fi

# ---- Codex ----
if [ -d "$HOME/.codex" ]; then
    DST="$HOME/.codex/skills/vault-graph/SKILL.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    # Append to AGENTS.md
    touch "$HOME/.codex/AGENTS.md"
    if ! grep -q "vault-graph" "$HOME/.codex/AGENTS.md" 2>/dev/null; then
        echo "" >> "$HOME/.codex/AGENTS.md"
        echo "## Vault Knowledge Graph" >> "$HOME/.codex/AGENTS.md"
        echo "Always check vault-graph before searching vault/wiki files: \`vault-graph search/explain/query\`" >> "$HOME/.codex/AGENTS.md"
        echo "Graph: ~/.hermes/vault/vault-out/graph.json" >> "$HOME/.codex/AGENTS.md"
    fi
    echo "  [✓] Codex:   $DST + ~/.codex/AGENTS.md"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))
else
    echo "  [ ] Codex:   SKIP (no ~/.codex)"
fi

# ---- Continue ----
if [ -d "$HOME/.continue" ]; then
    DST="$HOME/.continue/rules/vault-graph.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    echo "  [✓] Continue: $DST"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))
else
    echo "  [ ] Continue: SKIP (no ~/.continue)"
fi

# ---- Codeium ----
if [ -d "$HOME/.codeium" ]; then
    DST="$HOME/.codeium/memories/global_rules.md"
    mkdir -p "$(dirname "$DST")"
    if ! grep -q "vault-graph" "$DST" 2>/dev/null; then
        echo "" >> "$DST"
        echo "## Vault Knowledge Graph" >> "$DST"
        echo "Always check vault-graph before searching vault/wiki files: \`vault-graph search/explain/query\`" >> "$DST"
        echo "Graph: ~/.hermes/vault/vault-out/graph.json" >> "$DST"
    fi
    echo "  [✓] Codeium: $DST"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))
else
    echo "  [ ] Codeium: SKIP (no ~/.codeium)"
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
