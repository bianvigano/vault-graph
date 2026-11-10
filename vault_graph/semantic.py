"""Multilingual semantic retrieval with automatic model selection."""
from __future__ import annotations
import json, math, sqlite3
from pathlib import Path

MODELS = {'small': 'intfloat/multilingual-e5-small', 'base': 'intfloat/multilingual-e5-base', 'large': 'intfloat/multilingual-e5-large'}

def available_memory_gb() -> float:
    try:
        return int(Path('/proc/meminfo').read_text().split('MemAvailable:')[1].split()[0]) / 1024 / 1024
    except (FileNotFoundError, IndexError, ValueError):
        return 4.0

def choose_model(database: Path, requested: str | None = None) -> tuple[str, str]:
    if requested and requested not in MODELS:
        raise ValueError('Model harus small, base, atau large')
    if requested:
        return requested, 'dipilih manual'
    with sqlite3.connect(database) as db:
        count, chars = db.execute('SELECT count(*), coalesce(sum(length(content)),0) FROM documents').fetchone()
    ram = available_memory_gb()
    # ponytail: automatic mode favors completion on CPU; large remains manual.
    if ram >= 8:
        return 'small', f'RAM {ram:.1f} GB; {count} dokumen; mode otomatis CPU'
    return 'small', f'RAM {ram:.1f} GB; {count} dokumen'

def _model(name: str):
    from sentence_transformers import SentenceTransformer
    import torch
    torch.set_num_threads(4)
    encoder = SentenceTransformer(MODELS[name], device='cpu')
    class Encoder:
        def embed(self, texts):
            return iter(encoder.encode(texts, batch_size=4, normalize_embeddings=True))
    return Encoder()

def index_embeddings(database: Path, requested: str | None = None) -> dict:
    selected, reason = choose_model(database, requested)
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE IF NOT EXISTS document_embeddings (path TEXT PRIMARY KEY, vector TEXT NOT NULL, model TEXT NOT NULL)')
        rows = db.execute('SELECT path, title || char(10) || content FROM documents').fetchall()
        current = db.execute('SELECT DISTINCT model FROM document_embeddings').fetchall()
        if current and current != [(MODELS[selected],)]:
            db.execute('DELETE FROM document_embeddings')
        if not rows:
            return {'count': 0, 'model': selected, 'reason': reason}
        model = _model(selected)
        for start in range(0, len(rows), 16):
            batch = rows[start:start + 16]
            vectors = model.embed(['passage: ' + text for _, text in batch])
            db.executemany('INSERT OR REPLACE INTO document_embeddings VALUES (?, ?, ?)', ((path, json.dumps(vector.tolist()), MODELS[selected]) for (path, _), vector in zip(batch, vectors)))
    return {'count': len(rows), 'model': selected, 'reason': reason}

def retrieve_semantic(database: Path, query: str, limit: int = 5) -> dict:
    if not query.strip():
        raise ValueError('Query kosong')
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
        rows = db.execute('SELECT e.path,e.vector,e.model,d.title,d.content FROM document_embeddings e JOIN documents d ON d.path=e.path').fetchall()
    if not rows:
        return {'query': query, 'results': [], 'mode': 'semantic'}
    model_name = next(iter(rows))[2].split('/')[-1]
    name = {'multilingual-e5-small': 'small', 'multilingual-e5-base': 'base', 'multilingual-e5-large': 'large'}[model_name]
    q = next(_model(name).embed(['query: ' + query]))
    qnorm = math.sqrt(sum(x*x for x in q)) or 1
    scored = []
    for path, raw, _, title, content in rows:
        vector = json.loads(raw)
        norm = math.sqrt(sum(x*x for x in vector)) or 1
        scored.append((sum(a*b for a,b in zip(q, vector)) / (qnorm * norm), path, title, ' '.join(content.split())[:700]))
    scored.sort(reverse=True)
    return {'query': query, 'mode': 'semantic', 'model': model_name, 'results': [{'source': p, 'citation': f'[vault: {p}]', 'title': t, 'excerpt': e, 'score': round(float(s), 5)} for s, p, t, e in scored[:limit]], 'notice': 'Hasil semantic multilingual; tetap verifikasi sumber.'}
