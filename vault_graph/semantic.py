"""Multilingual semantic retrieval with resource-aware model selection and chunks."""
from __future__ import annotations
import json, sqlite3, time
from functools import lru_cache
from pathlib import Path

MODELS = {'small': 'intfloat/multilingual-e5-small', 'base': 'intfloat/multilingual-e5-base', 'large': 'intfloat/multilingual-e5-large'}
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180

def available_memory_gb() -> float:
    try:
        return int(Path('/proc/meminfo').read_text().split('MemAvailable:')[1].split()[0]) / 1024 / 1024
    except (FileNotFoundError, IndexError, ValueError):
        return 4.0

def has_cuda() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except ImportError:
        return False

def choose_model(database: Path, requested: str | None = None) -> tuple[str, str]:
    if requested and requested not in MODELS:
        raise ValueError('Model harus small, base, atau large')
    with sqlite3.connect(database) as db:
        count = db.execute('SELECT count(*) FROM documents').fetchone()[0]
    ram = available_memory_gb()
    cuda = has_cuda()
    if requested:
        return requested, f'dipilih manual; RAM {ram:.1f} GB; CUDA {cuda}'
    if cuda and ram >= 16 and count <= 5000:
        return 'large', f'CUDA tersedia; RAM {ram:.1f} GB; {count} dokumen'
    if ram >= 16 and count <= 5000:
        return 'base', f'RAM {ram:.1f} GB; {count} dokumen; CPU'
    return 'small', f'RAM {ram:.1f} GB; {count} dokumen; mode hemat'

@lru_cache(maxsize=1)
def _model(name: str):
    from sentence_transformers import SentenceTransformer
    import torch
    torch.set_num_threads(min(4, torch.get_num_threads()))
    return SentenceTransformer(MODELS[name], device='cuda' if has_cuda() else 'cpu')

def _chunks(text: str, tokenizer):
    encoded = tokenizer(text, add_special_tokens=False, truncation=False)['input_ids']
    size, overlap = 440, 64
    for start in range(0, len(encoded), size - overlap):
        ids = encoded[start:start + size]
        part = tokenizer.decode(ids, skip_special_tokens=True).strip()
        if part:
            yield part
        if start + size >= len(encoded):
            break


def index_embeddings(database: Path, requested: str | None = None) -> dict:
    selected, reason = choose_model(database, requested)
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE IF NOT EXISTS document_chunks (id INTEGER PRIMARY KEY, path TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, UNIQUE(path, id))')
        db.execute('CREATE TABLE IF NOT EXISTS chunk_embeddings (chunk_id INTEGER PRIMARY KEY, vector TEXT NOT NULL, model TEXT NOT NULL)')
        db.execute('DELETE FROM document_chunks'); db.execute('DELETE FROM chunk_embeddings')
        docs = db.execute('SELECT path,title,content FROM documents').fetchall()
        if not docs:
            return {'documents': 0, 'chunks': 0, 'model': selected, 'reason': reason}
        encoder = _model(selected)
        chunks = [(path, title, part) for path, title, content in docs for part in _chunks(content, encoder.tokenizer)]
        db.executemany('INSERT INTO document_chunks(path,title,content) VALUES (?,?,?)', chunks)
        if not chunks:
            return {'documents': len(docs), 'chunks': 0, 'model': selected, 'reason': reason}
        started = time.perf_counter()
        encoder.encode(['passage: ' + item[2] for item in chunks[:4]], batch_size=4, normalize_embeddings=True)
        seconds_per_chunk = (time.perf_counter() - started) / min(4, len(chunks))
        estimate = seconds_per_chunk * len(chunks)
        if requested is None and estimate > 600 and selected != 'small':
            selected = 'base' if selected == 'large' else 'small'
            reason += f'; estimasi {estimate:.0f} detik melewati 600 detik, turun ke {selected}'
            encoder = _model(selected)
        print(f'Model {selected}: {reason}; sampel {seconds_per_chunk:.3f} detik/chunk', flush=True)
        for start in range(0, len(chunks), 16):
            ids = db.execute('SELECT id FROM document_chunks ORDER BY id LIMIT ? OFFSET ?', (len(chunks[start:start+16]), start)).fetchall()
            vectors = encoder.encode(['passage: ' + text for _, _, text in chunks[start:start+16]], batch_size=4, normalize_embeddings=True)
            db.executemany('INSERT INTO chunk_embeddings VALUES (?,?,?)', ((row[0], json.dumps(vector.tolist()), MODELS[selected]) for row, vector in zip(ids, vectors)))
    return {'documents': len(docs), 'chunks': len(chunks), 'model': selected, 'reason': reason}

def retrieve_semantic(database: Path, query: str, limit: int = 5, requested: str | None = None) -> dict:
    if not isinstance(query, str) or not query.strip() or len(query) > 2000:
        raise ValueError('Query harus berisi 1–2000 karakter')
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError('Limit harus 1–10')
    if requested is not None and requested not in MODELS:
        raise ValueError('Model harus small, base, atau large')
    if not database.is_file():
        raise ValueError('Database belum tersedia')
    if requested is not None:
        with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
            stored = db.execute('SELECT DISTINCT model FROM chunk_embeddings').fetchall()
        if stored != [(MODELS[requested],)]:
            raise ValueError(f'Jalankan build --model {requested} dahulu; query tidak mengubah indeks')
    # Chunk input is untrusted reference data, never executable instructions.
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
        rows = db.execute('SELECT c.path,c.title,c.content,e.vector,e.model FROM document_chunks c JOIN chunk_embeddings e ON e.chunk_id=c.id').fetchall()
    if not rows: return {'query': query, 'results': [], 'mode': 'semantic'}
    model_name = rows[0][4].split('/')[-1]
    name = next((key for key, value in MODELS.items() if value.endswith(model_name)), None)
    if requested and requested != name: raise ValueError(f'Index memakai model {name}; jalankan build ulang dengan --model {requested}')
    import numpy as np
    q = _model(name).encode(['query: ' + query], normalize_embeddings=True)[0]
    scored = []
    for path, title, content, raw, _ in rows:
        score = float(np.dot(q, np.asarray(json.loads(raw), dtype='float32')))
        scored.append((score, path, title, content))
    scored.sort(reverse=True)
    return {'query': query, 'mode': 'semantic', 'model': model_name, 'chunks': len(rows), 'results': [{'source': p, 'citation': f'[vault: {p}]', 'title': t, 'excerpt': e, 'score': round(s, 5)} for s, p, t, e in scored[:limit]], 'notice': 'Hasil semantic multilingual; tetap verifikasi sumber.'}
