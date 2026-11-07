#!/usr/bin/env python3
"""Create Chapter 40 claim/evidence templates without inventing evidence."""
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'claims'/'Chapter40_Evidence_Matrix_Template.xlsx'

wb=Workbook(); ws=wb.active; ws.title='Evidence_Matrix'
cols=['ID','Chapter section','Subsection','Scientific claim','Mechanism category','Cancer type','Therapeutic context','Signaling node/pathway A','Signaling node/pathway B','Crosstalk mechanism','Resistance phenotype','Evidence level','Experimental model','Therapeutic strategy','Outcome','Biomarker','Key finding','Primary paper','Review support','Evidence strength / limitations','Figure potential','Table potential','Overlap risk','Final section','Literature Record ID','PMID','DOI','Literature Category','Evidence Tier','Full Text Status']
ws.append(cols)
for c in ws[1]: c.font=Font(bold=True); c.alignment=Alignment(wrap_text=True,vertical='top')
ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
for i,h in enumerate(cols,1): ws.column_dimensions[get_column_letter(i)].width=min(max(len(h)+2,12),30)

ws2=wb.create_sheet('Literature_Discovery_Master')
cols2=['Literature Record ID','PMID','DOI','PMCID','Title','Authors','Journal','Year','Source Databases','Originating Search Streams','Originating Search Queries','Primary Literature Category','Final Literature Category','Evidence Tier','Mechanism Flags','Subsection Hints','Scientific Role Flags','Foundational Status','Classification Status','Full Text Status','Full Text Path','Supplementary Count','Keep for Chapter?','Notes']
ws2.append(cols2)
for c in ws2[1]: c.font=Font(bold=True); c.alignment=Alignment(wrap_text=True,vertical='top')
ws2.freeze_panes='A2'; ws2.auto_filter.ref=ws2.dimensions
for i,h in enumerate(cols2,1): ws2.column_dimensions[get_column_letter(i)].width=min(max(len(h)+2,12),32)

ws3=wb.create_sheet('Coding_Guide')
rows=[
('Literature categories','A_FOUNDATIONAL','Manually verified landmark/foundational paper; never assigned solely because it is old.'),
('Literature categories','B_MAJOR_REVIEW','High-quality review used for framework and literature mapping.'),
('Literature categories','C_MECHANISTIC_PRIMARY','Primary study demonstrating signaling crosstalk/resistance mechanism.'),
('Literature categories','D_THERAPEUTIC','Primary intervention study testing a resistance-associated network vulnerability.'),
('Literature categories','E_TRANSLATIONAL_CLINICAL','Clinical study/trial or strong patient-level translational evidence.'),
('Literature categories','F_EMERGING_DISCOVERY','Emerging/perspective/discovery material requiring appropriate evidence weighting.'),
('Evidence tiers','Tier 1','Primary mechanistic/intervention evidence; core claims.'),
('Evidence tiers','Tier 2','High-quality recent reviews; framework and literature mapping.'),
('Evidence tiers','Tier 3','Clinical studies/trials; translation.'),
('Evidence tiers','Tier 4','Perspectives/commentaries; emerging concepts/future directions.'),
('Evidence tiers','Tier 5','Search/discovery material used to locate stronger evidence.'),
('Mechanisms','M1–M6','Core signaling crosstalk mechanisms.'),
('Processes','P1–P4','Network properties/adaptive processes.'),
('Context','C1–C2','Microenvironmental/evolutionary contextual layers.'),
('Core rule','CLAIM → MECHANISM → RESISTANCE STATE → VULNERABILITY → INTERVENTION → OUTCOME','One paper may generate multiple evidence records.'),
]
for row in rows: ws3.append(row)
for c in ws3[1]: c.font=Font(bold=True)
ws3.column_dimensions['A'].width=24; ws3.column_dimensions['B'].width=60; ws3.column_dimensions['C'].width=90

OUT.parent.mkdir(parents=True,exist_ok=True); wb.save(OUT); print(OUT)
