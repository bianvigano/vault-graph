"""Module: analyze — god nodes, surprises, community stats."""
from __future__ import annotations

import networkx as nx
from collections import Counter


def analyze(G: nx.Graph) -> dict:
    """Analyze graph: god nodes, community stats, isolated nodes, surprises."""
    n = G.number_of_nodes()
    e = G.number_of_edges()

    analysis = {
        "node_count": n,
        "edge_count": e,
        "density": round(nx.density(G), 4) if n > 0 else 0,
        "god_nodes": [],
        "isolated_nodes": [],
        "community_count": 0,
        "community_stats": {},
        "surprises": [],
        "edge_confidence": Counter(),
    }

    if n == 0:
        return analysis

    # Edge confidence count
    for u, v, d in G.edges(data=True):
        analysis["edge_confidence"][d.get("confidence", "UNKNOWN")] += 1

    # Top nodes by degree
    degree = sorted(G.degree(), key=lambda x: x[1], reverse=True)
    analysis["god_nodes"] = [
        {"node": n, "degree": d, "label": G.nodes[n].get("label", ""), "type": G.nodes[n].get("type", "other")}
        for n, d in degree[:15] if d > 0
    ]

    # Isolated nodes
    analysis["isolated_nodes"] = [
        {"node": n, "label": G.nodes[n].get("label", ""), "type": G.nodes[n].get("type", "other")}
        for n, d in degree if d == 0
    ]

    # Community stats
    node_community = nx.get_node_attributes(G, "community")
    if node_community:
        comm_count = Counter(node_community.values())
        analysis["community_count"] = len(comm_count)
        for comm_id, count in comm_count.most_common(10):
            # Find representative node in this community
            rep_nodes = [n for n, c in node_community.items() if c == comm_id]
            rep_max = max(rep_nodes, key=lambda n: G.degree(n)) if rep_nodes else "unknown"
            analysis["community_stats"][str(comm_id)] = {
                "size": count,
                "representative": G.nodes[rep_max].get("label", rep_max),
            }

    # Surprises: high-confidence INFERRED edges
    for u, v, d in G.edges(data=True):
        if d.get("confidence") == "INFERRED" and d.get("relation") == "heading-mention":
            analysis["surprises"].append({
                "source": G.nodes[u].get("label", u),
                "target": G.nodes[v].get("label", v),
                "relation": d.get("relation", ""),
            })

    return analysis
