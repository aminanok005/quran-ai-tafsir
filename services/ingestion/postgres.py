"""Idempotent persistence for development-only Tafsir vector records."""

from __future__ import annotations

import json
import math
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import Engine, text

try:
    from .parser import ParsedTafsirRecord, assert_development_record
except ImportError:  # Supports direct unittest execution from this directory.
    from parser import ParsedTafsirRecord, assert_development_record

VECTOR_DIMENSIONS = 1536

_UPSERT_SCHOLAR = text("""
    INSERT INTO scholars (id, scholar_id, name, source_url)
    VALUES (:id, :scholar_id, :name, :source_url)
    ON CONFLICT (scholar_id) DO NOTHING
    RETURNING id
""")

_SELECT_SCHOLAR_ID = text("""
    SELECT id FROM scholars WHERE scholar_id = :scholar_id
""")

_UPSERT_BOOK = text("""
    INSERT INTO tafsir_books (
        id, book_id, scholar_id, title, title_ar, edition, publisher, language,
        permission_status, verification_status, verification_evidence, metadata
    )
    VALUES (
        :id, :book_id, :scholar_id, :title, :title_ar, :edition, :publisher,
        CAST('ar' AS language),
        CAST('development_only' AS permission_status),
        CAST('unverified' AS verification_status),
        :verification_evidence,
        CAST(:metadata AS json)
    )
    ON CONFLICT (book_id) DO NOTHING
    RETURNING id
""")

_SELECT_BOOK = text("""
    SELECT
        id,
        scholar_id,
        permission_status::text AS permission_status,
        verification_status::text AS verification_status
    FROM tafsir_books
    WHERE book_id = :book_id
    FOR UPDATE
""")

_SELECT_SOURCE_PERMISSION = text("""
    SELECT permission_status::text AS permission_status,
           verification_status::text AS verification_status
    FROM source_permissions
    WHERE source_id = :source_id
    FOR UPDATE
""")

_INSERT_SOURCE_PERMISSION = text("""
    INSERT INTO source_permissions (
        source_id, source_url, license, permission_status,
        verification_status, verification_evidence, notes
    )
    VALUES (
        :source_id, :source_url, :license,
        CAST('development_only' AS permission_status),
        CAST('unverified' AS verification_status),
        :verification_evidence, :notes
    )
    ON CONFLICT (source_id) DO NOTHING
""")

_UPSERT_PASSAGE = text("""
    INSERT INTO tafsir_passages (
        id, book_id, surah_number, ayah_start, ayah_end, arabic_text,
        volume, page, edition, source_url, embedding, verification_status
    )
    VALUES (
        :id, :book_id, :surah_number, :ayah_start, :ayah_end, :arabic_text,
        :volume, :page, :edition, :source_url, CAST(:embedding AS vector),
        CAST('unverified' AS evidence_level)
    )
    ON CONFLICT (id) DO UPDATE
    SET arabic_text = EXCLUDED.arabic_text,
        embedding = EXCLUDED.embedding
    WHERE tafsir_passages.arabic_text = EXCLUDED.arabic_text
    RETURNING id
""")


def _stable_uuid(value: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"quran-ai-tafsir:{value}")


