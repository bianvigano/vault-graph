"""Benchmark the stored semantic index and validate model selection."""
import time
from pathlib import Path
from vault_graph.semantic import choose_model, retrieve_semantic

DB = Path('/home/the-meh/vault/vault-out/graph.db')
name, reason = choose_model(DB)
assert name in {'small', 'base', 'large'}
queries = ['cara mengatur server Minecraft', 'cara memakai memory Hermes', 'pengaturan bahasa Indonesia']
started = time.perf_counter()
for query in queries:
    result = retrieve_semantic(DB, query, limit=3)
    assert result['results'], query
elapsed = time.perf_counter() - started
print(f'model={name} reason={reason}')
print(f'queries={len(queries)} elapsed={elapsed:.2f}s avg={elapsed / len(queries):.2f}s')
print('PASS: semantic benchmark and automatic model selection')
