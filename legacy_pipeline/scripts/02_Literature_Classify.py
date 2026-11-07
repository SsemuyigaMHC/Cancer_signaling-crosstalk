#!/usr/bin/env python3
"""Chapter 40 Stage 02 — classify discovery records into the locked evidence architecture.

The classifier is deliberately conservative. It assigns a PRIMARY literature
category for retrieval/storage, an evidence tier, mechanism flags, subsection
hints, and scientific-role flags. It does NOT claim that an older paper is
"foundational" automatically; foundational status can be promoted from the
curated seed file in config/foundational_seed.csv.
"""
from __future__ import annotations
import re, sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from config.settings import SETTINGS

CATEGORIES = ['A_FOUNDATIONAL','B_MAJOR_REVIEW','C_MECHANISTIC_PRIMARY','D_THERAPEUTIC','E_TRANSLATIONAL_CLINICAL','F_EMERGING_DISCOVERY']
MECHANISMS = {
'M1_BYPASS': ['bypass signaling','alternative pathway','compensatory pathway','bypass pathway','alternative signaling'],
'M2_FEEDBACK': ['negative feedback','feedback reactivation','feedback relief','feedback loop','pathway rebound','reactivation'],
'M3_PARALLEL_SURVIVAL': ['parallel signaling','parallel survival','redundant signaling','survival pathway'],
'M4_CONVERGENCE': ['signaling convergence','convergent signaling','common downstream','shared downstream','bottleneck'],
'M5_RECIPROCAL': ['reciprocal signaling','bidirectional crosstalk','mutual activation','mutual regulation','reciprocal crosstalk'],
'M6_RECEPTOR_SWITCHING': ['receptor switching','alternative receptor','rtk switching','receptor dependence'],
'P1_PLASTICITY': ['phenotypic plasticity','drug tolerant','drug-tolerant','tolerance state','cell-state transition'],
'P2_ROBUSTNESS': ['network robustness','resilience','redundancy','network architecture'],
'P3_REWIRING': ['network rewiring','signaling rewiring','adaptive rewiring','treatment-induced rewiring','therapy-induced rewiring'],
'P4_DYNAMIC_ADAPTATION': ['dynamic adaptation','adaptive response','early adaptive','longitudinal','time-resolved','temporal adaptation'],
'C1_MICROENVIRONMENT': ['tumor microenvironment','tumour microenvironment','microenvironment','cytokine','extracellular matrix','stromal'],
'C2_EVOLUTIONARY_ADAPTATION': ['clonal evolution','evolutionary therapy','evolutionary adaptation','population selection','clonal selection'],
}
SUBSECTION_HINTS = {
'2.1':['rewiring','adaptive signaling','network rewiring','treatment-induced'],
'2.2':['negative feedback','network robustness','signaling redundancy','feedback loop'],
'2.3':['context-dependent','tumor context','genotype-dependent','treatment history','microenvironment'],
'3.1':['actionable','network vulnerability','signaling dependency','bottleneck'],
'3.2':['multi-omics','phosphoproteomics','single-cell','functional genomics','crispr'],
'3.3':['systems biology','network pharmacology','network modeling','computational network'],
'4.1':['rational combination','vertical inhibition','dual pathway','combination therapy'],
'4.2':['synthetic lethality','synthetic lethal','multi-target'],
'4.3':['network-based therapy','systems therapeutics','network-informed','multi-node'],
'5.1':['adaptive therapy','treatment scheduling','evolutionary therapy','dynamic treatment'],
'5.2':['biomarker-guided','predictive biomarker','on-treatment biomarker','dynamic biomarker'],
'5.3':['clinical trial','clinical translation','clinical cancer','trial'],
'6.1':['intratumoral heterogeneity','clonal evolution','single-cell','spatial','heterogeneity'],
'6.2':['clinical implementation','longitudinal molecular','dynamic monitoring','adaptive monitoring'],
'6.3':['ai','machine learning','longitudinal single-cell','spatial profiling','dynamic network modeling'],
}


def norm(x):
    if pd.isna(x): return ''
    return str(x).lower()

def has_any(text, terms):
    return [t for t in terms if t in text]

