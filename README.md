# Signaling Crosstalk Literature Retrieval (Chapter 40)

**Suggested GitHub repository name:** `signaling-crosstalk-literature-retrieval`

This narrowly scoped companion repository documents a literature-retrieval approach used during preparation of the chapter *Targeting Signaling Crosstalk to Overcome Drug Resistance*. It is **not** the chapter manuscript, an exhaustive systematic review, a validated scientific benchmark, a repository of full-text articles, or a source of publisher permissions.

## Why this name

It identifies the research theme and the reproducible **literature retrieval** task without suggesting that the code proves signaling dependencies or is a comprehensive cancer database. It is general enough for future chapter reference updates.

## Recommended workflow (narrow first)

1. Review `data/chapter40_citation_inventory.csv`. It was extracted automatically from the manuscript's inline-citation XML. Some rows are ambiguous; DOIs were drawn from the contributor's existing bibliography where a first-author/year match could be made, and require checking.
2. Run the **offline dry run**, which contacts no external sites:

   ```bash
   python scripts/retrieve_cited_references.py
   ```

3. After reviewing the input DOIs, use **exact DOI** metadata lookups:

   ```bash
   python scripts/retrieve_cited_references.py --live --limit 10
   ```

4. Inspect `outputs/cited_reference_manifest.csv`. Confirm Crossref title, first author, publication year, journal and DOI before adding anything to the manuscript. A verified bibliographic record is **not** proof that you have read the article.
5. Visit the provided Europe PMC open-access article links for full text where available and legally accessible. The code does not fetch paywalled PDFs, emulate login, or bypass access controls.
6. Complete missing or ambiguous DOIs **manually**, using DOI/title and verified publisher or PubMed records. Do not use broad discovery to fill citations automatically.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q scripts legacy_pipeline
```

Tests use local mock HTTP payloads. They verify parsing, exact lookup, and preservation of missing identifiers. **They are not live network or end-to-end literature acquisition tests**; internet access was unavailable in the preparation environment.

## Prior retrieval pipeline

`legacy_pipeline/` contains a cleaned code-only copy of the original retrieval setup, for provenance and future maintenance. It intentionally excludes `__pycache__`, article files, personal notes, logs, manuscripts and publisher correspondence. It was syntax-checked, not fully smoke-tested against remote databases or actual screening outputs. Broad discovery is now opt-in (`--phase broad --allow-broad`), and per-query PubMed retrieval is capped at 500 records by default.

## Repository limits and copyright

- Do not upload publisher PDFs, subscription full text, unpublished chapter drafts, editor correspondence, contributor agreements, protected tables/figures or other people's data unless licensed.
- Respect NCBI, Crossref, Europe PMC, publisher rate limits, terms and attribution requirements.
- This repository is an **optional associated methodological resource**, subject to the editor/publisher's approval. The editor's supplied instructions do not require a public GitHub repository.

**Before publishing:** Approve a software license; verify no proprietary code or third-party copyrighted material is included; confirm whether publisher/editor accept a repository link as optional supplemental material.
