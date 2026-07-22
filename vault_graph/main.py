#!/usr/bin/env python3
"""
vault-graph — Turn Hermes Vault (.md files) into a knowledge graph.
Graphify-style pipeline: detect -> extract -> build -> cluster -> analyze -> report -> export.

Usage:
  python3 -m vault_graph.main /home/the-meh/.hermes/vault --out vault-out
  python3 -m vault_graph.main /home/the-meh/.hermes/vault --out vault-out --watch
  python3 -m vault_graph.main /home/the-meh/.hermes/vault --out vault-out --serve GRAPH.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import networkx as nx
except ImportError:
    sys.exit("pip install networkx")


def main():
    parser = argparse.ArgumentParser(description="Vault Knowledge Graph")
    parser.add_argument("vault_path", nargs="?", default="", help="Path to Hermes vault")
    parser.add_argument("--out", default="/home/the-meh/.hermes/vault/vault-out", help="Output directory")
    parser.add_argument("--watch", action="store_true", help="Watch for changes and auto-rebuild")
    parser.add_argument("--serve", metavar="GRAPH.json", help="Start MCP server on graph.json")
    parser.add_argument("--install", action="store_true", help="Install skill into ~/.hermes/skills/")
    parser.add_argument("--project", action="store_true", help="Project-scoped install")
    args = parser.parse_args()

    vault = Path(args.vault_path) if args.vault_path else Path(".")
    if not args.serve and not args.install and not vault.is_dir():
        sys.exit(f"Not a directory: {vault}")
    out_dir = Path(args.out)

    # --install
    if args.install:
        from vault_graph.install import install
        install(project=args.project)
        return

    # --serve
    if args.serve:
        graph_path = Path(args.serve)
        if not graph_path.exists():
            sys.exit(f"Graph not found: {graph_path}")
        from vault_graph.serve import serve
        print(f"MCP server on {graph_path}")
        serve(graph_path)
        return

    # --watch
    if args.watch:
        from vault_graph.watch import watch
        # Initial rebuild
        rebuild(vault, out_dir)
        # Then watch
        watch(vault, out_dir)
        return

    # Normal pipeline
    rebuild(vault, out_dir)


def rebuild(vault: Path, out_dir: Path):
    """Full pipeline rebuild."""
    from vault_graph.detect import collect_files
    from vault_graph.extract import extract
    from vault_graph.cache import load_cache, save_cache, split_files
    from vault_graph.security import sanitize_label

    cache_path = out_dir / ".vault_graph_cache.json"
    cache = load_cache(cache_path)

    # 1) detect
    files = collect_files(vault)
    cached_files, uncached_files, new_cache = split_files(files, cache, vault)
    
    if len(uncached_files) == 0 and out_dir.joinpath("graph.html").exists():
        print(f"  (all {len(files)} files cached — unchanged)")
        return

    skip_count = len(cached_files)
    print(f"  detect:  {len(files)} files ({skip_count} cached, {len(uncached_files)} new)")

    # 2) extract
    all_headings = _collect_all_headings(uncached_files)
    extractions = []
    for f in uncached_files:
        rel = str(f.relative_to(vault))
        result = extract(f, all_heading_set=all_headings)
        for n in result.get("nodes", []):
            n["id"] = rel if n["id"] == str(f) else n["id"]
            n["label"] = sanitize_label(n.get("label", ""))
        for e in result.get("edges", []):
            if e["source"] == str(f):
                e["source"] = rel
        extractions.append(result)

    node_count = sum(len(e.get("nodes", [])) for e in extractions)
    edge_count = sum(len(e.get("edges", [])) for e in extractions)
    print(f"  extract: {node_count} nodes, {edge_count} raw edges")

    # For cached files, load previous extractions from graph.json if exists
    old_graph_path = out_dir / "graph.json"
    if old_graph_path.exists() and cached_files:
        import json as _json
        old_data = _json.loads(old_graph_path.read_text())
        for node in old_data.get("nodes", []):
            nid = node.get("id", "")
            rel = str(nid)
            if any(str(cf.relative_to(vault)) == rel for cf in cached_files):
                extractions.append({"nodes": [node], "edges": []})

    # 3) build
    from vault_graph.build import build_graph
    G = build_graph(extractions)
    print(f"  build:   {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # 4) cluster
    from vault_graph.cluster import cluster
    G = cluster(G)
    comms = len(set(nx.get_node_attributes(G, "community").values()))
    print(f"  cluster: {comms} communities")

    # 5) analyze
    from vault_graph.analyze import analyze
    analysis = analyze(G)
    print(f"  analyze: {len(analysis['god_nodes'])} god nodes, {len(analysis['isolated_nodes'])} isolated, {len(analysis['surprises'])} surprises")

    # 6) report
    from vault_graph.report import render_report
    report_text = render_report(G, analysis)
    print(f"  report:  {len(report_text)} chars")

    # 7) export
    from vault_graph.export import export
    export(G, analysis, out_dir, report_text)

    # 8) foam-wiki export
    from vault_graph.wiki_export import export_wiki
    export_wiki(G, out_dir, vault)

    # 9) mermaid export
    from vault_graph.mermaid_export import export_mermaid
    export_mermaid(G, out_dir)

    # Save cache
    save_cache(cache_path, new_cache)

    # Summary
    print(f"\nKnowledge Graph Report")
    print(f"=======================")
    print(f"  Nodes:       {analysis['node_count']}")
    print(f"  Edges:       {analysis['edge_count']}")
    print(f"  Density:     {analysis['density']}")
    print(f"  Communities: {analysis['community_count']}")
    print(f"  Isolated:    {len(analysis['isolated_nodes'])}")
    print(f"  Cached:      {skip_count} files (unchanged)")

    if analysis["god_nodes"]:
        print(f"\n  God Nodes (top 5):")
        for gn in analysis["god_nodes"][:5]:
            print(f"    {gn['label'][:40]:40s} degree={gn['degree']:>4}  [{gn['type']}]")

    ec = analysis["edge_confidence"]
    if ec:
        print(f"\n  Edge Confidence:")
        for conf, count in sorted(ec.items()):
            print(f"    {conf:15s} {count}")

    print(f"\nDone! Open: {out_dir / 'graph.html'}")


def _collect_all_headings(files: list[Path]) -> dict[str, list[str]]:
    import re
    heading_re = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)
    code_block_re = re.compile(r"```[\s\S]*?```", re.MULTILINE)

    result = {}
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        text = code_block_re.sub("", text)
        headings = heading_re.findall(text)
        result[str(f)] = headings
    return result


if __name__ == "__main__":
    main()
