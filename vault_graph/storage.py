"""Penyimpanan graph SQLite; Markdown tetap menjadi sumber knowledge."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import networkx as nx


def save_graph(graph: "nx.Graph", path: Path) -> None:
    """Ganti snapshot dalam satu transaksi; kegagalan mempertahankan data lama."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("CREATE TABLE IF NOT EXISTS nodes (id TEXT PRIMARY KEY, attributes TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS edges (source TEXT REFERENCES nodes(id), target TEXT REFERENCES nodes(id), attributes TEXT NOT NULL, PRIMARY KEY(source, target))")
        db.execute("CREATE INDEX IF NOT EXISTS edges_target ON edges(target)")
        db.execute("DELETE FROM edges")
        db.execute("DELETE FROM nodes")
        db.executemany("INSERT INTO nodes VALUES (?, ?)", (
            (node, json.dumps(attrs, ensure_ascii=False))
            for node, attrs in graph.nodes(data=True)
        ))
        db.executemany("INSERT INTO edges VALUES (?, ?, ?)", (
            (source, target, json.dumps(attrs, ensure_ascii=False))
            for source, target, attrs in graph.edges(data=True)
        ))
        db.execute("PRAGMA user_version = 1")


def load_graph(path: Path) -> "nx.Graph":
    """Baca snapshot konsisten, tanpa membuat database kosong saat path salah."""
    import networkx as nx
    graph = nx.Graph()
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.execute("BEGIN")
        for node, attrs in db.execute("SELECT id, attributes FROM nodes"):
            graph.add_node(node, **json.loads(attrs))
        for source, target, attrs in db.execute("SELECT source, target, attributes FROM edges"):
            graph.add_edge(source, target, **json.loads(attrs))
    # ponytail: algoritma tetap NetworkX; gunakan query SQL langsung jika graph melampaui RAM.
    return graph
