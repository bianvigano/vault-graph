#!/bin/bash
# vault-graph install — auto-detect assistants, register skill + MCP
# Usage: bash install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GRAPH_JSON_DEFAULT="$HOME/.hermes/vault/vault-out/graph.json"
INSTALL_COUNT=0

echo "vault-graph install"
echo "==================="
echo "  repo: $SCRIPT_DIR"

# ---- Requirements ----
echo ""
echo "Requirements: pip install networkx matplotlib"
python3 -c "import networkx" 2>/dev/null && echo "  [✓] networkx" || {
    echo "  [✗] networkx HILANG. Install: pip install networkx"
    echo "      (graph tetap terbentuk tapi tanpa community detection)"
}
python3 -c "import matplotlib" 2>/dev/null && echo "  [✓] matplotlib" || {
    echo "  [✗] matplotlib HILANG. Install: pip install matplotlib"
    echo "      (graph.svg tidak terbentuk, graph.html tetap OK)"
}
echo ""

# ---- 1. CLI executables (~/.local/bin) ----
echo "--- CLI ---"
mkdir -p "$HOME/.local/bin"

# vault-graph wrapper
cat > "$HOME/.local/bin/vault-graph" << VGEOF
#!/bin/bash
cd "$SCRIPT_DIR" && exec python3 -m vault_graph.main "\$@"
VGEOF
chmod +x "$HOME/.local/bin/vault-graph"
echo "  [✓] vault-graph → ~/.local/bin/vault-graph"

# vq alias (backward compat)
cat > "$HOME/.local/bin/vq" << VQEOF
#!/bin/bash
cd "$SCRIPT_DIR" && exec python3 -m vault_graph.query "\$@"
VQEOF
chmod +x "$HOME/.local/bin/vq"
echo "  [✓] vq (legacy)  → ~/.local/bin/vq"

# Pastikan ~/.local/bin di PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    if [ -f "$HOME/.bashrc" ]; then
        if ! grep -q '.local/bin' "$HOME/.bashrc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo "  [✓] PATH        → ~/.local/bin ditambah ke ~/.bashrc"
        fi
    fi
fi
echo ""

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
        echo "  [✓] MCP:     $MCP_JSON"
    else
        echo "  [✓] MCP:     already exists ($MCP_JSON)"
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
    cat > "$TMC/solo_agent/vault-graph/SERVER_METADATA.json" <<< '{"server_name":"vault-graph"}'
    
    cat > "$TMC/solo_agent/vault-graph/tools/graph_stats.json" <<< '{"name":"graph_stats","description":"Graph statistics: node count, edge count, density, edge confidence breakdown","inputSchema":{"type":"object","properties":{}}}'
    cat > "$TMC/solo_agent/vault-graph/tools/graph_search.json" <<< '{"name":"graph_search","description":"Search nodes and edges by name or path","inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}'
    cat > "$TMC/solo_agent/vault-graph/tools/graph_path.json" <<< '{"name":"graph_path","description":"Find shortest path between two nodes","inputSchema":{"type":"object","properties":{"from":{"type":"string"},"to":{"type":"string"}},"required":["from","to"]}}'
    cat > "$TMC/solo_agent/vault-graph/tools/graph_explain.json" <<< '{"name":"graph_explain","description":"Explain a node: type, connections, related nodes","inputSchema":{"type":"object","properties":{"node":{"type":"string"}},"required":["node"]}}'
    cat > "$TMC/solo_agent/vault-graph/tools/graph_god_nodes.json" <<< '{"name":"graph_god_nodes","description":"Top 15 most-connected nodes in the graph","inputSchema":{"type":"object","properties":{}}}'
    cat > "$TMC/solo_agent/vault-graph/tools/graph_communities.json" <<< '{"name":"graph_communities","description":"Community detection summaries with representative nodes","inputSchema":{"type":"object","properties":{}}}'
    echo "  [✓] MCP:     $TMC"
else
    echo "  [ ] Trae:    SKIP (no ~/.trae)"
fi

# ---- Done ----
echo ""
echo "vault-graph ready! $INSTALL_COUNT assistants registered."
echo ""
echo "Commands:"
echo "  vault-graph ~/.hermes/vault              ← build graph"
echo "  vault-graph --query vault-out/graph.json god  ← query graph"
echo "  vault-graph --watch                      ← auto-rebuild"
echo "  vault-graph --serve vault-out/graph.json ← MCP server"
echo "  vq vault-out/graph.json god             ← query (legacy, same as --query)"
echo ""
echo "For new PC:"
echo "  git clone https://github.com/bianvigano/vault-graph"
echo "  cd vault-graph && bash install.sh"
echo "  vault-graph ~/.hermes/vault"
echo ""
