"""Read-only Tafsir parsers for development/research mode.

No rights or verification state is inferred from filenames, URLs, repository
presence, or dataset content. Output is isolated from production collections.
"""

from __future__ import annotations

from dataclasses import dataclass
import html
import json
from pathlib import Path
import re
import sqlite3
import unicodedata
from typing import Any, Mapping, Optional

try:
    from .policy import DEVELOPMENT, DEVELOPMENT_ONLY, UNVERIFIED
except ImportError:  # Supports direct unittest execution from this directory.
    from policy import DEVELOPMENT, DEVELOPMENT_ONLY, UNVERIFIED

DEVELOPMENT_COLLECTION = "tafsir_development"
_AYAH_KEY = re.compile(r"^(?P<surah>[1-9][0-9]*):(?P<ayah>[1-9][0-9]*)$")
_TAGS = re.compile(r"<[^>]*>")
_TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class DevelopmentProvenance:
    source_id: str
    dataset: str
    work: Optional[str] = None
    scholar: Optional[str] = None
    source_url: Optional[str] = None
    edition: Optional[str] = None
    license: Optional[str] = None
    verification_evidence: Optional[str] = None
    permission_status: str = DEVELOPMENT_ONLY
    verification_status: str = UNVERIFIED
    ingestion_mode: str = DEVELOPMENT
    production_eligible: bool = False

    def __post_init__(self) -> None:
        if self.permission_status != DEVELOPMENT_ONLY:
            raise ValueError("parser provenance must use development_only")
        if self.verification_status != UNVERIFIED:
            raise ValueError("parser provenance must use unverified")
        if self.ingestion_mode != DEVELOPMENT:
            raise ValueError("parser provenance must use explicit development mode")
        if self.production_eligible:
            raise ValueError("development provenance cannot be production eligible")


@dataclass(frozen=True)
class ParsedTafsirRecord:
    record_id: str
    source_id: str
    source_url: Optional[str]
    dataset: str
    work: Optional[str]
    scholar: Optional[str]
    edition: Optional[str]
    license: Optional[str]
    permission_status: str
    verification_status: str
    verification_evidence: Optional[str]
    ingestion_mode: str
    production_eligible: bool
    surah_number: int
    ayah_start: int
    ayah_end: int
    raw_text: str
    normalized_text: str
    source_key: str
    volume: Optional[int] = None
    page: Optional[int] = None


@dataclass(frozen=True)
class ParseIssue:
    code: str
    message: str
    source_key: Optional[str] = None


@dataclass(frozen=True)
class ParseResult:
    records: tuple[ParsedTafsirRecord, ...]
    issues: tuple[ParseIssue, ...]


def parse_ayah_key(value: str) -> tuple[int, int]:
    """Parse a strict ``surah:ayah`` key without correcting invalid input."""
    match = _AYAH_KEY.fullmatch(value.strip())
    if not match:
        raise ValueError(f"invalid ayah key: {value!r}")
    surah, ayah = int(match.group("surah")), int(match.group("ayah"))
    if surah > 114 or ayah > 286:
        raise ValueError(f"ayah key out of range: {value!r}")
    return surah, ayah


def normalize_text(raw_text: str) -> str:
    """Derive search text while retaining exact source text separately."""
    return " ".join(
        unicodedata.normalize("NFC", _TAGS.sub(" ", html.unescape(raw_text))).split()
    )


def _source_text(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping) and isinstance(value.get("text"), str):
        return value["text"]
    return None


def _record(
    provenance: DevelopmentProvenance,
    key: str,
    start: tuple[int, int],
    end: tuple[int, int],
    raw_text: str,
) -> ParsedTafsirRecord:
    if start[0] != end[0] or end[1] < start[1]:
        raise ValueError(f"invalid passage range for {key!r}")
    return ParsedTafsirRecord(
        record_id=f"{provenance.source_id}:{provenance.dataset}:{key}",
        source_id=provenance.source_id,
        source_url=provenance.source_url,
        dataset=provenance.dataset,
        work=provenance.work,
        scholar=provenance.scholar,
        edition=provenance.edition,
        license=provenance.license,
        permission_status=provenance.permission_status,
        verification_status=provenance.verification_status,
        verification_evidence=provenance.verification_evidence,
        ingestion_mode=provenance.ingestion_mode,
        production_eligible=provenance.production_eligible,
        surah_number=start[0],
        ayah_start=start[1],
        ayah_end=end[1],
        raw_text=raw_text,
        normalized_text=normalize_text(raw_text),
        source_key=key,
    )


