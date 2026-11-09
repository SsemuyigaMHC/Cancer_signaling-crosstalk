#!/usr/bin/env python3
"""Retrieve verifiable metadata for known cited DOIs; no broad searching.

Offline dry-run is default. --live enables exact-DOI Crossref and Europe PMC
lookup only. No paywall circumvention or copyrighted full-text downloads.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_INPUT=ROOT/'data'/'chapter40_citation_inventory.csv'


def normalize_doi(value: str)->str:
    v=value.strip()
    v=re.sub(r'^https?://(?:dx\.)?doi\.org/', '', v, flags=re.I)
    if v and (not re.fullmatch(r'10\.\d{4,9}/[^\s;]+', v, flags=re.I) or any(c in v for c in '<>')):
        raise ValueError(f'Invalid DOI: {value}')
    return v


def request_json(url: str, *, timeout=15, opener=None):
    opener=opener or urllib.request.urlopen
    req=urllib.request.Request(url, headers={'User-Agent':'Chapter40ReferenceAudit/1.0 (metadata-only; contact maintainer via GitHub)'})
    with opener(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def exact_lookup(doi: str, opener=None):
    doi=normalize_doi(doi)
    enc=urllib.parse.quote(doi,safe='')
    crossref=request_json('https://api.crossref.org/works/'+enc,opener=opener).get('message',{})
    # DOI-specific Europe PMC query is intentionally narrow (not a discovery search).
    query=urllib.parse.urlencode({'query':'DOI:'+doi,'format':'json','pageSize':2})
    epmc=request_json('https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+query,opener=opener)
    entries=epmc.get('resultList',{}).get('result',[])
    matching=[v for v in entries if normalize_doi(v.get('doi',''))==doi]
    match=matching[0] if matching else {}
    return {
      'doi':doi,'title':(crossref.get('title') or [''])[0],
      'journal':(crossref.get('container-title') or [''])[0],
      'crossref_authors':'; '.join(a.get('family','') for a in crossref.get('author',[])[:6]),
      'published':str((crossref.get('published') or crossref.get('created') or {}).get('date-parts', [['']])[0][0]),
      'pmid':match.get('id',''),'pmcid':match.get('pmcid',''),
      'is_open_access':match.get('isOpenAccess',''),
      'open_access_record':'https://europepmc.org/articles/'+match['pmcid'] if match.get('pmcid') and match.get('isOpenAccess')=='Y' else '',
      'metadata_source':'Crossref + Europe PMC exact DOI',
    }


def process(input_file:Path, output_file:Path, live:bool=False,limit:int=0,delay:float=0.4,opener=None):
    with input_file.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    if limit:rows=rows[:limit]
    out=[]
    for r in rows:
        item={**r,'lookup_status':'DOI_NOT_VERIFIED','retrieved_title':'','retrieved_journal':'','retrieved_year':'','open_access_record':''}
        raw_doi=r.get('doi','')
        try:
            doi=normalize_doi(raw_doi)
        except ValueError:
            doi=''
            item['lookup_status']='MALFORMED_DOI_MANUAL_REVIEW'
        if item['lookup_status']=='MALFORMED_DOI_MANUAL_REVIEW':
            pass
        elif not doi:item['lookup_status']='DOI_MISSING_MANUAL_REVIEW'
        elif not live:item['lookup_status']='EXACT_DOI_READY_DRY_RUN'
        else:
            try:
                info=exact_lookup(doi,opener=opener)
                item.update({'lookup_status':'METADATA_RETRIEVED_CHECK_AUTHOR_YEAR','retrieved_title':info['title'],'retrieved_journal':info['journal'],'retrieved_year':info['published'],'open_access_record':info['open_access_record']})
            except Exception as e:
                item['lookup_status']='LOOKUP_ERROR: '+str(e)[:160]
            if delay:time.sleep(delay)
        out.append(item)
    output_file.parent.mkdir(parents=True,exist_ok=True)
    with output_file.open('w',newline='',encoding='utf-8') as f:
        cols=list(out[0].keys()) if out else list(rows[0].keys())+['lookup_status'] if rows else ['lookup_status']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(out)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=DEFAULT_INPUT)
    p.add_argument('--output',type=Path,default=ROOT/'outputs'/'cited_reference_manifest.csv')
    p.add_argument('--live',action='store_true',help='Enable narrowly scoped online metadata checks; requires Internet')
    p.add_argument('--limit',type=int,default=0)
    p.add_argument('--delay',type=float,default=0.4)
    a=p.parse_args()
    if a.limit<0 or a.delay<0:p.error('limit and delay must be nonnegative')
    result=process(a.input,a.output,a.live,a.limit,a.delay)
    from collections import Counter
    print('Records:',len(result),'| statuses:',dict(Counter(x['lookup_status'] for x in result)),'| saved:',a.output)
    print('No copyrighted PDFs downloaded. Missing DOIs are left for human verification.')

if __name__=='__main__':main()
