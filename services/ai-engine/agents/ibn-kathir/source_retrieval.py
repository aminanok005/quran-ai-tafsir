"""Fail-closed source retrieval for the Ibn Kathir research profile."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_SOURCE_FIELDS = {
    "id",
    "source_id",
    "book_id",
    "author",
    "title",
    "original_text",
    "surah",
    "ayah",
    "source_url",
    "permission_status",
}


class IbnKathirSourceRetrieval:
    """Retrieve passages only from explicitly permission-approved source exports."""

    def __init__(self) -> None:
        self.sources: dict[str, dict[str, Any]] = {}
        self.index: dict[str, list[str]] = {}
        self.cache: dict[str, list[dict[str, Any]]] = {}
        self.source_metadata = {
            "tafsir_ibn_kathir": {
                "title": "Tafsir al-Qur'an al-Azim",
                "author": "Ibn Kathir",
                "author_ar": "ابن كثير",
                "methodology": "ma'thur",
                "language": "ar",
                "verification_status": "not_configured",
            }
        }

    async def load_sources(self, source_path: str | None = None) -> None:
        if source_path is None:
            raise RuntimeError(
                "No licensed Tafsir source store is configured for this agent."
            )

        path = Path(source_path)
        if not path.is_file():
            raise FileNotFoundError(f"Tafsir source export not found: {path}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("sources") if isinstance(payload, dict) else None
        if not isinstance(records, list):
            raise ValueError("Tafsir source export must contain a 'sources' list.")

        loaded: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Each Tafsir source record must be an object.")
            missing = REQUIRED_SOURCE_FIELDS - record.keys()
            if missing:
                raise ValueError(
                    f"Tafsir source record is missing required fields: {sorted(missing)}"
                )
            if record["permission_status"] != "approved":
                raise ValueError(
                    f"Tafsir source {record['id']} does not have approved usage rights."
                )
            if (
                not isinstance(record["surah"], int)
                or not 1 <= record["surah"] <= 114
                or not isinstance(record["ayah"], int)
                or record["ayah"] < 1
            ):
                raise ValueError(f"Tafsir source {record['id']} has an invalid Ayah key.")
            if not all(
                isinstance(record[field], str) and record[field].strip()
                for field in REQUIRED_SOURCE_FIELDS
                if field not in {"surah", "ayah", "permission_status"}
            ):
                raise ValueError(
                    f"Tafsir source {record['id']} has empty attribution or text fields."
                )

            source = dict(record)
            source["verified"] = False
            source.setdefault("excerpt", source["original_text"])
            loaded[source["id"]] = source

        self.sources = loaded
        await self._build_index()
        self.cache.clear()
        logger.info("Loaded %d permission-approved Tafsir passages", len(loaded))

    async def _build_index(self) -> None:
        self.index = {}
        for source_id, source in self.sources.items():
            ayah_id = f"{source['surah']}:{source['ayah']}"
            self.index.setdefault(ayah_id, []).append(source_id)

    async def retrieve(
        self,
        ayah_id: str,
        context: dict[str, Any],
        methodology: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        cache_key = (
            f"{ayah_id}:{methodology}:{max_results}:"
            f"{context.get('arabic_text', '')}"
        )
        if cache_key in self.cache:
            return [dict(source) for source in self.cache[cache_key]]

        sources = []
        for source_id in self.index.get(ayah_id, [])[:max_results]:
            source = dict(self.sources[source_id])
            source["relevance_score"] = 1.0
            source["methodology_match"] = source.get("methodology") == methodology
            sources.append(source)

        self.cache[cache_key] = [dict(source) for source in sources]
        return sources

    def get_source_metadata(self) -> dict[str, Any]:
        return self.source_metadata
