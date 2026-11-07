#!/usr/bin/env python3
"""Print the recommended QC-gated Chapter 40 workflow."""
print(r'''
CHAPTER 40 QC-GATED WORKFLOW

01 SEARCH
  -> 01_QC_Search_Results.py
  -> inspect retrieval yield, provenance, deduplication, mechanism coverage,
     metadata completeness, year/type balance, and manual QC sample
  -> ONLY THEN proceed to Stage 02

02 CLASSIFICATION
  -> 02_Literature_Classify.py
  -> 02_QC_Classification.py
  -> inspect category/tier distributions, mechanism/subsection coverage,
     contradictions, unclassified records, and stratified sample
  -> ONLY THEN proceed to Stage 03

03 FULL-TEXT ACQUISITION
  -> 03_Full_Text_Acquisition.py
  -> 03_QC_Full_Text_Acquisition.py
  -> inspect expected-vs-acquired records, failures, PDF existence,
     supplementary acquisition, and group coverage
  -> ONLY THEN proceed to claim extraction

04 EVIDENCE TEMPLATE
  -> 04_Create_Evidence_Templates.py
  -> 04_QC_Evidence_Template.py
  -> verify structure before entering scientific claims

IMPORTANT: QC scripts diagnose the pipeline; they do not replace scientific
human review. Automated labels remain provisional until verified.
''')
