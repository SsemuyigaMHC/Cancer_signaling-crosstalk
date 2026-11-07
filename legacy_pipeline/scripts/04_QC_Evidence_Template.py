#!/usr/bin/env python3
"""Stage 04 QC — verify the evidence-matrix template before claim extraction."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from config.settings import SETTINGS
EXPECTED_SHEETS=['Evidence_Matrix','Literature_Discovery_Master','Coding_Guide']
EXPECTED_COLUMNS=['ID','Chapter section','Subsection','Scientific claim','Mechanism category','Cancer type','Therapeutic context','Signaling node/pathway A','Signaling node/pathway B','Crosstalk mechanism','Resistance phenotype','Evidence level','Experimental model','Therapeutic strategy','Outcome','Biomarker','Key finding','Primary paper','Review support','Evidence strength / limitations','Figure potential','Table potential','Overlap risk','Final section']
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,default=SETTINGS.claims_dir/'Chapter40_Evidence_Matrix_Template.xlsx'); ap.add_argument('--output-dir',type=Path,default=SETTINGS.claims_dir/'QC_Template'); args=ap.parse_args()
    out=args.output_dir; out.mkdir(parents=True,exist_ok=True); flags=[]
    xl=pd.ExcelFile(args.input); sheets=xl.sheet_names
    pd.DataFrame({'Expected_Sheet':EXPECTED_SHEETS,'Present':[x in sheets for x in EXPECTED_SHEETS]}).to_excel(out/'04A_Sheet_Check.xlsx',index=False)
    if any(x not in sheets for x in EXPECTED_SHEETS): flags.append(('FAIL','One or more expected evidence-matrix sheets are missing.'))
    if 'Evidence_Matrix' in sheets:
        df=pd.read_excel(args.input,sheet_name='Evidence_Matrix',dtype=object).fillna('')
        missing=[c for c in EXPECTED_COLUMNS if c not in df.columns]
        pd.DataFrame({'Expected_Column':EXPECTED_COLUMNS,'Present':[x in df.columns for x in EXPECTED_COLUMNS]}).to_excel(out/'04B_Evidence_Column_Check.xlsx',index=False)
        if missing: flags.append(('FAIL','Missing Evidence_Matrix columns: '+', '.join(missing)))
        if 'ID' in df and df['ID'].astype(str).ne('').any() and df['ID'].astype(str).duplicated().any(): flags.append(('WARN','Duplicate evidence IDs detected.'))
    pd.DataFrame(flags or [('INFO','Evidence template structure passed automated QC; claim-level scientific QC begins during extraction.')],columns=['Level','Finding']).to_excel(out/'04C_QC_Flags.xlsx',index=False)
    print(f'Evidence template QC written to: {out}')
if __name__=='__main__': main()
