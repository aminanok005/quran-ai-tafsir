"""Development-only embedding metadata contract.

This module does not call providers, create vectors, or write indexes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from .parser import DEVELOPMENT_COLLECTION, ParsedTafsirRecord, assert_development_record
except ImportError:  # Supports direct unittest execution from this directory.
    from parser import DEVELOPMENT_COLLECTION, ParsedTafsirRecord, assert_development_record


@dataclass(frozen=True)
class EmbeddingDocument:
    document_id: str
    collection: str
    text: str
    metadata: dict[str, object]


def build_development_embedding_document(record: ParsedTafsirRecord) -> EmbeddingDocument:
    """Build provider-neutral embedding input for development collection only."""
    assert_development_record(record)
    if not record.normalized_text.strip():
        raise ValueError("cannot embed empty normalized text")
    metadata = {
        "record_id": record.record_id,
        "source_id": record.source_id,
        "source_url": record.source_url,
        "dataset": record.dataset,
        "work": record.work,
        "scholar": record.scholar,
        "edition": record.edition,
        "license": record.license,
        "verification_evidence": record.verification_evidence,
        "volume": record.volume,
        "page": record.page,
        "permission_status": record.permission_status,
        "verification_status": record.verification_status,
        "ingestion_mode": record.ingestion_mode,
        "production_eligible": record.production_eligible,
        "surah_number": record.surah_number,
        "ayah_start": record.ayah_start,
        "ayah_end": record.ayah_end,
    }
    return EmbeddingDocument(
        document_id=record.record_id,
        collection=DEVELOPMENT_COLLECTION,
        text=record.normalized_text,
        metadata=metadata,
    )


__all__ = ["EmbeddingDocument", "build_development_embedding_document"]
