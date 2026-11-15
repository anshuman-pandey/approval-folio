import io,tempfile,unittest
from server import create_app
from test_approvals import png

class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.owner={'Authorization':'Bearer '+'x'*48};self.client=create_app(self.tmp.name+'/db','x'*48).test_client()
  r=self.client.post('/api/projects',headers=self.owner,json={'title':'Brand','reviewers':['Design','Legal']});self.assertEqual(r.status_code,201)
  self.project=r.json['id'];self.people=r.json['reviewers'];self.base='/api/projects/'+self.project
 def tearDown(self):self.tmp.cleanup()
 def headers(self,n=0):return {'Authorization':'Bearer '+self.people[n]['token']}
 def review(self,n=0):return '/api/review/'+self.project+'/'+self.people[n]['id']
 def upload(self,expected='0'):
  return self.client.post(self.base+'/versions',headers=self.owner,data={'expected':expected,'file':(io.BytesIO(png()),'sample.png')})
 def test_complete_consensus_and_new_version_reset(self):
  file=self.upload();self.assertEqual(file.status_code,201)
  decision=dict(version=1,sha256=file.json['sha256'],decision='approved')
  for n in range(2):
   denied=self.client.post(self.review(n)+'/decisions',headers=self.headers(n),json=decision);self.assertEqual(denied.status_code,400)
   downloaded=self.client.get(self.review(n)+'/versions/1',headers=self.headers(n));self.assertEqual(downloaded.status_code,200);self.assertIn('attachment',downloaded.headers['Content-Disposition']);self.assertEqual(downloaded.headers['X-Content-SHA256'],decision['sha256'])
   self.assertEqual(self.client.post(self.review(n)+'/decisions',headers=self.headers(n),json=decision).status_code,200)
  self.assertTrue(self.client.get(self.base,headers=self.owner).json['approved'])
  self.assertEqual(self.upload('1').status_code,201)
  self.assertFalse(self.client.get(self.base,headers=self.owner).json['approved'])
  self.assertEqual(self.client.post(self.review()+'/decisions',headers=self.headers(),json=decision).status_code,400)
 def test_owner_routes_deny_reviewer_and_missing_credentials(self):
  for headers in ({},self.headers()):
   for method,path in [('get','/api/projects'),('get',self.base),('get',self.base+'/export'),('post',self.base+'/versions'),('post',self.base+'/reviewers/'+self.people[0]['id']+'/rotate'),('post','/api/projects')]:
    self.assertEqual(getattr(self.client,method)(path,headers=headers).status_code,401)
 def test_reviewer_scope_rotation_and_no_query_credentials(self):
  self.upload()
  self.assertEqual(self.client.get(self.review(1),headers=self.headers()).status_code,401)
  self.assertEqual(self.client.get(self.review()+'?token='+self.people[0]['token']).status_code,401)
  fresh=self.client.post(self.base+'/reviewers/'+self.people[0]['id']+'/rotate',headers=self.owner).json['token']
  self.assertEqual(self.client.get(self.review()+'/versions/1',headers=self.headers()).status_code,401)
  self.assertEqual(self.client.get(self.review(),headers={'Authorization':'Bearer '+fresh}).status_code,200)
 def test_malformed_requests_and_stale_upload(self):
  for body in [[],None,'bad']:
   self.assertIn(self.client.post('/api/projects',headers=self.owner,json=body).status_code,[400,415])
  for version in ['true','-1','1.0','99999999999']:
   self.assertEqual(self.upload(version).status_code,400)
  self.assertEqual(self.upload().status_code,201);self.assertEqual(self.upload().status_code,400)
 def test_export_has_history_without_secrets_and_security_headers(self):
  r=self.client.get(self.base+'/export',headers=self.owner);self.assertEqual(r.status_code,200)
  for person in self.people:self.assertNotIn(person['token'],r.text)
  self.assertIn('history',r.json);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy'])
 def test_request_size_is_bounded(self):
  r=self.client.post(self.base+'/versions',headers=self.owner,data={'expected':'0','file':(io.BytesIO(b'x'*(11*1024*1024)),'huge.pdf')});self.assertEqual(r.status_code,413)
 def test_weak_owner_configuration_rejected(self):
  for key in ['',None,'短'*40]:
   with self.assertRaises(ValueError):create_app(self.tmp.name+'/other',key)
