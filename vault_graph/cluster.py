"""Module: cluster — community detection (greedy modularity)."""
from __future__ import annotations

import networkx as nx
from networkx.algorithms import community


def cluster(G: nx.Graph) -> nx.Graph:
    """Run community detection and add 'community' attr to each node.

    Uses greedy modularity optimization (fast, deterministic).
    Falls back to label propagation for large graphs.
    """
    if G.number_of_edges() == 0:
        # All isolated → assign community 0
        for n in G.nodes():
            G.nodes[n]["community"] = 0
        return G

    try:
        comms = community.greedy_modularity_communities(G)
    except Exception:
        try:
            comms = list(community.label_propagation_communities(G))
        except Exception:
            for n in G.nodes():
                G.nodes[n]["community"] = 0
            return G

    for i, comm in enumerate(comms):
        for node in comm:
            G.nodes[node]["community"] = i

    return G
