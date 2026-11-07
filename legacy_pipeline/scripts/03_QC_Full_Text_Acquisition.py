#!/usr/bin/env python3
"""Stage 03 QC — audit full-text and supplementary acquisition completeness."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from config.settings import SETTINGS

def load(p):
    if not p.exists(): raise FileNotFoundError(p)
    return pd.read_excel(p,dtype=object).fillna('') if p.suffix.lower()=='.xlsx' else pd.read_csv(p,dtype=object).fillna('')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--classified',type=Path,default=SETTINGS.metadata_dir/'Literature_Classified.xlsx'); ap.add_argument('--summary',type=Path,default=SETTINGS.metadata_dir/'Full_Text_Acquisition_Summary.xlsx'); ap.add_argument('--output-dir',type=Path,default=SETTINGS.metadata_dir/'QC_Full_Text'); args=ap.parse_args()
    cls=load(args.classified); summ=load(args.summary); out=args.output_dir; out.mkdir(parents=True,exist_ok=True)
    flags=[]
    if 'PMID' in cls and 'pmid' in summ:
        expected=set(cls['PMID'].astype(str).str.extract(r'(\d+)')[0].dropna())
        observed=set(summ['pmid'].astype(str).str.extract(r'(\d+)')[0].dropna())
        missing=sorted(expected-observed); extra=sorted(observed-expected)
        pd.DataFrame({'PMID':missing}).to_excel(out/'03A_Expected_Not_in_Acquisition_Summary.xlsx',index=False)
        pd.DataFrame({'PMID':extra}).to_excel(out/'03B_Acquisition_Records_Not_in_Classified.xlsx',index=False)
        if missing: flags.append(('WARN',f'{len(missing):,} classified PMIDs are absent from the acquisition summary.'))
    status=summ['overall_status'].value_counts(dropna=False).rename_axis('Overall_Status').reset_index(name='Records') if 'overall_status' in summ else pd.DataFrame()
    group=summ['acquisition_group'].value_counts(dropna=False).rename_axis('Acquisition_Group').reset_index(name='Records') if 'acquisition_group' in summ else pd.DataFrame()
    pdf=summ['canonical_pdf_status'].value_counts(dropna=False).rename_axis('PDF_Status').reset_index(name='Records') if 'canonical_pdf_status' in summ else pd.DataFrame()
    supp=summ['supplementary_status'].value_counts(dropna=False).rename_axis('Supplementary_Status').reset_index(name='Records') if 'supplementary_status' in summ else pd.DataFrame()
    failed=summ[summ.get('overall_status','').astype(str).str.startswith('FAILED')] if 'overall_status' in summ else pd.DataFrame()
    failed.to_excel(out/'03E_Failed_Acquisitions.xlsx',index=False)
    for name,df in [('03C_Status_Distribution',status),('03D_Group_Distribution',group),('03F_PDF_Status',pdf),('03G_Supplementary_Status',supp)]: df.to_excel(out/f'{name}.xlsx',index=False)
    # File existence audit from recorded canonical paths.
    existence=[]
    if 'canonical_pdf_path' in summ:
        for _,r in summ.iterrows():
            p=str(r.get('canonical_pdf_path','')).strip(); exists=bool(p) and (ROOT/p).exists() if p else False
            existence.append({'PMID':r.get('pmid',''),'Group':r.get('acquisition_group',''),'Recorded_PDF_Path':p,'File_Exists':exists})
    exdf=pd.DataFrame(existence); exdf.to_excel(out/'03H_Recorded_PDF_File_Existence.xlsx',index=False)
    if not exdf.empty and (~exdf['File_Exists']).sum(): flags.append(('WARN',f'{int((~exdf.File_Exists).sum()):,} records claim a PDF path that is not present on disk.'))
    if not status.empty and status['Overall_Status'].astype(str).str.startswith('FAILED').any(): flags.append(('WARN',f"{int(status.loc[status.Overall_Status.astype(str).str.startswith('FAILED'),'Records'].sum()):,} acquisition records failed."))
    if not flags: flags.append(('INFO','No automated full-text QC warnings triggered; inspect failures and a sample of acquired files.'))
    pd.DataFrame(flags,columns=['Level','Finding']).to_excel(out/'03I_QC_Flags.xlsx',index=False)
    print(f'Full-text QC written to: {out}')
if __name__=='__main__': main()
