"""Version-bound approvals. Owner methods require authentication at the boundary."""
import hashlib,hmac,io,json,secrets,sqlite3,unicodedata,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
from images import image_bytes,Invalid
MAX_FILE=10*1024*1024
MAX_PROJECT=100*1024*1024

def text(value,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any(unicodedata.category(c)=='Cc' and c not in '\n\t' for c in value):raise Invalid('Text is missing, invalid or too long.')
    return value.strip()
def now():return datetime.now(timezone.utc).isoformat()
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def revision(value):
    if type(value) is not int or value<0:raise Invalid('Invalid version number.')
    return value

def document(filename,raw):
    filename=text(filename,200)
    if '/' in filename or '\\' in filename or filename in ('.','..') or any(unicodedata.category(c).startswith('C') for c in filename):raise Invalid('Use a plain filename.')
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_FILE:raise Invalid('File must contain 1 byte to 10 MiB.')
    if filename.lower().endswith('.pdf'):
        try:
            result=subprocess.run([sys.executable,'-I',str(Path(__file__).with_name('pdf_check.py'))],input=raw,capture_output=True,timeout=5,check=True)
            pages=json.loads(result.stdout)['pages']
            if type(pages) is not int or not 1<=pages<=100:raise ValueError('Invalid page count')
        except (subprocess.SubprocessError,OSError,ValueError,KeyError) as e:
            raise Invalid('PDF check failed. Use an unencrypted PDF with 1 to 100 pages within processing limits.') from e
        return filename,'application/pdf',raw
    if not filename.lower().endswith(('.png','.jpg','.jpeg')):raise Invalid('Use a PDF, PNG or JPEG.')
    normalized,_,_=image_bytes(raw)
    return filename.rsplit('.',1)[0]+'.png','image/png',normalized

class Approvals:
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=5);self.db.row_factory=sqlite3.Row;self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,title TEXT,latest INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS reviewers(id TEXT PRIMARY KEY,project TEXT REFERENCES projects(id),name TEXT,token_hash TEXT);
        CREATE TABLE IF NOT EXISTS versions(project TEXT REFERENCES projects(id),number INTEGER,filename TEXT,mime TEXT,data BLOB,sha256 TEXT,created_at TEXT,PRIMARY KEY(project,number));
        CREATE TABLE IF NOT EXISTS downloads(reviewer TEXT REFERENCES reviewers(id),project TEXT,version INTEGER,sha256 TEXT,created_at TEXT,FOREIGN KEY(project,version) REFERENCES versions(project,number));
        CREATE TABLE IF NOT EXISTS decisions(reviewer TEXT REFERENCES reviewers(id),project TEXT,version INTEGER,sha256 TEXT,decision TEXT,note TEXT,created_at TEXT,FOREIGN KEY(project,version) REFERENCES versions(project,number));''')
    def close(self):self.db.close()
    def create(self,title,names):
        title=text(title,200)
        if not isinstance(names,list) or not 1<=len(names)<=20:raise Invalid('Choose 1 to 20 reviewers.')
        names=[text(n,80) for n in names]
        if len(set(n.casefold() for n in names))!=len(names):raise Invalid('Reviewer names must be distinct.')
        project=secrets.token_urlsafe(16);credentials=[]
        with self.db:
            self.db.execute('INSERT INTO projects(id,title) VALUES(?,?)',(project,title))
            for name in names:
                key=secrets.token_urlsafe(16);token=secrets.token_urlsafe(32);self.db.execute('INSERT INTO reviewers VALUES(?,?,?,?)',(key,project,name,digest(token)));credentials.append(dict(id=key,name=name,token=token))
        return project,credentials
    def auth(self,project,reviewer,token):
        row=self.db.execute('SELECT * FROM reviewers WHERE id=? AND project=?',(reviewer,project)).fetchone()
        if row is None or not isinstance(token,str) or not hmac.compare_digest(row['token_hash'],digest(token)):raise Invalid('Reviewer access denied.')
        return row
    def upload(self,project,expected,filename,raw):
        revision(expected);filename,mime,data=document(filename,raw)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT latest FROM projects WHERE id=?',(project,)).fetchone()
            if row is None or row[0]!=expected:raise Invalid('Project changed. Reload before uploading.')
            size=self.db.execute('SELECT COALESCE(sum(length(data)),0) FROM versions WHERE project=?',(project,)).fetchone()[0]
            if size+len(data)>MAX_PROJECT:raise Invalid('Project storage limit reached (100 MiB including history).')
            version=expected+1;sha=hashlib.sha256(data).hexdigest()
            self.db.execute('INSERT INTO versions VALUES(?,?,?,?,?,?,?)',(project,version,filename,mime,data,sha,now()))
            self.db.execute('UPDATE projects SET latest=? WHERE id=?',(version,project))
        return dict(version=version,sha256=sha)
    def download(self,project,reviewer,token,version):
        revision(version)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE');self.auth(project,reviewer,token)
            row=self.db.execute('SELECT filename,mime,data,sha256 FROM versions WHERE project=? AND number=?',(project,version)).fetchone()
            if row is None:raise Invalid('Version not found.')
            self.db.execute('INSERT INTO downloads VALUES(?,?,?,?,?)',(reviewer,project,version,row['sha256'],now()))
        return dict(row)
    def decide(self,project,reviewer,token,version,sha,decision,note=''):
        revision(version)
        if decision not in ('approved','changes_requested'):raise Invalid('Invalid decision.')
        if decision=='changes_requested':note=text(note,4000)
        elif not isinstance(note,str) or len(note)>4000 or '\x00' in note:raise Invalid('Invalid note.')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE');self.auth(project,reviewer,token)
            latest=self.db.execute('SELECT latest FROM projects WHERE id=?',(project,)).fetchone()[0]
            row=self.db.execute('SELECT sha256 FROM versions WHERE project=? AND number=?',(project,version)).fetchone()
            if version!=latest or row is None or not isinstance(sha,str) or not hmac.compare_digest(row[0],sha):raise Invalid('This is not the current file. Download and review the latest version.')
            seen=self.db.execute('SELECT 1 FROM downloads WHERE reviewer=? AND project=? AND version=? AND sha256=?',(reviewer,project,version,sha)).fetchone()
            if seen is None:raise Invalid('Download this version before submitting a decision.')
            self.db.execute('INSERT INTO decisions VALUES(?,?,?,?,?,?,?)',(reviewer,project,version,sha,decision,note,now()))
    def rotate(self,project,reviewer):
        token=secrets.token_urlsafe(32)
        with self.db:
            if not self.db.execute('UPDATE reviewers SET token_hash=? WHERE id=? AND project=?',(digest(token),reviewer,project)).rowcount:raise Invalid('Reviewer not found.')
        return token
    def view(self,project):
        row=self.db.execute('SELECT * FROM projects WHERE id=?',(project,)).fetchone()
        if row is None:raise Invalid('Project not found.')
        result=dict(row);result['versions']=[dict(v) for v in self.db.execute('SELECT number,filename,mime,sha256,created_at FROM versions WHERE project=? ORDER BY number',(project,))];result['reviewers']=[]
        for reviewer in self.db.execute('SELECT id,name FROM reviewers WHERE project=? ORDER BY rowid',(project,)):
            decision=self.db.execute('SELECT decision,note,created_at FROM decisions WHERE reviewer=? AND project=? AND version=? ORDER BY rowid DESC LIMIT 1',(reviewer['id'],project,row['latest'])).fetchone()
            result['reviewers'].append(dict(reviewer,decision=dict(decision) if decision else None))
        result['approved']=bool(row['latest']) and all(r['decision'] and r['decision']['decision']=='approved' for r in result['reviewers'])
        return result
    def export(self,project):
        result=self.view(project);result['history']=[dict(r) for r in self.db.execute('SELECT reviewer,version,sha256,decision,note,created_at FROM decisions WHERE project=? ORDER BY rowid',(project,))]
        return json.dumps(result,ensure_ascii=False,indent=2)
