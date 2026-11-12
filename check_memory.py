"""Run: uv run python check_memory.py"""
import json
import sqlite3
import tempfile
from pathlib import Path
from vault_graph import memory as m

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    a, b = root/'a', root/'b'
    a.mkdir(); b.mkdir()
    db = root/'memory.db'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE memories (id INTEGER PRIMARY KEY, fact TEXT, source TEXT, mtime_ns INTEGER)')
        conn.execute("INSERT INTO memories VALUES (1,'old','old.md',1)")
    def fact(value, day, mode='update'):
        return 'memory: '+json.dumps(dict(subject='User',key='editor',value=value,date=day,kind='dynamic',mode=mode))
    text = '\n'.join(['User does not want coffee.', 'User does not want coffee.', 'Pengguna sedang bekerja pada proyek.', fact('vim','2026-01-01'),fact('emacs','2026-02-01'),fact('nano','2026-03-01','extends'),fact('code','2026-03-01')])
    source = a/'note.md'
    source.write_text(text)
    assert m.build(db,a)==6
    rows = m.records(db,a)
    neg = next(r for r in rows if 'does not' in r['fact'])
    assert len(neg['sources'])==2
    assert any(r['status']=='superseded' for r in rows)
    assert any(any(x['type']=='extends' for x in r['relations']) for r in rows)
    assert any(r['status']=='conflict' for r in rows)
    assert m.profile(db,a)['dynamic']
    assert m.recall(db,'coffee',a)['memories']
    assert m.forget(db,a,neg['id'])['forgotten']
    m.build(db,a)
    assert not m.recall(db,'coffee',a)['memories']
    assert not m.profile(db,b)['count']
    source.write_text('User prefers water.')
    m.build(db,a)
    assert any(r['status']=='stale' for r in m.records(db,a))
    for name,args in [('recall',{}),('profile',{'limit':True}),('forget',{'id':'bad'}),('memory',{'unknown':1})]:
        try:
            m.call(name,args,db,a)
        except ValueError:
            pass
        else:
            raise AssertionError((name,args))
    assert m.call('memory',{},db,a)['indexed']==1
    assert m.call('profile',{},db,a)['count']==1
    assert m.call('recall',{'query':'water'},db,a)['memories']
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0]==1
print('PASS extraction, negation, dedup, dynamic, updates/extends/conflict, stale, tombstones, namespaces, migration, tool validation')
