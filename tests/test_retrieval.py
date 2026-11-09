import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from scripts.retrieve_cited_references import normalize_doi, exact_lookup, process

class FakeResponse:
    def __init__(self, payload): self.payload=json.dumps(payload).encode()
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self): return self.payload

def fake_open(request,timeout=15):
    url=request.full_url
    if 'crossref.org' in url:
        return FakeResponse({'message':{'title':['Verified cancer study'],'container-title':['Test Journal'],'author':[{'family':'Example'}],'published':{'date-parts':[[2024]]}}})
    if 'europepmc' in url:
        return FakeResponse({'resultList':{'result':[{'doi':'10.1234/test.1','id':'123','pmcid':'PMC123','isOpenAccess':'Y'}]}})
    raise AssertionError(url)

class TestExactRetrieval(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize_doi('https://doi.org/10.1234/test.1'),'10.1234/test.1')
        with self.assertRaises(ValueError):normalize_doi('not-a-doi')
        with self.assertRaises(ValueError):normalize_doi('10.1200/ABC;PAGEGROUP:STRING:PUBLICATION')
    def test_malformed_doi_is_queued_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)/'seed.csv';out=Path(tmp)/'out.csv'
            with inp.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['first_author','year','doi']);w.writeheader()
                w.writerow({'first_author':'Bad','year':'2024','doi':'10.1200/ABC;PAGEGROUP:STRING:PUBLICATION'})
                w.writerow({'first_author':'Good','year':'2024','doi':'10.1234/test.1'})
            data=process(inp,out,live=False)
            self.assertEqual(data[0]['lookup_status'],'MALFORMED_DOI_MANUAL_REVIEW')
            self.assertEqual(data[1]['lookup_status'],'EXACT_DOI_READY_DRY_RUN')

    def test_live_mock_exact_only(self):
        r=exact_lookup('10.1234/test.1',opener=fake_open)
        self.assertEqual(r['title'],'Verified cancer study')
        self.assertEqual(r['open_access_record'],'https://europepmc.org/articles/PMC123')
    def test_dry_run_retains_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)/'seed.csv';out=Path(tmp)/'out.csv'
            with inp.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['first_author','year','doi']);w.writeheader();w.writerow({'first_author':'Example','year':'2024','doi':'10.1234/test.1'});w.writerow({'first_author':'Unknown','year':'2025','doi':''})
            data=process(inp,out,live=False)
            self.assertEqual(len(data),2)
            self.assertEqual(data[0]['lookup_status'],'EXACT_DOI_READY_DRY_RUN')
            self.assertEqual(data[1]['lookup_status'],'DOI_MISSING_MANUAL_REVIEW')
    def test_live_mock(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)/'seed.csv';out=Path(tmp)/'out.csv'
            with inp.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['first_author','year','doi']);w.writeheader();w.writerow({'first_author':'Example','year':'2024','doi':'10.1234/test.1'})
            data=process(inp,out,live=True,delay=0,opener=fake_open)
            self.assertEqual(data[0]['retrieved_title'],'Verified cancer study')

if __name__=='__main__':unittest.main()
