"""Authenticated local API. No public deployment is configured."""
import hmac,io,os,sqlite3
from flask import Flask,g,request,jsonify,send_file,abort
from werkzeug.exceptions import HTTPException
from approvals import Approvals,Invalid,MAX_FILE

def create_app(path,owner_key):
    if not isinstance(owner_key,str) or not owner_key.isascii() or len(owner_key)<32:
        raise ValueError('Set APPROVAL_OWNER_KEY to at least 32 random ASCII characters.')
    app=Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=MAX_FILE+65536,MAX_FORM_MEMORY_SIZE=65536,MAX_FORM_PARTS=3)
    def db():
        if 'db' not in g:g.db=Approvals(path)
        return g.db
    def token():
        value=request.headers.get('Authorization','')
        return value[7:] if value.startswith('Bearer ') else ''
    def owner():
        if not hmac.compare_digest(token().encode(),owner_key.encode()):abort(401,description='Owner access denied.')
    def reviewer(project,person):
        try:db().auth(project,person,token())
        except Invalid:abort(401,description='Reviewer access denied.')
    def data():
        body=request.get_json()
        if not isinstance(body,dict):raise Invalid('Expected a JSON object.')
        return body
    @app.teardown_appcontext
    def close(error):
        store=g.pop('db',None)
        if store:store.close()
    @app.after_request
    def headers(response):
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response
    @app.errorhandler(Invalid)
    def invalid(error):return jsonify(error=str(error)),400
    @app.errorhandler(HTTPException)
    def http_error(error):return jsonify(error=error.description),error.code
    @app.errorhandler(sqlite3.OperationalError)
    def unavailable(error):return jsonify(error='Storage unavailable. Retry shortly.'),503
    @app.get('/')
    def home():return app.send_static_file('index.html')
    @app.get('/api/projects')
    def listing():
        owner();return jsonify([dict(r) for r in db().db.execute('SELECT id,title,latest FROM projects ORDER BY rowid DESC')])
    @app.post('/api/projects')
    def create():
        owner();body=data();project,people=db().create(body.get('title'),body.get('reviewers'))
        return jsonify(id=project,reviewers=people),201
    @app.get('/api/projects/<project>')
    def view(project):owner();return jsonify(db().view(project))
    @app.post('/api/projects/<project>/versions')
    def upload(project):
        owner();file=request.files.get('file');expected=request.form.get('expected','')
        if file is None:raise Invalid('Choose a file.')
        if not expected.isascii() or not expected.isdecimal() or len(expected)>9:raise Invalid('Invalid expected version.')
        return jsonify(db().upload(project,int(expected),file.filename,file.stream.read(MAX_FILE+1))),201
    @app.post('/api/projects/<project>/reviewers/<person>/rotate')
    def rotate(project,person):owner();return jsonify(token=db().rotate(project,person))
    @app.get('/api/projects/<project>/export')
    def export(project):
        owner();return send_file(io.BytesIO(db().export(project).encode()),mimetype='application/json',as_attachment=True,download_name='approval-history.json')
    @app.get('/api/review/<project>/<person>')
    def review(project,person):
        reviewer(project,person);return jsonify(db().view(project))
    @app.get('/api/review/<project>/<person>/versions/<int:version>')
    def download(project,person,version):
        reviewer(project,person)
        file=db().download(project,person,token(),version)
        response=send_file(io.BytesIO(file['data']),mimetype=file['mime'],as_attachment=True,download_name=file['filename'])
        response.headers['X-Content-SHA256']=file['sha256'];return response
    @app.post('/api/review/<project>/<person>/decisions')
    def decide(project,person):
        reviewer(project,person);body=data()
        db().decide(project,person,token(),body.get('version'),body.get('sha256'),body.get('decision'),body.get('note',''))
        return jsonify(ok=True)
    return app

if __name__=='__main__':
    os.umask(0o077)
    create_app(os.environ.get('APPROVAL_DATABASE','approval.sqlite3'),os.environ.get('APPROVAL_OWNER_KEY','')).run(host='127.0.0.1',port=8093)
