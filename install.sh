#!/bin/bash
# vault-graph install — auto-detect assistants, register skill + MCP
# Usage: bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GRAPH_JSON_DEFAULT="$HOME/.hermes/vault/vault-out/graph.json"
INSTALL_COUNT=0

echo "vault-graph install"
echo "==================="

# ---- Requirements ----
echo ""
echo "Requirements: pip install networkx matplotlib"
python3 -c "import networkx" 2>/dev/null || echo "  [!] networkx not installed. Run: pip install networkx"
python3 -c "import matplotlib" 2>/dev/null || echo "  [!] matplotlib not installed. Run: pip install matplotlib"
echo ""

# ---- 1. CLI alias ----
ALIAS_LINE="alias vq=\"cd '$SCRIPT_DIR' && python3 -m vault_graph.query\""
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
cat > "$SKILL_MD" << 'SKILLEOF'
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
vq vault-out/graph.json stats
```

## Watch
```bash
vault-graph /path/to/vault --watch
```

## MCP
```bash
python3 -m vault_graph.serve vault-out/graph.json
```

## Output
- graph.html (D3 interactive + query bar)
- graph.json (raw data)
- mermaid.html (Mermaid flowchart)
- foam-vault/ ([[wiki-linked]] pages)
- GRAPH_REPORT.md (analysis)
SKILLEOF

# ---- Hermes ----
if [ -d "$HOME/.hermes" ]; then
    DST="$HOME/.hermes/skills/vault/vault-graph/SKILL.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    echo "  [✓] Hermes: $DST"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))

    # ---- Hermes MCP ----
    MCP_JSON="$HOME/.hermes/mcp.json"
    if [ ! -f "$MCP_JSON" ]; then
        cat > "$MCP_JSON" << MCPEOF
{
  "mcpServers": {
    "vault-graph": {
      "command": "python3",
      "args": [
        "-m",
        "vault_graph.serve",
        "${GRAPH_JSON_DEFAULT}"
      ],
      "cwd": "${SCRIPT_DIR}"
    }
  }
}
MCPEOF
        echo "  [✓] Hermes MCP: $MCP_JSON"
    else
        echo "  [✓] Hermes MCP: already exists (mcp.json found)"
    fi
fi

# ---- Trae ----
if [ -d "$HOME/.trae" ]; then
    DST="$HOME/.trae/builtin_skills/vault-graph/SKILL.md"
    mkdir -p "$(dirname "$DST")"
    cp "$SKILL_MD" "$DST"
    echo "  [✓] Trae:   $DST"
    INSTALL_COUNT=$((INSTALL_COUNT + 1))

    # ---- Trae MCP ----
    TMC="$HOME/.trae/mcps/vault-graph"
    mkdir -p "$TMC/solo_agent/vault-graph/tools"
    echo '{"server_name":"vault-graph"}' > "$TMC/solo_agent/vault-graph/SERVER_METADATA.json"
    echo '{"name":"graph_stats","description":"Graph statistics","inputSchema":{"type":"object","properties":{}}}' > "$TMC/solo_agent/vault-graph/tools/graph_stats.json"
    echo '{"name":"graph_search","description":"Search nodes","inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}' > "$TMC/solo_agent/vault-graph/tools/graph_search.json"
    echo '{"name":"graph_path","description":"Shortest path between nodes","inputSchema":{"type":"object","properties":{"from":{"type":"string"},"to":{"type":"string"}},"required":["from","to"]}}' > "$TMC/solo_agent/vault-graph/tools/graph_path.json"
    echo '{"name":"graph_explain","description":"Explain a node","inputSchema":{"type":"object","properties":{"node":{"type":"string"}},"required":["node"]}}' > "$TMC/solo_agent/vault-graph/tools/graph_explain.json"
    echo '{"name":"graph_god_nodes","description":"Most-connected nodes","inputSchema":{"type":"object","properties":{}}}' > "$TMC/solo_agent/vault-graph/tools/graph_god_nodes.json"
    echo '{"name":"graph_communities","description":"Community summaries","inputSchema":{"type":"object","properties":{}}}' > "$TMC/solo_agent/vault-graph/tools/graph_communities.json"
    echo "  [✓] Trae MCP: $TMC"
fi

# ---- Done ----
echo ""
echo "Done! $INSTALL_COUNT assistants registered."
echo ""
echo "For friends:"
echo "  git clone https://github.com/bianvigano/vault-graph"
echo "  cd vault-graph && bash install.sh"
echo ""
echo "Run 'source ~/.bash_aliases' or open new terminal."
