"""Vector retrieval over rights-filtered Tafsir passages."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, text


SEARCH_SQL = text("""
    SELECT
        p.id::text AS passage_id,
        p.surah_number,
        p.ayah_start,
        p.ayah_end,
        p.arabic_text,
        CASE
            WHEN sp.permission_status::text = 'approved'
             AND sp.verification_status::text = 'verified'
             AND COALESCE(sp.license, b.license) IS NOT NULL
             AND COALESCE(sp.verification_evidence, b.verification_evidence) IS NOT NULL
             AND COALESCE(sp.source_url, b.source_url, p.source_url) IS NOT NULL
            THEN p.thai_translation
            ELSE NULL
        END AS thai_translation,
        p.volume,
        p.page,
        p.edition,
        p.source_url,
        p.verification_status::text AS evidence_status,
        b.book_id,
        b.title AS book_title,
        s.scholar_id,
        s.name AS scholar_name,
        sp.permission_status::text AS permission_status,
        sp.verification_status::text AS source_verification_status,
        COALESCE(sp.license, b.license) AS license,
        COALESCE(sp.source_url, b.source_url, p.source_url) AS source_reference,
        1 - (p.embedding <=> CAST(:embedding AS vector)) AS similarity
    FROM tafsir_passages AS p
    JOIN tafsir_books AS b ON b.id = p.book_id
    JOIN scholars AS s ON s.id = b.scholar_id
    JOIN source_permissions AS sp ON sp.source_id = b.book_id
    WHERE p.embedding IS NOT NULL
      AND (:surah_number IS NULL OR p.surah_number = :surah_number)
      AND (:ayah_number IS NULL OR (p.ayah_start <= :ayah_number AND p.ayah_end >= :ayah_number))
      AND (:scholar_id IS NULL OR s.scholar_id = :scholar_id)
      AND (
          (
              :include_development = TRUE
              AND sp.permission_status::text = 'development_only'
              AND sp.verification_status::text = 'unverified'
              AND b.permission_status::text = 'development_only'
              AND b.verification_status::text = 'unverified'
              AND p.verification_status::text = 'unverified'
          )
          OR
          (
              :include_development = FALSE
              AND sp.permission_status::text = 'approved'
              AND sp.verification_status::text = 'verified'
              AND b.permission_status::text = 'approved'
              AND b.verification_status::text = 'verified'
              AND p.verification_status::text IN ('verified', 'source_attributed', 'scholarly_difference')
              AND COALESCE(sp.license, b.license) IS NOT NULL
              AND COALESCE(sp.verification_evidence, b.verification_evidence) IS NOT NULL
              AND COALESCE(sp.source_url, b.source_url, p.source_url) IS NOT NULL
          )
      )
    ORDER BY p.embedding <=> CAST(:embedding AS vector)
    LIMIT :top_k
""")


def _evidence_label(value: object) -> str:
    normalized = str(value).lower()
    labels = {
        "source_attributed": "SOURCE-ATTRIBUTED",
        "scholarly_difference": "SCHOLARLY DIFFERENCE",
        "ai_synthesis": "AI-SYNTHESIS",
    }
    return labels.get(normalized, normalized.upper())


def search_tafsir(
    engine: Engine,
    embedding: list[float],
    *,
    surah_number: int | None,
    ayah_number: int | None,
    scholar_id: str | None,
    top_k: int,
    include_development: bool,
) -> list[dict[str, Any]]:
    """Run a parameterized cosine search and return traceable passage records."""
    vector_literal = "[" + ",".join(repr(value) for value in embedding) + "]"
    with engine.connect() as connection:
        rows = connection.execute(
            SEARCH_SQL,
            {
                "embedding": vector_literal,
                "surah_number": surah_number,
                "ayah_number": ayah_number,
                "scholar_id": scholar_id,
                "top_k": top_k,
                "include_development": include_development,
            },
        ).mappings().all()

    return [
        {
            "passage_id": row["passage_id"],
            "surah_number": row["surah_number"],
            "ayah_start": row["ayah_start"],
            "ayah_end": row["ayah_end"],
            "arabic_text": row["arabic_text"],
            "thai_translation": row["thai_translation"],
            "volume": row["volume"],
            "page": row["page"],
            "edition": row["edition"],
            "evidence_status": _evidence_label(row["evidence_status"]),
            "similarity": float(row["similarity"]),
            "source": {
                "book_id": row["book_id"],
                "title": row["book_title"],
                "scholar_id": row["scholar_id"],
                "scholar": row["scholar_name"],
                "url": row["source_reference"],
                "license": row["license"],
                "permission_status": row["permission_status"],
                "verification_status": row["source_verification_status"],
            },
        }
        for row in rows
    ]

__all__ = ["SEARCH_SQL", "search_tafsir"]
