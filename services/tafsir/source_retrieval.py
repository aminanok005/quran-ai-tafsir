"""
Read-only retrieval from the local QUL tafsir SQLite datasets.
"""

import logging
import json
import os
import re
import sqlite3
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DATASET_METADATA = {
    "ar-tafsir-ibn-kathir": {
        "author": "Ibn Kathir",
        "author_ar": "ابن كثير",
        "title": "Tafsir Ibn Kathir",
        "title_ar": "تفسير ابن كثير",
        "language": "ar",
        "resource_url": "https://qul.tarteel.ai/resources/tafsir/22",
    },
    "ar-tafsir-al-tabari": {
        "author": "Al-Tabari",
        "author_ar": "الطبري",
        "title": "Jami' al-Bayan (Tafsir al-Tabari)",
        "title_ar": "جامع البيان عن تأويل آي القرآن",
        "language": "ar",
        "resource_url": "https://qul.tarteel.ai/resources/tafsir/37",
    },
    "ar-tafseer-al-qurtubi": {
        "author": "Al-Qurtubi",
        "author_ar": "القرطبي",
        "title": "Al-Jami' li-Ahkam al-Quran (Tafsir al-Qurtubi)",
        "title_ar": "الجامع لأحكام القرآن",
        "language": "ar",
        "resource_url": None,
    },
    "id-tafsir-as-saadi": {
        "author": "Abd al-Rahman al-Sa'di",
        "author_ar": "عبد الرحمن السعدي",
        "title": "Taysir al-Karim al-Rahman (Indonesian translation)",
        "title_ar": "تيسير الكريم الرحمن",
        "language": "id",
        "resource_url": "https://qul.tarteel.ai/resources/tafsir/503",
    },
    "tafsir-as-saadi": {
        "author": "Abd al-Rahman al-Sa'di",
        "author_ar": "عبد الرحمن السعدي",
        "title": "Taysir al-Karim al-Rahman",
        "title_ar": "تيسير الكريم الرحمن",
        "language": "ar",
        "resource_url": None,
    },
}

BLOCK_TAGS = {"br", "div", "p", "li", "blockquote", "h1", "h2", "h3"}
AYAH_KEY_PATTERN = re.compile(r"(?:[1-9]|[1-9][0-9]|1[01][0-4]):[1-9][0-9]{0,2}")


@lru_cache(maxsize=2)
def _load_json_dataset(path: str, modified_ns: int, size: int) -> Dict[str, Any]:
    del modified_ns, size
    with Path(path).open(encoding="utf-8") as source_file:
        records = json.load(source_file)
    if not isinstance(records, dict):
        raise ValueError(f"Expected an ayah-keyed JSON object in {Path(path).name}")
    for ayah_key, record in records.items():
        if not isinstance(ayah_key, str) or not AYAH_KEY_PATTERN.fullmatch(ayah_key):
            raise ValueError(f"Invalid Quran ayah key in {Path(path).name}: {ayah_key!r}")
        if isinstance(record, str):
            continue
        if not isinstance(record, dict) or not isinstance(record.get("text"), str):
            raise ValueError(f"Invalid passage record for {ayah_key} in {Path(path).name}")
        ayah_keys = record.get("ayah_keys", [])
        if not isinstance(ayah_keys, list) or any(
            not isinstance(key, str) or not AYAH_KEY_PATTERN.fullmatch(key)
            for key in ayah_keys
        ):
            raise ValueError(f"Invalid ayah_keys mapping for {ayah_key} in {Path(path).name}")
    return records


def _json_record(
    records: Dict[str, Any], ayah_key: str
) -> Optional[Dict[str, Any]]:
    record = records.get(ayah_key)
    group_key = ayah_key
    visited = set()
    while isinstance(record, str) and AYAH_KEY_PATTERN.fullmatch(record):
        if record == group_key or record in visited or record not in records:
            return None
        visited.add(group_key)
        group_key = record
        record = records[group_key]
    if isinstance(record, str):
        raw_text = record
        mapped_keys = [group_key]
    elif isinstance(record, dict):
        raw_text = record["text"]
        mapped_keys = record.get("ayah_keys") or [group_key]
        group_key = mapped_keys[0]
    else:
        return None
    if not raw_text.strip():
        return None
    if not mapped_keys or any(key not in records for key in mapped_keys):
        mapped_keys = [group_key]
    return {
        "group_ayah_key": group_key,
        "ayah_keys": mapped_keys,
        "raw_text": raw_text,
    }


