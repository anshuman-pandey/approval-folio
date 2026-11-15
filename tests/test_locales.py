import json,re,unittest
from pathlib import Path
class CatalogTests(unittest.TestCase):
 def test_bindings_errors_and_placeholders_have_all_translations(self):
  root=Path(__file__).resolve().parents[1];raw=(root/'static/messages.js').read_text();catalog=json.loads(raw[raw.index('{'):].strip().rstrip(';'))
  from html import unescape
  keys={unescape(k) for k in re.findall(r'data-i18n(?:-placeholder)?="([^"]*)"',(root/'static/index.html').read_text())}
  for f in ['server.py','approvals.py','images.py']:keys.update(re.findall(r"(?:Invalid\(|description=)'([^']*)'",(root/f).read_text()))
  self.assertFalse(keys-set(catalog))
  for source,translations in catalog.items():
   self.assertEqual(set(translations),{'de','es','ja','zh-CN','zh-TW'})
   for translated in translations.values():
    self.assertTrue(translated.strip());self.assertEqual(set(re.findall(r'\{\d+\}',source)),set(re.findall(r'\{\d+\}',translated)))
