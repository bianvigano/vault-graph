"""Benchmark actual stored-model latency and source relevance."""
import sqlite3
import time
from pathlib import Path
from vault_graph.semantic import choose_model, retrieve_semantic

DB = Path('/home/the-meh/vault/vault-out/graph.db')
with sqlite3.connect(DB) as db:
    stored = db.execute('SELECT DISTINCT model FROM chunk_embeddings').fetchall()
assert len(stored) == 1, stored
stored_model = stored[0][0].split('/')[-1]
queries = [
    ('cara mengatur server Minecraft', 'minecraft/'),
    ('cara memakai memory Hermes', 'hermes'),
    ('pengaturan bahasa Indonesia', None),
]
started = time.perf_counter()
results = []
for query, expected in queries:
    result = retrieve_semantic(DB, query, limit=5)
    assert result['results'], query
    if expected:
        assert any(expected in item['source'].lower() for item in result['results']), (query, result['results'])
    results.append(result)
elapsed = time.perf_counter() - started
recommended, reason = choose_model(DB)
print(f'stored_model={stored_model}')
print(f'recommended_model={recommended} reason={reason}')
print(f'queries={len(queries)} elapsed={elapsed:.2f}s avg={elapsed / len(queries):.2f}s')
print('PASS: actual model, latency, and source-relevance benchmark')
