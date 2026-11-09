# Scientific scope and validation

This repository supports the literature-search workflow associated with Chapter 40, *Targeting Signaling Crosstalk to Overcome Drug Resistance*.

## Evidence boundaries

- Citation inventory rows were extracted from manuscript citation markup and matched to bibliography text heuristically. They are candidate records, **not a verified reference dataset**.
- The citation utility retrieves metadata only; it does not evaluate whether a paper supports a therapeutic, molecular, causal or clinical claim.
- The original `legacy_pipeline/` includes broader discovery, screening, accessible full-text acquisition and blank evidence-template scripts, but **its full sequence has not been end-to-end tested for this release**.
- Absence from a search or failure to retrieve full text must not be interpreted as negative evidence.
- All downstream scientific interpretation and claim–source reconciliation require manual review of primary literature.

## Quality control

The default offline citation run flags empty or malformed DOI strings without making network requests or silently rewriting the input inventory. Live mode accesses Crossref and Europe PMC, but titles, authors, dates and DOI identities must still be checked by a person. Offline tests use mocks and do not establish database service uptime or scientific recall.

## Scope of released files

Code and candidate citation metadata are provided. No protected full texts, publisher manuscripts, editor correspondence or automatically extracted experimental claims are included.
