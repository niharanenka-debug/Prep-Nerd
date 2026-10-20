import sqlite3, json
from pathlib import Path
class Database:
    def __init__(self,path): self.path=str(path); self.init()
    def conn(self): c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; return c
    def init(self):
        with self.conn() as c:
            c.executescript("""CREATE TABLE IF NOT EXISTS sources(id INTEGER PRIMARY KEY,title TEXT,kind TEXT,content TEXT,source_ref TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS artifacts(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,payload TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS mistakes(id INTEGER PRIMARY KEY,payload TEXT,status TEXT DEFAULT 'Needs More Practice',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""")
    def add_source(self,title,kind,content,ref=''):
        with self.conn() as c: return c.execute('INSERT INTO sources(title,kind,content,source_ref) VALUES(?,?,?,?)',(title,kind,content,ref)).lastrowid
    def sources(self):
        with self.conn() as c:return [dict(x) for x in c.execute('SELECT * FROM sources ORDER BY id DESC').fetchall()]
    def save(self,kind,title,payload):
        with self.conn() as c:return c.execute('INSERT INTO artifacts(kind,title,payload) VALUES(?,?,?)',(kind,title,json.dumps(payload))).lastrowid
    def artifacts(self,kind=None):
        with self.conn() as c:
            q='SELECT * FROM artifacts'; args=()
            if kind:q+=' WHERE kind=?';args=(kind,)
            q+=' ORDER BY id DESC'; return [dict(x) for x in c.execute(q,args).fetchall()]
    def add_mistake(self,payload):
        with self.conn() as c:return c.execute('INSERT INTO mistakes(payload,status) VALUES(?,?)',(json.dumps(payload),payload.get('status','Needs More Practice'))).lastrowid
    def mistakes(self):
        with self.conn() as c:return [dict(x, payload=json.loads(x['payload'])) for x in c.execute('SELECT * FROM mistakes ORDER BY id DESC').fetchall()]
    def update_mistake(self,i,status):
        with self.conn() as c:c.execute('UPDATE mistakes SET status=? WHERE id=?',(status,i))
    def delete(self,table,i):
        if table not in {'sources','artifacts','mistakes'}: raise ValueError('invalid table')
        with self.conn() as c:c.execute(f'DELETE FROM {table} WHERE id=?',(i,))
