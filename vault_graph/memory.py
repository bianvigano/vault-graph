"""Deterministic local candidates, not LLM extraction or verified truth."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / '.local/share/vault-graph/memory.db'
LIMITS = 'Kandidat lokal deterministik; bukan LLM/semantic atau kebenaran terverifikasi. Tanggal fakta hanya dari konten.'


def namespace(vault):
    return str(Path(vault).expanduser().resolve(strict=True))


def _db(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    # Keep the legacy table intact: lost predicates cannot be reliably reconstructed.
    db.execute('''CREATE TABLE IF NOT EXISTS memory_facts (
        id TEXT PRIMARY KEY, namespace TEXT NOT NULL, fact TEXT NOT NULL,
        subject TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
        date TEXT, kind TEXT NOT NULL, mode TEXT NOT NULL, candidate INTEGER NOT NULL,
        first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
        forgotten INTEGER NOT NULL DEFAULT 0)''')
    db.execute('''CREATE TABLE IF NOT EXISTS memory_sources (
        id TEXT NOT NULL, source TEXT NOT NULL, line INTEGER NOT NULL,
        seen TEXT NOT NULL, active INTEGER NOT NULL, PRIMARY KEY(id,source,line))''')
    db.execute('CREATE TABLE IF NOT EXISTS memory_meta (key TEXT PRIMARY KEY, value TEXT)')
    return db


def _norm(text):
    return ' '.join(text.split()).casefold()


def extract(text):
    """Yield line and intact assertion; skip fenced code, quotations and headings."""
    fence = None
    for line, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith(('```', '~~~')):
            token = stripped[:3]
            fence = None if fence == token else token if fence is None else fence
            continue
        if fence or stripped.startswith(('>', '#', '<!--')):
            continue
        assertion = re.sub(r'^\s*[-*+]\s+', '', raw).strip()
        if assertion.startswith('memory:'):
            try:
                obj = json.loads(assertion[7:].strip())
                if not isinstance(obj, dict) or set(obj) - {'subject','key','value','date','kind','mode'}:
                    continue
                if any(not isinstance(obj.get(k), str) or not obj[k].strip() for k in ('subject','key','value')):
                    continue
                if obj.get('date') is not None:
                    date.fromisoformat(obj['date'])
                if obj.get('kind', 'dynamic') not in ('static', 'dynamic') or obj.get('mode', 'update') not in ('update', 'extends'):
                    continue
                yield line, dict(fact=f"{obj['subject']} | {obj['key']} | {obj['value']}", subject=obj['subject'], key=obj['key'], value=obj['value'], date=obj.get('date'), kind=obj.get('kind','dynamic'), mode=obj.get('mode','update'), candidate=0)
            except (ValueError, TypeError):
                continue
        elif re.match(r'(?i)^(user|pengguna|saya|aku|i)\s+(?:(?:tidak|tak|not|do not|does not|don\x27t|doesn\x27t)\s+)?(?:prefers?|ingin|suka|menggunakan|pakai|memakai|tolak|mau|sedang|currently|use|uses|want|work|bekerja|tinggal)\b', assertion):
            subject = assertion.split()[0]
            dynamic = bool(re.search(r'(?i)\b(sedang|sekarang|saat ini|currently|proyek|project|sementara|hari ini)\b', assertion))
            # ponytail: natural-language assertions remain opaque candidates; use explicit keys for reliable updates.
            yield line, dict(fact=assertion, subject=subject, key='', value=assertion, date=None, kind='dynamic' if dynamic else 'static', mode='update', candidate=1)


def build(path, vault):
    from vault_graph.detect import collect_files
    root = Path(namespace(vault))
    if not root.is_dir():
        raise ValueError('Vault harus direktori')
    # Read everything before modifying state: unreadable sources must not silently retire facts.
    sources = [(f, f.read_text(encoding='utf-8')) for f in sorted(collect_files(root)) if f.resolve().is_relative_to(root)]
    now = datetime.now(timezone.utc).isoformat()
    with _db(path) as db:
        # Non-destructive migration: retain raw old rows, quarantine incomplete candidates.
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='memories'").fetchone() and not db.execute("SELECT 1 FROM memory_meta WHERE key='legacy_preserved'").fetchone():
            db.execute("INSERT INTO memory_meta VALUES ('legacy_preserved','Legacy memories retained unchanged; rebuild source to restore predicates/provenance')")
        db.execute('UPDATE memory_facts SET active=0 WHERE namespace=?', (str(root),))
        db.execute('UPDATE memory_sources SET active=0 WHERE id IN (SELECT id FROM memory_facts WHERE namespace=?)', (str(root),))
        ids = set()
        for source, text in sources:
            for line, fact in extract(text):
                identity = [str(root)] + [_norm(str(fact[k])) for k in ('subject','key','value','date','kind','mode','candidate')]
                ident = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]
                ids.add(ident)
                db.execute('''INSERT INTO memory_facts (id,namespace,fact,subject,key,value,date,kind,mode,candidate,first_seen,last_seen)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen,active=1''',
                    (ident,str(root),*[fact[k] for k in ('fact','subject','key','value','date','kind','mode','candidate')],now,now))
                db.execute('INSERT INTO memory_sources VALUES (?,?,?,?,1) ON CONFLICT(id,source,line) DO UPDATE SET seen=excluded.seen,active=1', (ident,str(source),line,now))
    return len(ids)


def _validate(limit):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit harus integer 1–100')


def records(path, vault):
    ns = namespace(vault)
    with _db(path) as db:
        rows = [dict(r) for r in db.execute('SELECT * FROM memory_facts WHERE namespace=? ORDER BY first_seen,id', (ns,))]
        for row in rows:
            row['sources'] = [dict(s) for s in db.execute('SELECT source,line,seen,active FROM memory_sources WHERE id=? ORDER BY source,line', (row['id'],))]
    for row in rows:
        row['relations'] = []
        row['status'] = 'forgotten' if row['forgotten'] else 'stale' if not row['active'] else 'candidate' if row['candidate'] else 'current'
        if row['candidate'] or row['status'] in ('forgotten','stale'):
            continue
        peers = [p for p in rows if p['id'] != row['id'] and not p['candidate'] and p['active'] and not p['forgotten'] and (_norm(p['subject']),_norm(p['key'])) == (_norm(row['subject']),_norm(row['key']))]
        for peer in peers:
            if _norm(peer['value']) == _norm(row['value']):
                continue
            if row['date'] and peer['date'] and row['date'] != peer['date']:
                newer = row['date'] > peer['date']
                latest = row if newer else peer
                relation = 'extends' if latest['mode'] == 'extends' else 'updates'
                row['relations'].append({'type': relation if newer else ('extended_by' if relation == 'extends' else 'updated_by'), 'id': peer['id']})
                if not newer and relation == 'updates':
                    row['status'] = 'superseded'
            else:
                row['relations'].append({'type':'conflicts','id':peer['id']})
                if row['status'] != 'superseded':
                    row['status'] = 'conflict'
    return rows


def profile(path, vault, limit=50):
    _validate(limit)
    rows = records(path, vault)
    current = [r for r in rows if r['status'] in ('current','candidate','conflict')]
    return {'static':[r for r in current if r['kind']=='static'][:limit], 'dynamic':[r for r in current if r['kind']=='dynamic'][:limit], 'history':[r for r in rows if r['status'] not in ('current','candidate','conflict')][:limit], 'count':len(current), 'limits':LIMITS}


def forget(path, vault, ident):
    if not isinstance(ident,str) or not re.fullmatch('[0-9a-f]{24}',ident):
        raise ValueError('id harus 24 karakter hex dari profile/recall')
    with _db(path) as db:
        changed = db.execute('UPDATE memory_facts SET forgotten=1 WHERE namespace=? AND id=?', (namespace(vault),ident)).rowcount
    return {'forgotten':bool(changed), 'id':ident}


def recall(path, query, vault, limit=10, graph_path=None):
    _validate(limit)
    if not isinstance(query,str) or not query.strip() or len(query)>4096:
        raise ValueError('query harus teks tidak kosong, maksimal 4096 karakter')
    terms = set(re.findall(r'\w+',query.casefold()))
    rows = [r for r in records(path,vault) if r['status'] in ('current','candidate','conflict')]
    for row in rows:
        row['score'] = len(terms & set(re.findall(r'\w+',row['fact'].casefold())))
    result = {'method':'lexical', 'memories':sorted([r for r in rows if r['score']],key=lambda r:(-r['score'],r['id']))[:limit], 'documents':[], 'limits':LIMITS}
    if graph_path and Path(graph_path).exists():
        from vault_graph.retrieval import retrieve
        try:
            docs = retrieve(Path(graph_path),query,min(limit,10))
            # Retrieval index may belong to another vault; never return cross-root sources.
            root = Path(namespace(vault))
            verified = []
            for doc in docs['results']:
                source = (root / doc['source']).resolve()
                if source.is_relative_to(root) and source.is_file():
                    # Verify indexed content against the actual root, not relative names alone.
                    with sqlite3.connect(graph_path) as index:
                        digest = index.execute('SELECT digest FROM documents WHERE path=?', (doc['source'],)).fetchone()
                    if digest and hashlib.sha256(source.read_bytes()).hexdigest() == digest[0]:
                        verified.append(dict(doc, source=str(source), namespace=str(root)))
            result['documents'] = verified
            result['document_note'] = 'Dokumen hanya disertakan jika provenance indeks cocok root; tanpa konteks graph tambahan.'
        except (sqlite3.Error, ValueError) as exc:
            result['document_note'] = str(exc)
    return result


def tools():
    return [{'name':'memory','description':'Build deterministic local memory candidates (not LLM); preserves history.', 'inputSchema':{'type':'object','properties':{},'additionalProperties':False}},
            {'name':'profile','description':'Static/dynamic candidates and history.', 'inputSchema':{'type':'object','properties':{'limit':{'type':'integer','minimum':1,'maximum':100}},'additionalProperties':False}},
            {'name':'recall','description':'Lexical memory + document recall with provenance (not semantic).', 'inputSchema':{'type':'object','properties':{'query':{'type':'string','minLength':1,'maxLength':4096},'limit':{'type':'integer','minimum':1,'maximum':100}},'required':['query'],'additionalProperties':False}},
            {'name':'forget','description':'Soft-forget a memory ID, persistent across rebuild.', 'inputSchema':{'type':'object','properties':{'id':{'type':'string','pattern':'^[0-9a-f]{24}$'}},'required':['id'],'additionalProperties':False}}]


def call(name,args,path,vault,graph_path=None):
    if not isinstance(args,dict):
        raise ValueError('arguments harus object')
    allowed = {'memory':set(),'profile':{'limit'},'recall':{'query','limit'},'forget':{'id'}}
    if name not in allowed or set(args)-allowed[name]:
        raise ValueError('Tool/argumen tidak dikenal')
    if name == 'memory':
        return {'indexed':build(path,vault),'limits':LIMITS}
    if name == 'profile':
        return profile(path,vault,args.get('limit',50))
    if name == 'forget':
        return forget(path,vault,args.get('id'))
    return recall(path,args.get('query'),vault,args.get('limit',10),graph_path)
