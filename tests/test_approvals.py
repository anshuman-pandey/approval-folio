import io,json,tempfile,unittest,subprocess
from unittest.mock import patch
from PIL import Image
from pypdf import PdfWriter
from approvals import Approvals,Invalid,document

def pdf(encrypted=False):
 writer=PdfWriter();writer.add_blank_page(width=100,height=100)
 if encrypted:writer.encrypt('secret')
 out=io.BytesIO();writer.write(out);return out.getvalue()
def png():
 out=io.BytesIO();Image.new('RGB',(40,30),'red').save(out,format='PNG');return out.getvalue()
class ApprovalTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=self.tmp.name+'/db';self.db=Approvals(self.path);self.project,self.people=self.db.create('Launch PDF',['Design','Legal']);self.a,self.b=self.people
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def upload(self,expected=0):return self.db.upload(self.project,expected,'proof.pdf',pdf())
 def read(self,person,version=1):return self.db.download(self.project,person['id'],person['token'],version)
 def decide(self,person,sha,version=1,decision='approved',note=''):self.db.decide(self.project,person['id'],person['token'],version,sha,decision,note)
 def test_all_reviewers_required_and_new_version_resets(self):
  first=self.upload()
  for person in self.people:self.read(person);self.decide(person,first['sha256'])
  self.assertTrue(self.db.view(self.project)['approved']);second=self.upload(1)
  self.assertFalse(self.db.view(self.project)['approved']);self.assertTrue(all(r['decision'] is None for r in self.db.view(self.project)['reviewers']))
  self.assertEqual(first['sha256'],second['sha256'])
 def test_stale_decision_never_approves_new_version(self):
  first=self.upload();self.read(self.a);self.upload(1)
  with self.assertRaises(Invalid):self.decide(self.a,first['sha256'])
 def test_digest_mismatch_rejected(self):
  self.upload();self.read(self.a)
  with self.assertRaises(Invalid):self.decide(self.a,'0'*64)
 def test_download_required_for_each_reviewer(self):
  first=self.upload();self.read(self.a)
  with self.assertRaises(Invalid):self.decide(self.b,first['sha256'])
 def test_changes_require_note_and_history_is_append_only(self):
  first=self.upload();self.read(self.a);self.decide(self.a,first['sha256'])
  with self.assertRaises(Invalid):self.decide(self.a,first['sha256'],decision='changes_requested')
  self.decide(self.a,first['sha256'],decision='changes_requested',note='Fix heading')
  result=json.loads(self.db.export(self.project));self.assertEqual(len(result['history']),2);self.assertEqual(result['reviewers'][0]['decision']['decision'],'changes_requested');self.assertFalse(result['approved'])
 def test_old_versions_stay_downloadable(self):
  first=self.upload();second=self.db.upload(self.project,1,'image.png',png())
  self.assertEqual(self.read(self.a,1)['sha256'],first['sha256']);self.assertEqual(self.read(self.a,2)['sha256'],second['sha256'])
 def test_rotation_revokes_access_without_destroying_history(self):
  first=self.upload();self.read(self.a);self.decide(self.a,first['sha256']);new=self.db.rotate(self.project,self.a['id'])
  with self.assertRaises(Invalid):self.read(self.a)
  with self.assertRaises(Invalid):self.decide(self.a,first['sha256'])
  self.a['token']=new;self.read(self.a);self.assertEqual(len(json.loads(self.db.export(self.project))['history']),1)
 def test_cross_project_identity_rejected(self):
  other,people=self.db.create('Other',['Someone']);first=self.upload()
  with self.assertRaises(Invalid):self.db.download(self.project,people[0]['id'],people[0]['token'],1)
  with self.assertRaises(Invalid):self.db.rotate(other,self.a['id'])
 def test_stale_upload_and_quota_rollback(self):
  self.upload()
  with self.assertRaises(Invalid):self.upload()
  with patch('approvals.MAX_PROJECT',1):
   with self.assertRaises(Invalid):self.upload(1)
  self.assertEqual(len(self.db.view(self.project)['versions']),1)
 def test_persistence_and_no_secret_export(self):
  self.upload();self.db.close();self.db=Approvals(self.path);self.read(self.a);raw=self.db.export(self.project)
  self.assertNotIn('token_hash',raw)
  for person in self.people:self.assertNotIn(person['token'],raw)
 def test_empty_project_not_approved(self):self.assertFalse(self.db.view(self.project)['approved'])
 def test_invalid_reviewer_names_and_revision(self):
  for names in [[],['Sam','sam'],[''],[None]]:
   with self.assertRaises(Invalid):self.db.create('Title',names)
  with self.assertRaises(Invalid):self.upload(True)
class DocumentTests(unittest.TestCase):
 def test_pdf_and_image(self):
  self.assertEqual(document('proof.pdf',pdf())[1],'application/pdf');name,mime,data=document('photo.jpg',png());self.assertEqual(name,'photo.png');self.assertEqual(mime,'image/png');self.assertTrue(data.startswith(b'\x89PNG'))
 def test_invalid_and_encrypted_pdf(self):
  for content in [b'not pdf',pdf(True)]:
   with self.assertRaises(Invalid):document('proof.pdf',content)
 def test_filename_type_and_size(self):
  for name in ['../proof.pdf','a\\b.pdf','proof\r.pdf','proof.svg','proof\u202e.pdf']:
   with self.assertRaises(Invalid):document(name,pdf())
  with self.assertRaises(Invalid):document('proof.pdf',b'x'*(10*1024*1024+1))

class ProcessingTests(unittest.TestCase):
 def test_timeout_is_rejected(self):
  with patch('approvals.subprocess.run',side_effect=subprocess.TimeoutExpired('pdf_check',5)):
   with self.assertRaises(Invalid):document('proof.pdf',pdf())
 def test_worker_failure_is_rejected(self):
  with patch('approvals.subprocess.run',side_effect=subprocess.CalledProcessError(1,'pdf_check')):
   with self.assertRaises(Invalid):document('proof.pdf',pdf())
 def test_invalid_worker_output_is_rejected(self):
  with patch('approvals.subprocess.run',return_value=subprocess.CompletedProcess('pdf_check',0,b'{"pages":false}')):
   with self.assertRaises(Invalid):document('proof.pdf',pdf())
