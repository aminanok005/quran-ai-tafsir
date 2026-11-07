#!/usr/bin/env python3
"""Embed and ingest a local Tafsir JSON file into the development-only pgvector corpus."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT / "services" / "ingestion"))

from services.ingestion.parser import DevelopmentProvenance, parse_json_file
from services.ingestion.postgres import upsert_development_records

from sqlalchemy import create_engine

logger = logging.getLogger("tafsir_ingestion")


def _require_development_environment(environment: str, explicitly_configured: bool) -> None:
    if not explicitly_configured or environment.strip().lower() != "development":
        raise RuntimeError(
            "Ingestion writes require ENVIRONMENT to be explicitly configured as development."
        )


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True, help="Local JSON mapping keyed by surah:ayah")
    parser.add_argument("--source-id", required=True, help="Stable source/book identifier")
    parser.add_argument("--dataset", required=True, help="Dataset name or relative path")
    parser.add_argument("--scholar-id", required=True)
    parser.add_argument("--scholar-name", required=True)
    parser.add_argument("--book-title", required=True)
    parser.add_argument("--book-title-ar")
    parser.add_argument("--work")
    parser.add_argument("--source-url")
    parser.add_argument("--edition")
    parser.add_argument("--license")
    parser.add_argument("--verification-evidence")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--apply-development-only",
        action="store_true",
        help="Call the configured embedding service and write development-only rows to PostgreSQL.",
    )
    return parser.parse_args()


async def _ingest(args: argparse.Namespace) -> int:
    if args.batch_size < 1 or args.batch_size > 128:
        raise ValueError("--batch-size must be between 1 and 128")
    if not args.file.is_file():
        raise FileNotFoundError("Tafsir JSON file was not found.")

    provenance = DevelopmentProvenance(
        source_id=args.source_id,
        dataset=args.dataset,
        work=args.work,
        scholar=args.scholar_name,
        source_url=args.source_url,
        edition=args.edition,
        license=args.license,
        verification_evidence=args.verification_evidence,
    )
    parsed = parse_json_file(args.file, provenance)
    logger.info(
        "Parsed %d development-only passages; skipped/reported %d source issues.",
        len(parsed.records),
        len(parsed.issues),
    )
    for issue in parsed.issues:
        logger.warning("Skipped source record: %s", issue.code)
    if not parsed.records:
        raise ValueError("No valid Tafsir passages were found in the input file.")
    if not args.apply_development_only:
        logger.info("Dry run complete. No embeddings were requested and no database was changed.")
        return 0

    from services.api.config import settings
    from services.api.services.embedding import embed_texts

    _require_development_environment(
        settings.environment,
        "environment" in settings.model_fields_set,
    )
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured before ingestion.")

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        for offset in range(0, len(parsed.records), args.batch_size):
            batch = parsed.records[offset : offset + args.batch_size]
            embeddings = await embed_texts([record.normalized_text for record in batch])
            count = upsert_development_records(
                engine,
                list(zip(batch, embeddings, strict=True)),
                scholar_id=args.scholar_id,
                scholar_name=args.scholar_name,
                book_title=args.book_title,
                book_title_ar=args.book_title_ar,
            )
            logger.info("Persisted development batch %d (%d passages).", offset // args.batch_size + 1, count)
    finally:
        engine.dispose()
    logger.info("Development-only ingestion completed.")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    return asyncio.run(_ingest(_arguments()))


if __name__ == "__main__":
    raise SystemExit(main())
