"""Development-only persistence for Quran Foundation Tafsir API responses."""

from __future__ import annotations

import json
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import Engine, text

from .quran_foundation_tafsir import QuranFoundationTafsir


def upsert_development_qf_tafsir(
    engine: Engine,
    passage: QuranFoundationTafsir,
    *,
    source_url: str,
) -> None:
    source_id = f"qf_tafsir_{passage.resource_id}"
    scholar_id = f"qf_resource_{passage.resource_id}"
    book_uuid = uuid5(NAMESPACE_URL, f"quran-ai:{source_id}")
    scholar_uuid = uuid5(NAMESPACE_URL, f"quran-ai:{scholar_id}")
    passage_uuid = uuid5(
        NAMESPACE_URL,
        f"quran-ai:{source_id}:{passage.verse_key}",
    )
    language = {
        "arabic": "ar",
        "english": "en",
        "thai": "th",
        "urdu": "ur",
    }.get(passage.language_name.lower(), "en")
    metadata = json.dumps(
        {
            "provider": "Quran Foundation Content API",
            "resource_id": passage.resource_id,
            "slug": passage.slug,
            "language_name": passage.language_name,
            "permission_status": "development_only",
            "verification_status": "unverified",
            "production_eligible": False,
        }
    )

    with engine.begin() as connection:
        existing = connection.execute(
            text("""
                SELECT permission_status::text AS permission_status,
                       verification_status::text AS verification_status
                FROM tafsir_books
                WHERE book_id = :book_id
                FOR UPDATE
            """),
            {"book_id": source_id},
        ).mappings().first()
        if existing and (
            existing["permission_status"] != "development_only"
            or existing["verification_status"] != "unverified"
        ):
            raise ValueError("refusing to write a non-development Quran Foundation source")
        existing_permission = connection.execute(
            text("""
                SELECT permission_status::text AS permission_status,
                       verification_status::text AS verification_status
                FROM source_permissions
                WHERE source_id = :source_id
                FOR UPDATE
            """),
            {"source_id": source_id},
        ).mappings().first()
        if existing_permission and (
            existing_permission["permission_status"] != "development_only"
            or existing_permission["verification_status"] != "unverified"
        ):
            raise ValueError("refusing to reuse a non-development source permission record")

        connection.execute(
            text("""
                INSERT INTO scholars (id, scholar_id, name, source_url)
                VALUES (:id, :scholar_id, :name, :source_url)
                ON CONFLICT (scholar_id) DO NOTHING
            """),
            {
                "id": scholar_uuid,
                "scholar_id": scholar_id,
                "name": passage.resource_name,
                "source_url": source_url,
            },
        )
        resolved_scholar_id = connection.execute(
            text("SELECT id FROM scholars WHERE scholar_id = :scholar_id"),
            {"scholar_id": scholar_id},
        ).scalar_one()
        connection.execute(
            text("""
                INSERT INTO tafsir_books (
                    id, book_id, scholar_id, title, edition, source_url, language,
                    permission_status, verification_status, metadata
                )
                VALUES (
                    :id, :book_id, :scholar_id, :title, :edition, :source_url,
                    CAST(:language AS language),
                    CAST('development_only' AS permission_status),
                    CAST('unverified' AS verification_status),
                    CAST(:metadata AS json)
                )
                ON CONFLICT (book_id) DO NOTHING
            """),
            {
                "id": book_uuid,
                "book_id": source_id,
                "scholar_id": resolved_scholar_id,
                "title": passage.resource_name,
                "edition": f"Quran Foundation resource {passage.resource_id}",
                "source_url": source_url,
                "language": language,
                "metadata": metadata,
            },
        )
        connection.execute(
            text("""
                INSERT INTO source_permissions (
                    source_id, source_url, permission_status,
                    verification_status, notes
                )
                VALUES (
                    :source_id, :source_url,
                    CAST('development_only' AS permission_status),
                    CAST('unverified' AS verification_status),
                    'Development-only API cache; rights review required before production use'
                )
                ON CONFLICT (source_id) DO NOTHING
            """),
            {"source_id": source_id, "source_url": source_url},
        )
        connection.execute(
            text("""
                INSERT INTO tafsir_passages (
                    id, book_id, surah_number, ayah_start, ayah_end,
                    arabic_text, source_url,
                    verification_status
                )
                VALUES (
                    :id, :book_id, :surah, :ayah, :ayah,
                    :text, :source_url,
                    CAST('unverified' AS evidence_level)
                )
                ON CONFLICT (id) DO UPDATE
                SET arabic_text = EXCLUDED.arabic_text,
                    source_url = EXCLUDED.source_url,
                    updated_at = CURRENT_TIMESTAMP
            """),
            {
                "id": passage_uuid,
                "book_id": book_uuid,
                "surah": int(passage.verse_key.split(":", 1)[0]),
                "ayah": int(passage.verse_key.split(":", 1)[1]),
                "text": passage.text,
                "source_url": source_url,
            },
        )
