#!/usr/bin/env python3
"""Convenient entry point for the validated cited-reference utility.

The earlier multi-stage pipeline is available in legacy_pipeline/ but is not
claimed to have passed a new end-to-end validation.
"""
from __future__ import annotations
import argparse
import csv
import subprocess
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sp=p.add_subparsers(dest='step',required=True)
    sp.add_parser('test', help='Run offline tests and syntax checks')
    sp.add_parser('status', help='Summarize reference input and current output')
    c=sp.add_parser('citations',help='Make citation manifest; dry-run by default')
    c.add_argument('--live', action='store_true',help='Request Crossref / Europe PMC metadata')
    c.add_argument('--limit', type=int, default=0)
    c.add_argument('--input', type=Path)
    c.add_argument('--output', type=Path)
    args=p.parse_args()
    if args.step=='test':
        r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT)
        if r.returncode: return r.returncode
        return subprocess.run([sys.executable,'-m','compileall','-q','scripts','legacy_pipeline','run.py'],cwd=ROOT).returncode
    if args.step=='status':
        data=ROOT/'data/chapter40_citation_inventory.csv'
        out=ROOT/'outputs/cited_reference_manifest.csv'
        with data.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
        print(f'Citation candidates: {len(rows)}')
        print(f'With DOI field: {sum(bool(r.get("doi")) for r in rows)}')
        print(f'Output exists: {out.exists()}')
        if out.exists():
            with out.open(encoding='utf-8-sig',newline='') as f: saved=list(csv.DictReader(f))
            print('Lookup statuses:',dict(Counter(r.get('lookup_status','') for r in saved)))
        print('Legacy multistage pipeline: available in legacy_pipeline/, not end-to-end validated')
        return 0
    cmd=[sys.executable,str(ROOT/'scripts/retrieve_cited_references.py')]
    if args.live:cmd.append('--live')
    cmd+=['--limit',str(args.limit)]
    if args.input:cmd+=['--input',str(args.input)]
    if args.output:cmd+=['--output',str(args.output)]
    return subprocess.run(cmd,cwd=ROOT).returncode

if __name__=='__main__': sys.exit(main())