class _VisibleTextParser(HTMLParser):
    """Extract user-visible text from the QUL HTML passage without losing text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1
        elif tag in BLOCK_TAGS and self._ignored_depth == 0:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag in BLOCK_TAGS and self._ignored_depth == 0:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self.parts.append(data)


def _visible_text(raw_html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(raw_html)
    text = "".join(parser.parts)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def connect_readonly(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)


class TafsirSourceRetrieval:
    """Retrieve passages by Quran ayah key from a local QUL-format SQLite file."""

    def __init__(self, source_path: Optional[str] = None):
        self.source_path = Path(source_path) if source_path else None
        self.database_path: Optional[Path] = None
        self.json_records: Optional[Dict[str, Any]] = None
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.index: Dict[str, List[str]] = {}
        self.embedding_model = None
        self.vector_db = None
        self.cache: Dict[str, List[Dict[str, Any]]] = {}
        self.source_metadata: Dict[str, Any] = {}

    def _default_path(self) -> Path:
        configured_path = os.environ.get("QURAN_TAFSIR_DB_PATH")
        if configured_path:
            return Path(configured_path)
        repo_root = Path(__file__).resolve().parents[2]
        return repo_root / "data-tafsir" / "ar-tafsir-ibn-kathir.db"

    async def load_sources(self, source_path: Optional[str] = None) -> None:
        path = Path(source_path) if source_path else self.source_path or self._default_path()
        path = path.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Tafsir SQLite database not found: {path}")

        dataset_id = path.stem
        metadata = DATASET_METADATA.get(dataset_id)
        if metadata is None:
            raise ValueError(f"Unrecognized tafsir dataset: {path.name}")

        if path.suffix.lower() == ".json":
            stat = path.stat()
            records = _load_json_dataset(str(path), stat.st_mtime_ns, stat.st_size)
            row_count = len(records)
            self.json_records = records
        elif path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            connection = self._connect(path)
            try:
                columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(tafsir)")
                }
                required_columns = {
                    "ayah_key", "group_ayah_key", "from_ayah", "to_ayah", "ayah_keys", "text"
                }
                if not required_columns.issubset(columns):
                    raise ValueError(
                        f"Unexpected tafsir schema in {path.name}; "
                        f"missing {sorted(required_columns - columns)}"
                    )
                row_count = connection.execute("SELECT COUNT(*) FROM tafsir").fetchone()[0]
            finally:
                connection.close()
            self.json_records = None
        else:
            raise ValueError(f"Unsupported tafsir source format: {path.suffix}")

        self.source_path = path
        self.database_path = path
        self.source_metadata = {
            **metadata,
            "source_id": f"qul:{dataset_id}",
            "dataset_file": f"data-tafsir/{path.name}",
            "row_count": row_count,
            "source_backend": "qul_json" if path.suffix.lower() == ".json" else "qul_sqlite",
            "rights_status": "unknown",
            "verification_status": "not_reviewed",
        }
        self.cache.clear()
        logger.info("Configured QUL tafsir source %s (%s rows)", path.name, row_count)

    async def _load_from_file(self, source_path: str) -> None:
        await self.load_sources(source_path)

    async def _load_from_database(self) -> None:
        await self.load_sources()

    async def _build_index(self) -> None:
        self.index = {}

    async def retrieve(
        self,
        ayah_id: str,
        context: Dict[str, Any],
        methodology: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        if not re.fullmatch(r"(?:[1-9]|[1-9][0-9]|1[01][0-4]):[1-9][0-9]{0,2}", ayah_id):
            raise ValueError(f"Invalid Quran ayah key: {ayah_id}")
        if max_results < 1:
            raise ValueError("max_results must be positive")
        if self.database_path is None:
            await self.load_sources()

        cache_key = f"{self.database_path}:{ayah_id}:{methodology}:{max_results}"
        if cache_key in self.cache:
            return [source.copy() for source in self.cache[cache_key]]

        if self.database_path is None:
            raise RuntimeError("Tafsir source was not initialized")
        if self.database_path.suffix.lower() == ".json":
            if self.json_records is None:
                raise RuntimeError("Tafsir JSON source was not initialized")
            passage = _json_record(self.json_records, ayah_id)
            if passage is None:
                return []
            raw_html = passage["raw_text"]
            text = _visible_text(raw_html)
            if not text:
                return []
            mapped_ayah_keys = passage["ayah_keys"]
            citation_start = mapped_ayah_keys[0]
            citation_end = mapped_ayah_keys[-1]
            citation_range = (
                citation_start
                if citation_start == citation_end
                else f"{citation_start}-{citation_end}"
            )
            group_ayah_key = passage["group_ayah_key"]
        else:
            raw_html = ""
            text = ""
            mapped_ayah_keys = []
            citation_range = ""
            group_ayah_key = ayah_id
            connection = self._connect(self.database_path)
            try:
                row = connection.execute(
                    """SELECT ayah_key, group_ayah_key, from_ayah, to_ayah, ayah_keys, text
                       FROM tafsir WHERE ayah_key = ?""",
                    (ayah_id,),
                ).fetchone()
                if row is None:
                    return []

                if not (row[5] or "").strip():
                    group_key = row[1]
                    if not group_key or group_key == ayah_id:
                        return []
                    row = connection.execute(
                        """SELECT ayah_key, group_ayah_key, from_ayah, to_ayah, ayah_keys, text
                           FROM tafsir WHERE ayah_key = ?""",
                        (group_key,),
                    ).fetchone()
                    if row is None or not (row[5] or "").strip():
                        return []
            finally:
                connection.close()

            raw_html = row[5] or ""
            text = _visible_text(raw_html)
            if not text:
                return []
            citation_start = row[2] or row[0]
            citation_end = row[3] or citation_start
            citation_range = (
                citation_start
                if citation_start == citation_end
                else f"{citation_start}-{citation_end}"
            )
            group_ayah_key = row[1] or row[0]
            mapped_ayah_keys = [
                key.strip()
                for key in (row[4] or "").split(",")
                if key.strip()
            ] or [row[0]]
        metadata = self.source_metadata
        source_id = f"{metadata['source_id']}:{ayah_id}"
        result = {
            "id": source_id,
            "source_id": metadata["source_id"],
            "source_backend": metadata["source_backend"],
            "dataset_file": metadata["dataset_file"],
            "resource_url": metadata["resource_url"],
            "author": metadata["author"],
            "author_ar": metadata["author_ar"],
            "title": metadata["title"],
            "title_ar": metadata["title_ar"],
            "language": metadata["language"],
            "surah": int(ayah_id.split(":")[0]),
            "ayah": int(ayah_id.split(":")[1]),
            "ayah_key": ayah_id,
            "group_ayah_key": group_ayah_key,
            "ayah_range": citation_range,
            "ayah_keys": mapped_ayah_keys,
            "original_text": text,
            "raw_source_html": raw_html,
            "excerpt": text[:4000],
            "rights_status": metadata["rights_status"],
            "verified": False,
            "metadata": {
                "dataset_file": metadata["dataset_file"],
                "resource_url": metadata["resource_url"],
                "language": metadata["language"],
                "rights_status": metadata["rights_status"],
                "verification_status": metadata["verification_status"],
            },
            "relevance_score": 1.0,
            "methodology_match": True,
        }
        self.cache[cache_key] = [result]
        return [result.copy()]

    @staticmethod
    def _connect(path: Path) -> sqlite3.Connection:
        return connect_readonly(path)

    async def _calculate_relevance(
        self, source: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        return 1.0 if source.get("ayah_key") == context.get("ayah_id") else 0.8

    def _check_methodology_match(self, source: Dict[str, Any], methodology: str) -> bool:
        return True

    async def _semantic_search(
        self, ayah_id: str, context: Dict[str, Any], max_results: int
    ) -> List[Dict[str, Any]]:
        return []

    def get_source_metadata(self) -> Dict[str, Any]:
        return self.source_metadata.copy()
