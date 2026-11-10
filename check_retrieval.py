"""Run: uv run python check_retrieval.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from vault_graph.retrieval import index_documents, retrieve

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    note = root / 'solution.md'
    note.write_text('# Perbaikan Folia\nGunakan scheduler regional untuk entitas Folia.', encoding='utf-8')
    db = root / 'test.db'
    assert index_documents(db, root, [note]) == 1
    result = retrieve(db, 'scheduler Folia')
    assert result['results'][0]['source'] == 'solution.md'
    assert 'regional' in result['results'][0]['excerpt']
    assert retrieve(db, 'xyznotpresent')['results'] == []
    note.unlink()
    index_documents(db, root, [])
    assert retrieve(db, 'Folia')['results'] == []

requests = [
    {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize'},
    {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
    {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'graph_retrieve_context', 'arguments': {'query': 'Minecraft'}}},
]
process = subprocess.run([sys.executable, '-m', 'vault_graph.main', 'serve'], input='\n'.join(map(json.dumps, requests))+'\n', text=True, capture_output=True, check=True)
responses = [json.loads(line) for line in process.stdout.splitlines()]
assert len(responses) == 3
assert any(t['name'] == 'graph_retrieve_context' for t in responses[1]['result']['tools'])
context = json.loads(responses[2]['result']['content'][0]['text'])
assert context['results'] and context['results'][0]['citation'].startswith('[vault: ')
print('PASS: retrieval, citation, no-match, deletion, MCP initialize/list/retrieve')
