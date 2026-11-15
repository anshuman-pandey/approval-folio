"""Disposable non-root deployment and complete approval-history recovery test."""
import io,json,secrets,subprocess,tempfile,time,urllib.request,urllib.error
from pathlib import Path
from pypdf import PdfWriter
ROOT=Path(__file__).resolve().parents[1]
name='folio-test-'+secrets.token_hex(5);volume=name+'-data';restored=name+'-restore';key=secrets.token_urlsafe(32);image='approval-folio-acceptance:local'
def docker(*args):return subprocess.check_output(['docker',*args],text=True).strip()
def call(base,path,token=key,data=None,raw=None,content_type=None):
 headers={'Authorization':'Bearer '+token}
 if data is not None:raw=json.dumps(data).encode();content_type='application/json'
 if content_type:headers['Content-Type']=content_type
 with urllib.request.urlopen(urllib.request.Request(base+path,data=raw,headers=headers),timeout=10) as r:return r.read()
def ready(container):
 base='http://127.0.0.1:'+docker('port',container,'8093/tcp').rsplit(':',1)[1]
 for _ in range(100):
  try:
   with urllib.request.urlopen(base,timeout=1) as r:
    if r.status==200:return base
  except (OSError,urllib.error.URLError):time.sleep(.1)
 raise RuntimeError('Service failed to start')
def start(container,vol):
 docker('run','-d','--name',container,'--read-only','--tmpfs','/tmp:size=32m','--cap-drop=ALL','--security-opt=no-new-privileges:true','-e','APPROVAL_OWNER_KEY='+key,'-v',vol+':/data','-p','127.0.0.1::8093',image)
 return ready(container)
def upload(base,url,expected,payload):
 boundary='folio-test-boundary'
 raw=(f'--{boundary}\r\nContent-Disposition: form-data; name="expected"\r\n\r\n{expected}\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="brand.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode()+payload+f'\r\n--{boundary}--\r\n'.encode())
 return json.loads(call(base,url+'/versions',raw=raw,content_type='multipart/form-data; boundary='+boundary))
try:
 base=start(name,volume);assert docker('exec',name,'id','-u')=='10001'
 writer=PdfWriter();writer.add_blank_page(width=300,height=200);out=io.BytesIO();writer.write(out);payload=out.getvalue()
 created=json.loads(call(base,'/api/projects',data={'title':'Brand review','reviewers':['Designer']}));url='/api/projects/'+created['id'];person=created['reviewers'][0];token=person['token'];review='/api/review/'+created['id']+'/'+person['id']
 first=upload(base,url,0,payload);assert call(base,review+'/versions/1',token)==payload
 call(base,review+'/decisions',token,data={'version':1,'sha256':first['sha256'],'decision':'approved'})
 docker('restart',name);base=ready(name);assert json.loads(call(base,url))['approved'];assert call(base,review+'/versions/1',token)==payload
 docker('stop',name)
 with tempfile.TemporaryDirectory() as tmp:
  source=Path(tmp)/'source.sqlite3';backup=Path(tmp)/'backup.sqlite3';docker('cp',name+':/data/approval.sqlite3',str(source))
  subprocess.run(['python3',str(ROOT/'scripts/backup.py'),str(source),str(backup)],check=True);assert backup.stat().st_mode & 0o777==0o600
  assert subprocess.run(['python3',str(ROOT/'scripts/backup.py'),str(source),str(backup)],capture_output=True).returncode!=0
  docker('volume','create',restored)
  docker('run','--rm','--user','0','-v',restored+':/data','-v',str(backup)+':/backup:ro',image,'python','-c',"import shutil,os;shutil.copyfile('/backup','/data/approval.sqlite3');os.chown('/data/approval.sqlite3',10001,10001);os.chmod('/data/approval.sqlite3',0o600);os.chown('/data',10001,10001)")
  base=start(name+'-restored',restored);assert call(base,review+'/versions/1',token)==payload
  exported=json.loads(call(base,url+'/export'));assert exported['approved'];assert len(exported['history'])==1
  upload(base,url,1,payload);assert not json.loads(call(base,url))['approved']
  try:call(base,review+'/decisions',token,data={'version':1,'sha256':first['sha256'],'decision':'approved'});raise AssertionError('Stale decision accepted')
  except urllib.error.HTTPError as e:assert e.code==400
  call(base,url+'/reviewers/'+person['id']+'/rotate',data={})
  try:call(base,review,token);raise AssertionError('Revoked token worked')
  except urllib.error.HTTPError as e:assert e.code==401
 print('PASS: bounded PDF processing in non-root read-only container; exact bytes, approvals and history survive restart/restore; new version reset, stale rejection and key revocation work after restore')
finally:
 for container in (name,name+'-restored'):subprocess.run(['docker','rm','-f',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for vol in (volume,restored):subprocess.run(['docker','volume','rm',vol],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