def build_development_record_parameters(
    record: ParsedTafsirRecord,
    embedding: list[float],
    *,
    scholar_id: str,
    scholar_name: str,
    book_title: str,
    book_title_ar: str | None = None,
) -> dict[str, object]:
    """Validate and map one parser record to the canonical DB schema."""
    assert_development_record(record)
    if len(embedding) != VECTOR_DIMENSIONS:
        raise ValueError(f"embedding must contain exactly {VECTOR_DIMENSIONS} dimensions")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in embedding
    ):
        raise ValueError("embedding values must be finite numbers")
    if not scholar_id.strip() or not scholar_name.strip() or not book_title.strip():
        raise ValueError("scholar_id, scholar_name, and book_title are required")

    book_uuid = _stable_uuid(f"book:{record.source_id}")
    metadata = {
        "source_id": record.source_id,
        "dataset": record.dataset,
        "work": record.work,
        "scholar": record.scholar,
        "edition": record.edition,
        "license": record.license,
        "source_url": record.source_url,
        "verification_evidence": record.verification_evidence,
        "permission_status": "development_only",
        "verification_status": "unverified",
        "ingestion_mode": "development",
        "production_eligible": False,
    }
    return {
        "scholar": {
            "id": _stable_uuid(f"scholar:{scholar_id}"),
            "scholar_id": scholar_id,
            "name": scholar_name,
            "source_url": record.source_url,
        },
        "book": {
            "id": book_uuid,
            "book_id": record.source_id,
            "scholar_id": _stable_uuid(f"scholar:{scholar_id}"),
            "title": book_title,
            "title_ar": book_title_ar,
            "edition": record.edition,
            "publisher": None,
            "verification_evidence": record.verification_evidence,
            "metadata": json.dumps(metadata, ensure_ascii=False),
        },
        "source_permission": {
            "source_id": record.source_id,
            "source_url": record.source_url,
            "license": record.license,
            "verification_evidence": record.verification_evidence,
            "notes": f"Development-only import from {record.dataset}",
        },
        "passage": {
            "id": _stable_uuid(f"passage:{record.record_id}"),
            "book_id": book_uuid,
            "surah_number": record.surah_number,
            "ayah_start": record.ayah_start,
            "ayah_end": record.ayah_end,
            "arabic_text": record.raw_text,
            "volume": record.volume,
            "page": record.page,
            "edition": record.edition,
            "source_url": record.source_url,
            "embedding": "[" + ",".join(repr(value) for value in embedding) + "]",
        },
    }


def upsert_development_records(
    engine: Engine,
    records: list[tuple[ParsedTafsirRecord, list[float]]],
    *,
    scholar_id: str,
    scholar_name: str,
    book_title: str,
    book_title_ar: str | None = None,
) -> int:
    """Persist one batch; rights and evidence states are never promoted by ingestion."""
    if not records:
        return 0
    source_ids = {record.source_id for record, _ in records}
    if len(source_ids) != 1:
        raise ValueError("one ingestion batch must contain exactly one source_id")

    record_parameters = [
        build_development_record_parameters(
            record,
            embedding,
            scholar_id=scholar_id,
            scholar_name=scholar_name,
            book_title=book_title,
            book_title_ar=book_title_ar,
        )
        for record, embedding in records
    ]
    source_id = next(iter(source_ids))

    with engine.begin() as connection:
        existing_book = connection.execute(
            _SELECT_BOOK,
            {"book_id": source_id},
        ).mappings().first()
        if existing_book and (
            existing_book["permission_status"] != "development_only"
            or existing_book["verification_status"] != "unverified"
        ):
            raise ValueError("refusing to ingest into an existing non-development Tafsir book")

        existing_permission = connection.execute(
            _SELECT_SOURCE_PERMISSION,
            {"source_id": source_id},
        ).mappings().first()
        if existing_permission and (
            existing_permission["permission_status"] != "development_only"
            or existing_permission["verification_status"] != "unverified"
        ):
            raise ValueError("refusing to reuse a non-development source permission record")

        shared = record_parameters[0]
        scholar_parameters = dict(shared["scholar"])
        scholar_id_result = connection.execute(_UPSERT_SCHOLAR, scholar_parameters).scalar_one_or_none()
        if scholar_id_result is None:
            scholar_id_result = connection.execute(
                _SELECT_SCHOLAR_ID,
                {"scholar_id": scholar_id},
            ).scalar_one()

        book_parameters = dict(shared["book"])
        book_parameters["scholar_id"] = scholar_id_result
        book_id_result = connection.execute(_UPSERT_BOOK, book_parameters).scalar_one_or_none()
        if book_id_result is None:
            existing_book = connection.execute(
                _SELECT_BOOK,
                {"book_id": source_id},
            ).mappings().one()
            if existing_book["scholar_id"] != scholar_id_result:
                raise ValueError("existing Tafsir book belongs to a different scholar")
            book_id_result = existing_book["id"]

        connection.execute(_INSERT_SOURCE_PERMISSION, shared["source_permission"])
        for params in record_parameters:
            passage_parameters = dict(params["passage"])
            passage_parameters["book_id"] = book_id_result
            result = connection.execute(_UPSERT_PASSAGE, passage_parameters)
            if result.scalar_one_or_none() is None:
                raise ValueError(
                    "existing passage text differs from the source; review it before re-ingestion"
                )
    return len(records)


__all__ = [
    "VECTOR_DIMENSIONS",
    "build_development_record_parameters",
    "upsert_development_records",
]
