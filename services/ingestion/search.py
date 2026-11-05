"""Development-only lexical search over parsed Tafsir records."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

try:
    from .parser import DEVELOPMENT_COLLECTION, ParsedTafsirRecord, assert_development_record
except ImportError:  # Supports direct unittest execution from this directory.
    from parser import DEVELOPMENT_COLLECTION, ParsedTafsirRecord, assert_development_record


@dataclass(frozen=True)
class SearchHit:
    record: ParsedTafsirRecord
    score: int
    collection: str = DEVELOPMENT_COLLECTION

    @property
    def provenance(self) -> dict[str, object]:
        return {
            "record_id": self.record.record_id,
            "source_id": self.record.source_id,
            "source_url": self.record.source_url,
            "dataset": self.record.dataset,
            "work": self.record.work,
            "scholar": self.record.scholar,
            "edition": self.record.edition,
            "license": self.record.license,
            "verification_evidence": self.record.verification_evidence,
            "volume": self.record.volume,
            "page": self.record.page,
            "permission_status": self.record.permission_status,
            "verification_status": self.record.verification_status,
            "ingestion_mode": self.record.ingestion_mode,
            "production_eligible": self.record.production_eligible,
            "surah_number": self.record.surah_number,
            "ayah_start": self.record.ayah_start,
            "ayah_end": self.record.ayah_end,
        }


def _terms(query: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\w+", query.casefold(), flags=re.UNICODE))


def search_development(
    records: Iterable[ParsedTafsirRecord],
    query: str,
    *,
    limit: int = 20,
) -> tuple[SearchHit, ...]:
    """Search normalized text; reject records outside development isolation."""
    if limit < 1:
        raise ValueError("limit must be positive")
    terms = _terms(query)
    if not terms:
        return ()
    hits: list[SearchHit] = []
    for record in records:
        assert_development_record(record)
        text = record.normalized_text.casefold()
        score = sum(text.count(term) for term in terms)
        if score:
            hits.append(SearchHit(record=record, score=score))
    hits.sort(key=lambda hit: (-hit.score, hit.record.record_id))
    return tuple(hits[:limit])


__all__ = ["SearchHit", "search_development"]