def classify_category(row, seed):
    key = str(row.get('PMID','')).strip()
    doi = norm(row.get('DOI','')).strip()
    title = norm(row.get('Title',''))
    if key in seed or doi in seed:
        return 'A_FOUNDATIONAL'
    ptype = norm(row.get('Publication Type',''))
    text = ' '.join(norm(row.get(c,'')) for c in ['Title','Abstract','Keywords','MeSH Terms','Publication Type'])
    if any(x in ptype for x in ['review','meta-analysis','systematic review','scoping review','narrative review']):
        return 'B_MAJOR_REVIEW'
    if any(x in ptype for x in ['clinical trial','randomized controlled trial','controlled clinical trial']) or any(x in text for x in ['clinical trial','phase i','phase ii','phase iii','patient cohort','patients treated']):
        return 'E_TRANSLATIONAL_CLINICAL'
    perspective = any(x in ptype for x in ['comment','editorial','perspective']) or any(x in text for x in ['perspective','commentary','future directions'])
    intervention = any(x in text for x in ['combination therapy','dual inhibition','co-treatment','co-treatment','therapeutic targeting','inhibitor','inhibition','treatment'])
    mechanism = any(any(t in text for t in ts) for ts in MECHANISMS.values())
    emerging = any(x in text for x in ['artificial intelligence','machine learning','single-cell','spatial transcriptomics','dynamic network','adaptive therapy'])
    if perspective:
        return 'F_EMERGING_DISCOVERY'
    if intervention and mechanism:
        return 'D_THERAPEUTIC'
    if mechanism:
        return 'C_MECHANISTIC_PRIMARY'
    if emerging:
        return 'F_EMERGING_DISCOVERY'
    return 'F_EMERGING_DISCOVERY'

def evidence_tier(category, row):
    if category in ('A_FOUNDATIONAL','C_MECHANISTIC_PRIMARY','D_THERAPEUTIC'):
        return 'Tier 1'
    if category == 'B_MAJOR_REVIEW': return 'Tier 2'
    if category == 'E_TRANSLATIONAL_CLINICAL': return 'Tier 3'
    text=' '.join(norm(row.get(c,'')) for c in ['Title','Abstract','Publication Type'])
    if any(x in text for x in ['perspective','commentary','editorial']): return 'Tier 4'
    return 'Tier 5'

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', type=Path, default=SETTINGS.metadata_dir/'Literature_Discovery_broad.xlsx')
    args=ap.parse_args()
    df=pd.read_excel(args.input,dtype=object).fillna('')
    seed_path=ROOT/'config'/'foundational_seed.csv'
    seed=set()
    if seed_path.exists():
        seed_df=pd.read_csv(seed_path,dtype=str).fillna('')
        for c in ['PMID','DOI']:
            if c in seed_df:
                seed.update(x.strip().lower() for x in seed_df[c] if x.strip())
    categories=[]; tiers=[]; mechs=[]; subs=[]; roles=[]
    for _,r in df.iterrows():
        text=' '.join(norm(r.get(c,'')) for c in ['Title','Abstract','Keywords','MeSH Terms','Publication Type'])
        cat=classify_category(r,seed); categories.append(cat); tiers.append(evidence_tier(cat,r))
        mh=[]
        for m,terms in MECHANISMS.items():
            if has_any(text,terms): mh.append(m)
        mechs.append('; '.join(mh))
        sh=[]
        for sub,terms in SUBSECTION_HINTS.items():
            if has_any(text,terms): sh.append(sub)
        subs.append('; '.join(sh))
        rr=[]
        if mh: rr.append('MECHANISM')
        if cat=='D_THERAPEUTIC': rr += ['VULNERABILITY','INTERVENTION']
        if cat=='E_TRANSLATIONAL_CLINICAL': rr.append('TRANSLATION')
        if any(x in text for x in ['biomarker','signature','predictive marker']): rr.append('BIOMARKER')
        if not rr: rr.append('DISCOVERY')
        roles.append('; '.join(dict.fromkeys(rr)))
    df['Primary Literature Category']=categories
    df['Evidence Tier']=tiers
    df['Mechanism Flags']=mechs
    df['Subsection Hints']=subs
    df['Scientific Role Flags']=roles
    df['Classification Status']='AUTOMATED_PROVISIONAL'
    df['Final Literature Category']=''
    df['Foundational Status']='NOT_MANUALLY_CURATED'
    out=SETTINGS.metadata_dir/'Literature_Classified.xlsx'
    df.to_excel(out,index=False)
    df.to_csv(out.with_suffix('.csv'),index=False)
    print(f'Wrote {len(df)} records to {out}')
    print(df['Primary Literature Category'].value_counts(dropna=False).to_string())

if __name__=='__main__': main()
