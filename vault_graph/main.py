#!/usr/bin/env python3
"""
vault-graph — Turn Vault (.md + Trae) into a knowledge graph.

Usage:
  vault-graph build [vault_path]         Build graph (default: from config)
  vault-graph god                          Top 15 most-connected nodes
  vault-graph search <term>               Search nodes
  vault-graph explain <node>              Node details
  vault-graph path <A> <B>                Shortest path
  vault-graph communities                 Community summary
  vault-graph isolated                    Nodes without connections
  vault-graph stats                       Graph statistics
  vault-graph query <question>            Natural language query
  vault-graph config [show|set|path]      View/edit config
  vault-graph watch                       Auto-rebuild on file changes
  vault-graph serve                       Start MCP server
  vault-graph install                     Register skill with assistants
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "vault-graph"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "vault": str(Path.home() / ".hermes" / "vault"),
    "out": "vault-out",
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def resolve_graph_path() -> Path:
    cfg = load_config()
    vault = Path(cfg["vault"])
    out = Path(cfg["out"])
    if not out.is_absolute():
        out = vault / out
    return out / "graph.json"


def resolve_vault_out(vault_path: str | None = None) -> tuple[Path, Path]:
    cfg = load_config()
    vault = Path(cfg["vault"])
    if vault_path:
        vault = Path(vault_path)
    out = Path(cfg["out"])
    if not out.is_absolute():
        out = vault / out
    return vault, out


def main():
    parser = argparse.ArgumentParser(
        description="Vault Knowledge Graph",
        usage="vault-graph <command> [args]",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    p_build = sub.add_parser("build", help="Build knowledge graph")
    p_build.add_argument("vault_path", nargs="?", help="Vault path (default: from config)")

    sub.add_parser("god", help="Top 15 most-connected nodes")
    sub.add_parser("communities", help="Community summary")
    sub.add_parser("isolated", help="Nodes with no connections")
    sub.add_parser("stats", help="Graph statistics")

    p_search = sub.add_parser("search", help="Search nodes by name")
    p_search.add_argument("term", help="Search term")

    p_explain = sub.add_parser("explain", help="Explain a node")
    p_explain.add_argument("node", help="Node name or label")

    p_path = sub.add_parser("path", help="Shortest path between two nodes")
    p_path.add_argument("a", help="From node")
    p_path.add_argument("b", help="To node")

    p_query = sub.add_parser("query", help="Natural language graph query")
    p_query.add_argument("question", help="Question text")

    # ---- config ----
    p_cfg = sub.add_parser("config", help="View or edit config")
    p_cfg.add_argument("action", nargs="?", default="show",
                       choices=["show", "set", "path"],
                       help="show (default), set key=value, path")

    p_watch = sub.add_parser("watch", help="Watch vault for changes, auto-rebuild")
    p_watch.add_argument("vault_path", nargs="?", help="Vault path (default: from config)")

    sub.add_parser("serve", help="Start MCP server")
    sub.add_parser("install", help="Register skill with Hermes + Trae")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ---- config ----
    if args.command == "config":
        if args.action == "show":
            cfg = load_config()
            print(f"Config: {CONFIG_PATH}")
            for k, v in cfg.items():
                print(f"  {k}: {v}")
            print(f"\nGraph: {resolve_graph_path()}")
        elif args.action == "path":
            print(str(CONFIG_PATH))
        elif args.action == "set":
            print("Usage: vault-graph config show  (edit file manually)")
            print(f"       File: {CONFIG_PATH}")
        return

    if args.command == "install":
        from vault_graph.install import install
        install()
        return

    if args.command == "serve":
        graph_path = resolve_graph_path()
        if not graph_path.exists():
            sys.exit(f"Graph not found: {graph_path}\nRun: vault-graph build")
        from vault_graph.serve import serve
        print(f"MCP server on {graph_path}")
        serve(graph_path)
        return

    if args.command == "build":
        vault_path = getattr(args, "vault_path", None)
        vault, out_dir = resolve_vault_out(vault_path)
        if not vault.is_dir():
            sys.exit(f"Not a directory: {vault}")
        cfg = load_config()
        cfg["vault"] = str(vault)
        cfg["out"] = cfg.get("out", "vault-out")
        save_config(cfg)
        print(f"config: vault={vault}")
        _rebuild(vault, out_dir)
        return

    if args.command == "watch":
        vault_path = getattr(args, "vault_path", None)
        vault, out_dir = resolve_vault_out(vault_path)
        from vault_graph.watch import watch
        _rebuild(vault, out_dir)
        watch(vault, out_dir)
        return

    # Query commands: need graph.json
    graph_path = resolve_graph_path()
    if not graph_path.exists():
        sys.exit(f"Graph not found: {graph_path}\nRun: vault-graph build")

    try:
        import networkx as nx
    except ImportError:
        sys.exit("pip install networkx")

    from vault_graph.query import load_graph, run_query_cmd
    G = load_graph(graph_path)

    cmd = args.command
    if cmd == "god":
        run_query_cmd(G, "god", [])
    elif cmd == "communities":
        run_query_cmd(G, "communities", [])
    elif cmd == "isolated":
        run_query_cmd(G, "isolated", [])
    elif cmd == "stats":
        run_query_cmd(G, "stats", [])
    elif cmd == "search":
        run_query_cmd(G, "search", [args.term])
    elif cmd == "explain":
        run_query_cmd(G, "explain", [args.node])
    elif cmd == "path":
        run_query_cmd(G, "path", [args.a, args.b])
    elif cmd == "query":
        run_query_cmd(G, "query", [args.question])


def _rebuild(vault: Path, out_dir: Path):
    from vault_graph.detect import collect_files
    from vault_graph.extract import extract
    from vault_graph.cache import load_cache, save_cache, split_files
    from vault_graph.security import sanitize_label

    cache_path = out_dir / ".vault_graph_cache.json"
    cache = load_cache(cache_path)

    files = collect_files(vault)
    cached_files, uncached_files, new_cache = split_files(files, cache, vault)

    from vault_graph.trae import trae_available, collect_trae_extractions
    trae_extractions: list[dict] = []
    trae_count = 0
    if trae_available():
        trae_extractions = collect_trae_extractions()
        trae_count = sum(len(e.get("nodes", [])) for e in trae_extractions)

    if len(uncached_files) == 0 and out_dir.joinpath("graph.html").exists() and trae_count == 0:
        print(f"  (all {len(files)} files cached — unchanged)")
        return

    skip_count = len(cached_files)
    print(f"  detect:  {len(files)} vault files ({skip_count} cached, {len(uncached_files)} new)")

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

    if trae_count:
        print(f"  trae:    {trae_count} nodes from ~/.trae/memory/")
        extractions.extend(trae_extractions)

    node_count = sum(len(e.get("nodes", [])) for e in extractions)
    edge_count = sum(len(e.get("edges", [])) for e in extractions)
    print(f"  extract: {node_count} nodes, {edge_count} raw edges")

    old_graph_path = out_dir / "graph.json"
    if old_graph_path.exists() and cached_files:
        import json as _json
        old_data = _json.loads(old_graph_path.read_text())
        for node in old_data.get("nodes", []):
            nid = node.get("id", "")
            rel = str(nid)
            if any(str(cf.relative_to(vault)) == rel for cf in cached_files):
                extractions.append({"nodes": [node], "edges": []})

    from vault_graph.build import build_graph
    G = build_graph(extractions)

    # Classify synthetic nodes (concept:*, trae:*)
    for n in G.nodes():
        if G.nodes[n].get("type", "?") == "?" or G.nodes[n].get("type") is None:
            if str(n).startswith("concept:"):
                G.nodes[n]["type"] = "concept"
            elif str(n).startswith("trae:"):
                G.nodes[n]["type"] = "trae-session"
            elif G.nodes[n].get("type") is None:
                G.nodes[n]["type"] = "other"
    
    print(f"  build:   {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    import networkx as nx
    from vault_graph.cluster import cluster
    G = cluster(G)
    comms = len(set(nx.get_node_attributes(G, "community").values()))
    print(f"  cluster: {comms} communities")

    from vault_graph.analyze import analyze
    analysis = analyze(G)
    print(f"  analyze: {len(analysis['god_nodes'])} god nodes, {len(analysis['isolated_nodes'])} isolated, {len(analysis['surprises'])} surprises")

    from vault_graph.report import render_report
    report_text = render_report(G, analysis)
    print(f"  report:  {len(report_text)} chars")

    from vault_graph.export import export
    export(G, analysis, out_dir, report_text)

    from vault_graph.wiki_export import export_wiki
    export_wiki(G, out_dir, vault)

    from vault_graph.mermaid_export import export_mermaid
    export_mermaid(G, out_dir)

    save_cache(cache_path, new_cache)

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
