"""Module: serve — MCP stdio server for graph query."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx


def serve(graph_path: Path):
    """Start MCP stdio server for querying vault graph.
    
    Reads JSON-RPC from stdin, responds with graph query results.
    Tools: graph_path, graph_explain, graph_god_nodes, graph_search, graph_communities, graph_stats
    """
    G = _load_graph(graph_path)

    for line in sys.stdin:
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        method = request.get("method", "")
        req_id = request.get("id")

        if method == "initialize":
            _respond(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "vault-graph-mcp", "version": "2.0.0"},
            })
            _send({"jsonrpc": "2.0", "result": None})

        elif method == "notifications/initialized":
            pass  # Client sent init confirmation — silently ack

        elif method == "tools/list":
            _respond(req_id, {"tools": [
                {"name": "graph_path", "description": "Find shortest path between two nodes", "inputSchema": {"type": "object", "properties": {"from": {"type": "string"}, "to": {"type": "string"}}, "required": ["from", "to"]}},
                {"name": "graph_explain", "description": "Explain a node and its connections", "inputSchema": {"type": "object", "properties": {"node": {"type": "string"}}, "required": ["node"]}},
                {"name": "graph_god_nodes", "description": "List most-connected nodes", "inputSchema": {"type": "object", "properties": {}}},
                {"name": "graph_search", "description": "Search nodes by label", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
                {"name": "graph_communities", "description": "List community summaries", "inputSchema": {"type": "object", "properties": {}}},
                {"name": "graph_stats", "description": "Graph statistics", "inputSchema": {"type": "object", "properties": {}}},
            ]})

        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            args = params.get("arguments", {})

            try:
                if tool_name == "graph_path":
                    result = _path(G, args["from"], args["to"])
                elif tool_name == "graph_explain":
                    result = _explain(G, args["node"])
                elif tool_name == "graph_god_nodes":
                    result = _god_nodes(G)
                elif tool_name == "graph_search":
                    result = _search(G, args["query"])
                elif tool_name == "graph_communities":
                    result = _communities(G)
                elif tool_name == "graph_stats":
                    result = _stats(G)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}

                _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
            except Exception as e:
                _respond(req_id, {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True})


def _load_graph(path: Path) -> nx.Graph:
    data = json.loads(path.read_text())
    G = nx.Graph()
    for n in data.get("nodes", []):
        G.add_node(n["id"], **{k: v for k, v in n.items() if k != "id"})
    for e in data.get("edges", []):
        G.add_edge(e["source"], e["target"], **{k: v for k, v in e.items() if k not in ("source", "target")})
    return G


def _path(G, from_label, to_label):
    f = _find_node(G, from_label)
    t = _find_node(G, to_label)
    if not f or not t:
        return {"error": f"Node not found: {from_label if not f else to_label}"}
    try:
        path = nx.shortest_path(G, f, t)
        hops = len(path) - 1
        nodes = [{"id": n, "label": G.nodes[n].get("label", ""), "type": G.nodes[n].get("type", "")} for n in path]
        return {"path": nodes, "hops": hops}
    except nx.NetworkXNoPath:
        return {"error": "No path found"}


def _explain(G, query):
    nid = _find_node(G, query)
    if not nid:
        return {"error": f"Node not found: {query}"}
    neighbors = [(v, G[u][v]) for u, v in G.edges(nid)]
    by_rel = {}
    for _, edge in neighbors:
        t = edge.get("relation", "unknown")
        by_rel[t] = by_rel.get(t, 0) + 1
    return {
        "id": nid,
        "label": G.nodes[nid].get("label", ""),
        "type": G.nodes[nid].get("type", ""),
        "degree": G.degree(nid),
        "community": G.nodes[nid].get("community"),
        "relations": by_rel,
    }


def _god_nodes(G):
    deg = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:15]
    return [{"id": n, "label": G.nodes[n].get("label", ""), "type": G.nodes[n].get("type", ""), "degree": d} for n, d in deg if d > 0]


def _search(G, query):
    q = query.lower()
    matches = []
    for n in G.nodes():
        label = (G.nodes[n].get("label", "") or "").lower()
        if q in label or q in n.lower():
            matches.append({"id": n, "label": G.nodes[n].get("label", ""), "type": G.nodes[n].get("type", ""), "degree": G.degree(n)})
    return {"matches": matches[:30], "total": len(matches)}


def _communities(G):
    from collections import Counter
    comm = nx.get_node_attributes(G, "community")
    comm_count = Counter(comm.values())
    result = {}
    for cid, count in comm_count.most_common(20):
        rep = max([n for n, c in comm.items() if c == cid], key=lambda n: G.degree(n))
        result[str(cid)] = {"size": count, "representative": G.nodes[rep].get("label", rep)}
    return result


def _stats(G):
    from collections import Counter
    types = Counter(G.nodes[n].get("type", "other") for n in G.nodes())
    ec = Counter(d.get("confidence", "?") for _, _, d in G.edges(data=True))
    comms = set(nx.get_node_attributes(G, "community").values())
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "types": dict(types.most_common()),
        "edge_confidence": dict(sorted(ec.items())),
        "communities": len(comms),
    }


def _find_node(G, query):
    q = query.lower()
    for n in G.nodes():
        if q == n.lower() or q == (G.nodes[n].get("label", "") or "").lower():
            return n
    for n in G.nodes():
        if q in n.lower() or q in (G.nodes[n].get("label", "") or "").lower():
            return n
    return None


def _send(data):
    sys.stdout.write(json.dumps(data) + "\n")
    sys.stdout.flush()


def _respond(req_id, result):
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})