def parse_json_payload(
    payload: Mapping[str, Any], provenance: DevelopmentProvenance
) -> ParseResult:
    """Parse a JSON mapping keyed by ``surah:ayah`` in memory."""
    records: list[ParsedTafsirRecord] = []
    issues: list[ParseIssue] = []
    seen: set[str] = set()
    for raw_key, value in payload.items():
        key = str(raw_key)
        if key in seen:
            issues.append(ParseIssue("duplicate_key", "duplicate ayah key", key))
            continue
        seen.add(key)
        try:
            ayah = parse_ayah_key(key)
        except ValueError as error:
            issues.append(ParseIssue("invalid_ayah_key", str(error), key))
            continue
        source_text = _source_text(value)
        if source_text is None:
            issues.append(ParseIssue("missing_text", "record has no string text field", key))
            continue
        if not source_text.strip():
            issues.append(ParseIssue("empty_text", "record text is empty", key))
        records.append(_record(provenance, key, ayah, ayah, source_text))
    return ParseResult(tuple(records), tuple(issues))


def parse_json_file(path: str | Path, provenance: DevelopmentProvenance) -> ParseResult:
    """Read and parse a JSON Tafsir mapping; never mutate source data."""
    duplicates: list[str] = []

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    with Path(path).open(encoding="utf-8") as source_file:
        payload = json.load(source_file, object_pairs_hook=object_pairs)
    if not isinstance(payload, dict):
        raise ValueError("Tafsir JSON root must be an object keyed by surah:ayah")
    parsed = parse_json_payload(payload, provenance)
    duplicate_issues = tuple(
        ParseIssue("duplicate_key", "duplicate JSON object key", key) for key in duplicates
    )
    return ParseResult(parsed.records, duplicate_issues + parsed.issues)


def _optional_key(value: Any) -> Optional[tuple[int, int]]:
    if value is None or not str(value).strip():
        return None
    return parse_ayah_key(str(value))


def parse_sqlite_file(
    path: str | Path,
    provenance: DevelopmentProvenance,
    *,
    table: str = "tafsir",
) -> ParseResult:
    """Read Tafsir SQLite database through a read-only URI connection."""
    if not _TABLE_NAME.fullmatch(table):
        raise ValueError(f"invalid SQLite table name: {table!r}")
    database = Path(path).resolve()
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
        missing = {"ayah_key", "text"} - columns
        if missing:
            raise ValueError(f"SQLite table missing required fields: {sorted(missing)}")
        rows = connection.execute(f'SELECT * FROM "{table}"').fetchall()
    finally:
        connection.close()

    records: list[ParsedTafsirRecord] = []
    issues: list[ParseIssue] = []
    seen: set[str] = set()
    for row in rows:
        key = str(row["ayah_key"])
        if key in seen:
            issues.append(ParseIssue("duplicate_key", "duplicate ayah key", key))
            continue
        seen.add(key)
        try:
            fallback = parse_ayah_key(key)
            start = _optional_key(row["from_ayah"]) if "from_ayah" in columns else None
            end = _optional_key(row["to_ayah"]) if "to_ayah" in columns else None
            if (start is None) != (end is None):
                raise ValueError("passage range requires both from_ayah and to_ayah")
            start, end = (fallback, fallback) if start is None else (start, end)
            if not isinstance(row["text"], str):
                raise ValueError("record text is not a string")
            record = _record(provenance, key, start, end, row["text"])
        except (TypeError, ValueError) as error:
            issues.append(ParseIssue("invalid_record", str(error), key))
            continue
        if not record.raw_text.strip():
            issues.append(ParseIssue("empty_text", "record text is empty", key))
        records.append(record)
    return ParseResult(tuple(records), tuple(issues))


def assert_development_record(record: ParsedTafsirRecord) -> None:
    """Block any record that could be mistaken for production-approved data."""
    if (
        record.permission_status != DEVELOPMENT_ONLY
        or record.verification_status != UNVERIFIED
        or record.ingestion_mode != DEVELOPMENT
        or record.production_eligible
    ):
        raise ValueError("record is not isolated as development-only data")


def embedding_collection(record: ParsedTafsirRecord) -> str:
    """Development parser cannot select a production embedding collection."""
    assert_development_record(record)
    return DEVELOPMENT_COLLECTION


def is_production_eligible(record: ParsedTafsirRecord) -> bool:
    """Conservative guard. Development parser output always evaluates false."""
    return bool(
        record.production_eligible
        and record.permission_status == "approved"
        and record.verification_status == "verified"
        and record.license
        and record.source_url
        and record.verification_evidence
    )


__all__ = [
    "DEVELOPMENT_COLLECTION",
    "DevelopmentProvenance",
    "ParsedTafsirRecord",
    "ParseIssue",
    "ParseResult",
    "assert_development_record",
    "embedding_collection",
    "is_production_eligible",
    "normalize_text",
    "parse_ayah_key",
    "parse_json_file",
    "parse_json_payload",
    "parse_sqlite_file",
]
