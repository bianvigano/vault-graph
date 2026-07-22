"""Module: query — CLI query commands for vault graph."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter

import networkx as nx


def query_main():
    """CLI entry: python -m vault_graph.query GRAPH.json [command]"""
    if len(sys.argv) < 2:
        _usage()
        sys.exit(1)

    graph_path = Path(sys.argv[1])
    if not graph_path.exists():
        print(f"Error: {graph_path} not found. Run vault-graph first.", file=sys.stderr)
        sys.exit(1)

    G = _load(graph_path)

    if len(sys.argv) < 3:
        # No subcommand: show stats
        _stats(G)
        return

    cmd = sys.argv[2].lower()
    args = sys.argv[3:]

    if cmd == "query" and args:
        _query(G, " ".join(args))
    elif cmd == "path" and len(args) >= 2:
        _path(G, args[0], " ".join(args[1:]))
    elif cmd == "explain" and args:
        _explain(G, " ".join(args))
    elif cmd == "god" or cmd == "top":
        _god_nodes(G)
    elif cmd == "communities":
        _communities(G)
    elif cmd == "stats":
        _stats(G)
    elif cmd == "search" and args:
        _search(G, " ".join(args))
    elif cmd == "isolated":
        _isolated(G)
    else:
        _usage()


def _usage():
    print("vault-graph-query — CLI query tool for knowledge graphs")
    print()
    print("Usage:")
    print("  python -m vault_graph.query graph.json [command] [args]")
    print()
    print("Commands:")
    print("  (no command)            Show graph stats")
    print("  query \"question\"        Natural language query")
    print("  path <A> <B>            Shortest path between two nodes")
    print("  explain <node>          Details about a node")
    print("  god                     Top 10 most-connected nodes")
    print("  communities             Community summary")
    print("  search <term>           Search nodes by name")
    print("  isolated                List isolated nodes")
    print("  stats                   Graph statistics")


def _load(path: Path) -> nx.Graph:
    data = json.loads(path.read_text())
    G = nx.Graph()
    for n in data.get("nodes", []):
        G.add_node(n["id"], **{k: v for k, v in n.items() if k != "id"})
    for e in data.get("edges", []):
        G.add_edge(e["source"], e["target"], **{k: v for k, v in e.items() if k not in ("source", "target")})
    return G


def _find(G, query: str):
    q = query.lower()
    for n in G.nodes():
        if q == n.lower() or q == (G.nodes[n].get("label", "") or "").lower():
            return n
    for n in G.nodes():
        if q in n.lower() or q in (G.nodes[n].get("label", "") or "").lower():
            return n
    return None


def _query(G, question: str):
    """Simple keyword-based graph query."""
    print(f"Query: {question}\n")
    terms = [t.lower() for t in question.split() if len(t) > 2]
    matches = set()
    for term in terms:
        for n in G.nodes():
            label = (G.nodes[n].get("label", "") or "").lower()
            nid = n.lower()
            if term in label or term in nid:
                matches.add(n)

    if not matches:
        print("No matches found.")
        return

    print(f"Matched {len(matches)} nodes:")
    for n in sorted(matches):
        degree = G.degree(n)
        ntype = G.nodes[n].get("type", "other")
        label = G.nodes[n].get("label", n)
        community = G.nodes[n].get("community", "?")
        print(f"  [{ntype:10s}] comm={community:<3} deg={degree:<4} {label[:60]}")

    if len(matches) < 20 and len(matches) > 1:
        print("\nPaths between matches:")
        nodes = list(matches)
        for i in range(min(len(nodes), 5)):
            for j in range(i+1, min(len(nodes), 5)):
                try:
                    path = nx.shortest_path(G, nodes[i], nodes[j])
                    print(f"  {G.nodes[nodes[i]].get('label', nodes[i])[:25]} ... {G.nodes[nodes[j]].get('label', nodes[j])[:25]}: {len(path)-1} hops")
                except nx.NetworkXNoPath:
                    pass


def _path(G, a: str, b: str):
    na = _find(G, a)
    nb = _find(G, b)
    if not na:
        print(f"Not found: {a}")
        return
    if not nb:
        print(f"Not found: {b}")
        return
    try:
        path = nx.shortest_path(G, na, nb)
        print(f"Path ({len(path)-1} hops):")
        for n in path:
            label = G.nodes[n].get("label", n)
            ntype = G.nodes[n].get("type", "?")
            print(f"  [{ntype}] {label[:60]}")
    except nx.NetworkXNoPath:
        print("No path found.")


def _explain(G, query: str):
    n = _find(G, query)
    if not n:
        print(f"Not found: {query}")
        return
    print(f"Node: {G.nodes[n].get('label', n)}")
    print(f" Type: {G.nodes[n].get('type', '?')}")
    print(f" Comm: {G.nodes[n].get('community', '?')}")
    print(f" Degree: {G.degree(n)}")
    print()
    neighbors = [(v, G[u][v]) for u, v in G.edges(n)]
    by_rel = Counter(d.get("relation", "?") for _, d in neighbors)
    by_conf = Counter(d.get("confidence", "?") for _, d in neighbors)
    print(f"Connections ({len(neighbors)}):")
    for rel, count in by_rel.most_common():
        print(f"  {rel}: {count}")
    print(f"Confidence:")
    for conf, count in sorted(by_conf.items()):
        print(f"  {conf}: {count}")
    if neighbors:
        print(f"\nTop connections:")
        for nb, edge in neighbors[:15]:
            label = G.nodes[nb].get("label", nb)
            print(f"  → {label[:50]:50s} [{edge.get('confidence', '?')}]")


def _god_nodes(G):
    deg = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:15]
    print("God Nodes (top 15):")
    for n, d in deg:
        if d == 0:
            break
        label = G.nodes[n].get("label", n)
        ntype = G.nodes[n].get("type", "?")
        print(f"  deg={d:<5} [{ntype:10s}] {label[:60]}")


def _communities(G):
    comm = nx.get_node_attributes(G, "community")
    if not comm:
        print("No community data. Run clustering first.")
        return
    ccount = Counter(comm.values())
    print(f"Communities: {len(ccount)}")
    for cid, count in ccount.most_common(15):
        reps = [n for n, c in comm.items() if c == cid]
        rep = max(reps, key=lambda n: G.degree(n)) if reps else "?"
        label = G.nodes[rep].get("label", rep) if rep != "?" else "?"
        print(f"  comm {cid:<4} size={count:<5} {label[:60]}")


def _search(G, term: str):
    q = term.lower()
    found = []
    for n in G.nodes():
        label = (G.nodes[n].get("label", "") or "").lower()
        if q in label or q in n.lower():
            found.append((n, G.nodes[n].get("label", n), G.nodes[n].get("type", "?"), G.degree(n)))

    found.sort(key=lambda x: x[3], reverse=True)
    print(f"Search: '{term}' — {len(found)} results")
    for nid, label, ntype, deg in found[:30]:
        print(f"  deg={deg:<5} [{ntype:10s}] {label[:60]}")

    if len(found) > 30:
        print(f"  ... and {len(found)-30} more")


def _isolated(G):
    deg = list(G.degree())
    isolated = [(n, G.nodes[n].get("label", n)) for n, d in deg if d == 0]
    print(f"Isolated nodes: {len(isolated)}/{G.number_of_nodes()}")
    for nid, label in sorted(isolated)[:20]:
        print(f"  {label[:60]}")
    if len(isolated) > 20:
        print(f"  ... and {len(isolated)-20} more")


def _stats(G):
    n = G.number_of_nodes()
    e = G.number_of_edges()
    density = round(nx.density(G), 4) if n > 0 else 0
    print(f"Nodes:      {n}")
    print(f"Edges:      {e}")
    print(f"Density:    {density}")

    types = Counter(G.nodes[n].get("type", "?") for n in G.nodes())
    print(f"Types:")
    for t, c in types.most_common():
        print(f"  {t:15s} {c}")

    ec = Counter(d.get("confidence", "?") for _, _, d in G.edges(data=True))
    print(f"Edges:")
    for c, cnt in sorted(ec.items()):
        print(f"  {c:15s} {cnt}")

    comms = set(nx.get_node_attributes(G, "community").values())
    print(f"Communities: {len(comms)}")


if __name__ == "__main__":
    query_main()
