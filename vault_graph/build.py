"""Module: build — construct NetworkX graph from extractions."""
from __future__ import annotations

import networkx as nx


def build_graph(extractions: list[dict]) -> nx.Graph:
    """Build NetworkX graph from list of extraction dicts.

    Each extraction: {"nodes": [...], "edges": [...]}
    """
    G = nx.Graph()

    # Add all nodes
    for ext in extractions:
        for node in ext.get("nodes", []):
            G.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})

    # Add all edges
    for ext in extractions:
        for edge in ext.get("edges", []):
            src = edge["source"]
            tgt = edge["target"]
            # Only add if both nodes exist (skip orphan edges)
            G.add_edge(src, tgt, **{
                "relation": edge.get("relation", ""),
                "confidence": edge.get("confidence", ""),
            })

    return G
