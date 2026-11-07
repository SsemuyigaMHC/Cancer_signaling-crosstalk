#!/usr/bin/env python3
"""Chapter 40 Stage 01 — broad and targeted literature discovery.

This stage maximizes recall and preserves search provenance. It does not make
final scientific inclusion decisions. Use --phase broad for Day 4 discovery,
--phase targeted for Day 5 targeted retrieval, or --phase all for both.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import SEARCH_PHASES, SETTINGS
from utilities.logging_utils import configure_logging
from utilities.pubmed import ingest_external_exports, build_literature_index, retrieve_metadata, search_all_queries, write_literature_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=sorted(SEARCH_PHASES), default='targeted')
    parser.add_argument('--output-tag', default='', help='Optional suffix for a distinct search run, e.g. RUN02')
    parser.add_argument('--no-external', action='store_true', help='Do not ingest external database exports for this run')
    parser.add_argument('--allow-broad', action='store_true', help='Explicitly opt in to high-recall broad discovery')
    args = parser.parse_args()
    if args.phase in ('broad','all') and not args.allow_broad:
        parser.error('Broad discovery is disabled by default; use --allow-broad only when justified.')

    logger = configure_logging(SETTINGS.logs_dir / f'01_Search_PubMed_{args.phase}.log')
    streams = SEARCH_PHASES[args.phase]
    logger.info('Chapter 40 literature discovery | phase=%s | streams=%d', args.phase, len(streams))

    query_to_pmids, failed = search_all_queries(streams)
    pubmed_index = build_literature_index(query_to_pmids, source_database='PubMed')
    if args.no_external:
        external_records, external_failures = [], []
        logger.info('External database exports disabled for this run.')
    else:
        external_records, external_failures = ingest_external_exports(SETTINGS.external_records_dir)
        failed.extend(external_failures)
    combined = build_literature_index({}, source_database='PubMed', base_records=pubmed_index, external_records=external_records)
    metadata = retrieve_metadata(combined)

    tag = f'_{args.output_tag.strip()}' if args.output_tag.strip() else ''
    out = SETTINGS.metadata_dir / f'Literature_Discovery_{args.phase}{tag}.xlsx'
    metadata.to_excel(out, index=False)
    metadata.to_csv(out.with_suffix('.csv'), index=False)
    write_literature_outputs(metadata, query_to_pmids, failed, SETTINGS.metadata_dir / f'discovery_{args.phase}{tag}')
    logger.info('Canonical records: %d', len(metadata))
    logger.info('Output: %s', out)

if __name__ == '__main__':
    main()
