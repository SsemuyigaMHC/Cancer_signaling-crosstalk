# Cancer Signaling Crosstalk — Literature Retrieval

**Literature discovery, reference checking and evidence-workflow scripts supporting Chapter 40: *Targeting Signaling Crosstalk to Overcome Drug Resistance*.**

This repository supports a **purposive narrative review** of adaptive signaling and therapeutic resistance in cancer. The standard workflow checks bibliographic metadata for cited references; an earlier multi-stage PubMed retrieval pipeline is also retained. Automated outputs are provisional and require human source verification. This is **not** a systematic-review dataset or a scientific validation of individual treatment claims.

## Get started (Python 3.10+)

```bash
python -m venv .venv
source .venv/bin/activate       # macOS / Linux / WSL
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The default citation workflow needs only the Python standard library. Internet access is required **only** for live metadata lookups.

## Run the reference-checking workflow

| Step | Command | Expected result |
| --- | --- | --- |
| 1. Offline tests | `python run.py test` | Local tests and syntax checks; no external database calls |
| 2. Inspect input | `python run.py status` | Counts of candidate citations, DOI fields and existing output |
| 3. Dry run | `python run.py citations` | `outputs/cited_reference_manifest.csv` with missing/malformed DOI flags; no internet |
| 4. Live pilot | `python run.py citations --live --limit 10` | Crossref / Europe PMC metadata for at most 10 candidate rows |
| 5. Live remainder | `python run.py citations --live` | Attempt lookups on all citation candidates, keeping failures for review |

Use `python run.py --help` or `python run.py citations --help` for options. To supply your own CSV (with a `doi` column):

```bash
python run.py citations --input path/to/references.csv --output outputs/my_references.csv --live
```

**Inspect the citation inventory before live retrieval.** The included `data/chapter40_citation_inventory.csv` was derived from manuscript citations and bibliography matching; it contains unresolved author/year matches and DOI strings with extraneous metadata. The program flags malformed DOIs for review, without changing source records. Metadata retrieval is not article-level evidence assessment.

## Repository structure

```text
├── run.py                         # Test, status and citation lookup entry point
├── requirements.txt               # Standard-library workflow: no external packages
├── requirements-legacy.txt        # Dependencies for older multi-stage scripts
├── scripts/                       # DOI-based reference metadata utility
├── tests/                         # Offline unit tests
├── data/                           # Candidate citation inventory (not verified)
├── legacy_pipeline/                # Prior discovery, screening and acquisition code
├── docs/                           # Scientific boundaries and legacy workflow notes
└── .gitignore                      # Excludes local results and sensitive runtime files
```

Outputs are generated under `outputs/` and ignored by Git.

## Earlier discovery and evidence-preparation workflow

The historical scripts in `legacy_pipeline/` cover PubMed search, provisional screening/classification, accessible full-text acquisition, quality checks and blank evidence-template preparation. They are **not** routed through the default `run.py` interface because an end-to-end integration test has not been completed. For dependencies, a real command example and known limitations, see [Legacy workflow](docs/LEGACY_WORKFLOW.md). Additional research interpretation cautions are in [Scientific notes](docs/SCIENTIFIC_NOTES.md).

## Responsible use and research interpretation

- Verify metadata against primary sources, including DOI, authors, article title, publication year and study design.
- Distinguish molecular associations, functional dependencies, preclinical response and clinical evidence; metadata lookups cannot verify these claims.
- An inaccessible or unlocated article is **not** negative scientific evidence.
- Follow NCBI, Crossref, Europe PMC and publisher usage requirements; do not redistribute paywalled full text or confidential materials.
- Do not commit generated searches, downloaded full texts, secrets or manuscript drafts. The `.gitignore` excludes common local output directories.

## Tests and availability

The included tests are offline and use mocked metadata responses. Neither live API connectivity nor the complete legacy multi-stage workflow is claimed as validated by these tests. The manuscript and publisher materials are not part of the release.

A public software license has not yet been assigned; see `LICENSE_PENDING_AUTHOR_DECISION.md`. Code availability does not imply permission for unrestricted reuse.
