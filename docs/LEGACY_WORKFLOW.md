# Earlier multi-stage literature pipeline

`legacy_pipeline/` retains the earlier scripts for PubMed searches, classification, screening, acquisition and evidence-template generation. These scripts are supplied as **historical/research workflow code**, not as a validated one-command pipeline.

Install optional dependencies with `python -m pip install -r requirements-legacy.txt` and set `NCBI_EMAIL` before running PubMed search stages. Examples:

```bash
export NCBI_EMAIL='you@institution.edu'
python legacy_pipeline/scripts/01_Search_PubMed.py --help
python legacy_pipeline/scripts/01_Search_PubMed.py --phase targeted --no-external
```

The search step performs network queries and writes local outputs; it must be run with proper NCBI usage etiquette. Broad discovery is deliberately opt-in with `--phase broad --allow-broad`. Other stage scripts require the expected prior-stage files, so check their options and prerequisite files before running them. Do not run large-scale acquisition without verifying access rights, request rates and local storage.

This release does not claim that every stage or all remote downloads have been tested. To avoid accidental claims of reproducibility, the main `run.py` entry point exposes only the reference utility and offline checks.
