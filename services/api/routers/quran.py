"""Quran catalog and text endpoints backed by Quran Cloud and local QPC V4 data."""

import json
import os
import re
import sqlite3
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Literal, Tuple
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi import Path as PathParameter

from services.tafsir.rights import permission_allows, source_permission

router = APIRouter(prefix="/api/v1/quran", tags=["quran"])
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SURAH_INFO_SOURCE_ID = "qul:surah-info-id"
QPC_LAYOUT_SOURCE_ID = "qul:qpc-v4-tajweed-15-lines"
QPC_LOCATION_PATTERN = re.compile(r"([1-9][0-9]{0,2}):([1-9][0-9]{0,2}):([1-9][0-9]{0,2})")
QPC_VERSE_PATTERN = re.compile(r"([1-9][0-9]{0,2}):([1-9][0-9]{0,2})")
QPC_DEFAULT_SCRIPT_TYPE = "code_v4"
QPC_DEFAULT_FONT_FAMILY = "p574-v4-tajweed"


class _PlainTextHTMLParser(HTMLParser):
    _BLOCK_TAGS = {"br", "div", "h1", "h2", "h3", "li", "p"}
    _IGNORED_TAGS = {"iframe", "object", "script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in self._IGNORED_TAGS:
            self.ignored_depth += 1
        elif not self.ignored_depth and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._IGNORED_TAGS and self.ignored_depth:
            self.ignored_depth -= 1
        elif not self.ignored_depth and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive integer")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.isdigit():
        number = int(value)
    else:
        raise ValueError(f"{field} must be a positive integer")
    if number < 1:
        raise ValueError(f"{field} must be a positive integer")
    return number


def _normalized_word(
    position: Any, text: Any, location: Any, verse_key: str
) -> Dict[str, Any]:
    word_position = _positive_integer(position, "word position")
    if not isinstance(text, str) or not text:
        raise ValueError(f"Invalid QPC V4 word text for {verse_key}")
    expected_location = f"{verse_key}:{word_position}"
    if location != expected_location:
        raise ValueError(f"Invalid QPC V4 word location for {verse_key}")
    return {
        "position": word_position,
        "text": text,
        "location": expected_location,
    }


@lru_cache(maxsize=1)
def _load_qpc_v4_verses(
    source_path: str, modified_ns: int, file_size: int
) -> Tuple[Dict[str, Any], ...]:
    del modified_ns, file_size
    with Path(source_path).open(encoding="utf-8") as source_file:
        records = json.load(source_file)
    if not isinstance(records, dict):
        raise ValueError("QPC V4 dataset must be an object")

    verses: Dict[str, Dict[str, Any]] = {}
    for key, record in records.items():
        if not isinstance(key, str) or not isinstance(record, dict):
            raise ValueError("QPC V4 dataset contains an invalid record")
        word_match = QPC_LOCATION_PATTERN.fullmatch(key)
        if word_match:
            surah, ayah, position = map(int, word_match.groups())
            verse_key = f"{surah}:{ayah}"
            if record.get("location") != key:
                raise ValueError(f"QPC V4 word location does not match key {key}")
            if _positive_integer(record.get("surah"), "surah") != surah:
                raise ValueError(f"QPC V4 surah does not match key {key}")
            if _positive_integer(record.get("ayah"), "ayah") != ayah:
                raise ValueError(f"QPC V4 ayah does not match key {key}")
            if _positive_integer(record.get("word"), "word position") != position:
                raise ValueError(f"QPC V4 word position does not match key {key}")
            word = _normalized_word(position, record.get("text"), key, verse_key)
            verse = verses.setdefault(
                verse_key,
                {
                    "verse_key": verse_key,
                    "surah_number": surah,
                    "number_in_surah": ayah,
                    "words": [],
                    "script_type": QPC_DEFAULT_SCRIPT_TYPE,
                    "font_family": QPC_DEFAULT_FONT_FAMILY,
                },
            )
            verse["words"].append(word)
            continue

        verse_match = QPC_VERSE_PATTERN.fullmatch(key)
        if not verse_match or record.get("verse_key") != key:
            raise ValueError(f"Invalid QPC V4 verse key: {key!r}")
        if not isinstance(record.get("text"), str) or not record["text"]:
            raise ValueError(f"Invalid QPC V4 verse text for {key}")
        surah, ayah = map(int, verse_match.groups())
        raw_words = record.get("words", [])
        if not isinstance(raw_words, list):
            raise ValueError(f"Invalid QPC V4 words for {key}")
        words = [
            _normalized_word(
                word.get("position"),
                word.get("text"),
                word.get("location"),
                key,
            )
            for word in raw_words
            if isinstance(word, dict)
        ]
        if len(words) != len(raw_words):
            raise ValueError(f"Invalid QPC V4 word record for {key}")
        script_type = record.get("script_type", QPC_DEFAULT_SCRIPT_TYPE)
        font_family = record.get("font_family", QPC_DEFAULT_FONT_FAMILY)
        if not isinstance(script_type, str) or not isinstance(font_family, str):
            raise ValueError(f"Invalid QPC V4 rendering metadata for {key}")
        verse = {
            "verse_key": key,
            "surah_number": surah,
            "number_in_surah": ayah,
            "text": record["text"],
            "words": words,
            "script_type": script_type,
            "font_family": font_family,
        }
        for field in ("page_number", "juz_number", "hizb_number"):
            if field in record:
                verse[field] = _positive_integer(record[field], field)
        verses[key] = verse

    ordered_verses = sorted(
        verses.values(), key=lambda verse: (verse["surah_number"], verse["number_in_surah"])
    )
    if not ordered_verses:
        raise ValueError("QPC V4 dataset contains no verses")

    global_number = 0
    previous_surah = 0
    previous_ayah = 0
    for verse in ordered_verses:
        surah = verse["surah_number"]
        ayah = verse["number_in_surah"]
        if surah == previous_surah and ayah != previous_ayah + 1:
            raise ValueError(f"QPC V4 ayah sequence has a gap in surah {surah}")
        if surah != previous_surah and ayah != 1:
            raise ValueError(f"QPC V4 surah {surah} does not start at ayah 1")
        if previous_surah and surah != previous_surah and surah != previous_surah + 1:
            raise ValueError(f"QPC V4 surah sequence has a gap before surah {surah}")
        words = verse["words"]
        words.sort(key=lambda word: word["position"])
        if [word["position"] for word in words] != list(range(1, len(words) + 1)):
            raise ValueError(f"QPC V4 words are not sequential for {verse['verse_key']}")
        if "text" not in verse:
            verse["text"] = " ".join(word["text"] for word in words)
        if not verse["text"]:
            raise ValueError(f"QPC V4 verse has no text: {verse['verse_key']}")
        global_number += 1
        verse["number"] = global_number
        previous_surah = surah
        previous_ayah = ayah

    return tuple(ordered_verses)


def _qpc_v4_path() -> Path:
    configured_path = os.environ.get("QURAN_QPC_V4_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    return REPOSITORY_ROOT / "data-tafsir" / "qpc-v4.json"


def _surah_info_path() -> Path:
    configured_path = os.environ.get("QURAN_SURAH_INFO_ID_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    return REPOSITORY_ROOT / "data-tafsir" / "surah-info-id.json"


def _qpc_15_line_layout_path() -> Path:
    configured_path = os.environ.get("QURAN_QPC_15_LINE_LAYOUT_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    return REPOSITORY_ROOT / "data-tafsir" / "qpc-v4-tajweed-15-lines.db"


@lru_cache(maxsize=1)
def _load_qpc_word_ayah_map(
    source_path: str, modified_ns: int, file_size: int
) -> Dict[int, str]:
    del modified_ns, file_size
    with Path(source_path).open(encoding="utf-8") as source_file:
        records = json.load(source_file)
    if not isinstance(records, dict):
        raise ValueError("QPC V4 dataset must be an object")

    word_ayah_map: Dict[int, str] = {}
    for key, record in records.items():
        match = QPC_LOCATION_PATTERN.fullmatch(key) if isinstance(key, str) else None
        if not match or not isinstance(record, dict) or record.get("location") != key:
            raise ValueError(f"Invalid QPC V4 word location: {key!r}")
        surah, ayah, position = map(int, match.groups())
        word_id = _positive_integer(record.get("id"), "word id")
        if word_id in word_ayah_map:
            raise ValueError(f"Duplicate QPC V4 word id: {word_id}")
        if (
            _positive_integer(record.get("surah"), "surah") != surah
            or _positive_integer(record.get("ayah"), "ayah") != ayah
            or _positive_integer(record.get("word"), "word position") != position
        ):
            raise ValueError(f"Invalid QPC V4 word mapping for {key}")
        word_ayah_map[word_id] = f"{surah}:{ayah}"
    if not word_ayah_map:
        raise ValueError("QPC V4 dataset contains no word mappings")
    if sorted(word_ayah_map) != list(range(1, len(word_ayah_map) + 1)):
        raise ValueError("QPC V4 word IDs are not sequential")
    return word_ayah_map


@lru_cache(maxsize=1)
def _load_qpc_15_line_layout(
    source_path: str, modified_ns: int, file_size: int
) -> Dict[str, Any]:
    del modified_ns, file_size
    database_uri = f"file:{quote(str(Path(source_path).resolve()))}?mode=ro"
    try:
        with sqlite3.connect(database_uri, uri=True) as connection:
            info_rows = connection.execute(
                "SELECT name, number_of_pages, lines_per_page, font_name FROM info"
            ).fetchall()
            rows = connection.execute(
                """
                SELECT page_number, line_number, line_type, is_centered,
                       first_word_id, last_word_id, surah_number
                FROM pages
                ORDER BY page_number, line_number
                """
            ).fetchall()
    except sqlite3.Error as error:
        raise ValueError("QPC 15-line layout database has an invalid schema") from error

    if len(info_rows) != 1:
        raise ValueError("QPC 15-line layout database must have one metadata record")
    name, total_pages, lines_per_page, font_name = info_rows[0]
    if (
        not isinstance(name, str)
        or not isinstance(font_name, str)
        or _positive_integer(total_pages, "number of pages") != 604
        or _positive_integer(lines_per_page, "lines per page") != 15
    ):
        raise ValueError("QPC 15-line layout metadata must describe 604 pages and 15 lines")

    pages: Dict[int, list[Dict[str, Any]]] = {page: [] for page in range(1, 605)}
    previous_word_id = 0
    for row in rows:
        page_number, line_number, line_type, is_centered, first_word_id, last_word_id, surah = row
        first_word_id = None if first_word_id in {None, ""} else first_word_id
        last_word_id = None if last_word_id in {None, ""} else last_word_id
        surah = None if surah in {None, ""} else surah
        if (
            isinstance(page_number, bool)
            or not isinstance(page_number, int)
            or page_number not in pages
            or isinstance(line_number, bool)
            or not isinstance(line_number, int)
            or not 1 <= line_number <= 15
            or line_type not in {"ayah", "basmallah", "surah_name"}
            or is_centered not in {0, 1}
        ):
            raise ValueError("QPC 15-line layout contains an invalid line record")

        line: Dict[str, Any] = {
            "line_number": line_number,
            "line_type": line_type,
            "is_centered": bool(is_centered),
        }
        if line_type == "ayah":
            first = _positive_integer(first_word_id, "first word id")
            last = _positive_integer(last_word_id, "last word id")
            if first > last or first != previous_word_id + 1:
                raise ValueError("QPC 15-line layout has invalid or discontinuous word ranges")
            line["first_word_id"] = first
            line["last_word_id"] = last
            previous_word_id = last
        elif first_word_id is not None or last_word_id is not None:
            raise ValueError("Non-ayah layout lines must not contain word ranges")
        if line_type == "surah_name":
            surah_number = _positive_integer(surah, "surah number")
            if surah_number > 114:
                raise ValueError("QPC surah heading is out of range")
            line["surah_number"] = surah_number
        elif surah is not None:
            raise ValueError("Only surah heading lines may contain a surah number")
        pages[page_number].append(line)

    for page_number, lines in pages.items():
        if not lines or [line["line_number"] for line in lines] != list(
            range(1, len(lines) + 1)
        ):
            raise ValueError(f"QPC 15-line layout has invalid lines on page {page_number}")
    return {
        "name": name,
        "total_pages": total_pages,
        "lines_per_page": lines_per_page,
        "font_name": font_name,
        "pages": pages,
        "last_word_id": previous_word_id,
    }


def _qpc_15_line_page(page_number: int) -> Dict[str, Any]:
    permission = source_permission(QPC_LAYOUT_SOURCE_ID)
    if not permission_allows(permission, ["display"]):
        status = permission.get("status", "unknown")
        raise HTTPException(
            status_code=403,
            detail=f"Mushaf layout is unavailable for display (rights status: {status})",
        )

    layout_path = _qpc_15_line_layout_path()
    qpc_path = _qpc_v4_path()
    if not layout_path.is_file() or not qpc_path.is_file():
        raise HTTPException(status_code=503, detail="QPC 15-line layout data is unavailable")
    layout_stat = layout_path.stat()
    qpc_stat = qpc_path.stat()
    try:
        layout = _load_qpc_15_line_layout(
            str(layout_path.resolve()), layout_stat.st_mtime_ns, layout_stat.st_size
        )
        word_ayah_map = _load_qpc_word_ayah_map(
            str(qpc_path.resolve()), qpc_stat.st_mtime_ns, qpc_stat.st_size
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=503, detail="QPC 15-line layout data could not be loaded"
        ) from error
    if layout["last_word_id"] != len(word_ayah_map):
        raise HTTPException(
            status_code=503, detail="QPC 15-line layout does not match the QPC V4 word data"
        )

    lines = []
    for source_line in layout["pages"].get(page_number, []):
        line = dict(source_line)
        if line["line_type"] == "ayah":
            first = line["first_word_id"]
            last = line["last_word_id"]
            line["verse_keys"] = list(
                dict.fromkeys(word_ayah_map[word_id] for word_id in range(first, last + 1))
            )
        lines.append(line)
    return {
        "code": 200,
        "status": "OK",
        "data": {
            "name": layout["name"],
            "page_number": page_number,
            "total_pages": layout["total_pages"],
            "lines_per_page": layout["lines_per_page"],
            "font_name": layout["font_name"],
            "font_status": "unpublished_pending_proofreading",
            "glyph_rendering_enabled": False,
            "source": "QUL KFGQPC V4 Tajweed 15-line layout",
            "source_id": QPC_LAYOUT_SOURCE_ID,
            "rights_status": permission.get("status", "unknown"),
            "lines": lines,
        },
    }


@lru_cache(maxsize=1)
def _load_surah_info(source_path: str, modified_ns: int, file_size: int) -> Dict[str, Any]:
    del modified_ns, file_size
    with Path(source_path).open(encoding="utf-8") as source_file:
        records = json.load(source_file)
    if not isinstance(records, dict):
        raise ValueError("Surah information dataset must be an object")

    normalized: Dict[str, Any] = {}
    for key, record in records.items():
        if (
            not isinstance(key, str)
            or not key.isdigit()
            or str(int(key)) != key
            or not 1 <= int(key) <= 114
            or not isinstance(record, dict)
            or isinstance(record.get("surah_number"), bool)
            or record.get("surah_number") != int(key)
            or not isinstance(record.get("surah_name"), str)
            or not record["surah_name"].strip()
            or not isinstance(record.get("short_text"), str)
            or not isinstance(record.get("text"), str)
            or not record["text"].strip()
        ):
            raise ValueError(f"Invalid surah information record: {key!r}")

        parser = _PlainTextHTMLParser()
        parser.feed(record["text"])
        parser.close()
        text = re.sub(r"[ \t\f\v]+", " ", "".join(parser.parts))
        paragraphs = [part.strip() for part in re.split(r"\n+", text) if part.strip()]
        if not paragraphs:
            raise ValueError(f"Surah information record has no readable text: {key}")
        normalized[key] = {
            "surah_number": int(key),
            "surah_name": record["surah_name"].strip(),
            "short_text": record["short_text"].strip(),
            "text": "\n\n".join(paragraphs),
        }
    return normalized


def _surah_info(number: int) -> Dict[str, Any]:
    source_id = SURAH_INFO_SOURCE_ID
    permission = source_permission(source_id)
    if not permission_allows(permission, ["display"]):
        status = permission.get("status", "unknown")
        raise HTTPException(
            status_code=403,
            detail=f"Surah background reading is unavailable for display (rights status: {status})",
        )

    source_path = _surah_info_path()
    if not source_path.is_file():
        raise HTTPException(status_code=503, detail="Surah background reading is unavailable")
    stat = source_path.stat()
    try:
        records = _load_surah_info(str(source_path.resolve()), stat.st_mtime_ns, stat.st_size)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=503, detail="Surah background reading could not be loaded"
        ) from error
    record = records.get(str(number))
    if record is None:
        raise HTTPException(status_code=404, detail="Surah background reading was not found")
    return {
        "code": 200,
        "status": "OK",
        "data": {
            **record,
            "language": "id",
            "source": "QUL Surah Information",
            "source_id": source_id,
            "rights_status": permission.get("status", "unknown"),
            "rights_allowed_uses": permission.get("allowed_uses", []),
        },
    }


def _qpc_v4_surah(number: int) -> Dict[str, Any]:
    source_path = _qpc_v4_path()
    if not source_path.is_file():
        raise HTTPException(status_code=503, detail="QPC V4 Quran script is unavailable")
    stat = source_path.stat()
    try:
        verses = _load_qpc_v4_verses(
            str(source_path.resolve()), stat.st_mtime_ns, stat.st_size
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=503, detail="QPC V4 Quran script could not be loaded"
        ) from error
    surah_verses = [
        {
            **verse,
            "numberInSurah": verse["number_in_surah"],
            "script_type": verse["script_type"],
            "font_family": verse["font_family"],
        }
        for verse in verses
        if verse["surah_number"] == number
    ]
    if not surah_verses:
        raise HTTPException(status_code=404, detail="Surah is not present in QPC V4 data")
    return {
        "code": 200,
        "status": "OK",
        "data": {
            "ayahs": surah_verses,
            "source": "QUL QPC V4",
            "source_file": source_path.name,
        },
    }


async def _fetch_quran_cloud(path: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"https://api.alquran.cloud/v1{path}",
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
    except httpx.TimeoutException as error:
        raise HTTPException(status_code=504, detail="Quran provider request timed out") from error
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502, detail="Quran provider returned an unsuccessful response"
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(status_code=503, detail="Could not reach Quran provider") from error

    try:
        payload = response.json()
    except ValueError as error:
        raise HTTPException(
            status_code=502, detail="Quran provider returned invalid JSON"
        ) from error
    if not isinstance(payload, dict) or payload.get("code") != 200:
        raise HTTPException(status_code=502, detail="Quran provider returned invalid data")
    return payload


@router.get("/surahs")
async def list_surahs() -> Dict[str, Any]:
    return await _fetch_quran_cloud("/surah")


@router.get("/surahs/{surah_number}")
async def get_surah(
    surah_number: int = PathParameter(ge=1, le=114),
    edition: Literal["quran-uthmani", "th.thai", "ar.alafasy", "qpc-v4"] = Query(
        default="quran-uthmani"
    ),
) -> Dict[str, Any]:
    if edition == "qpc-v4":
        return _qpc_v4_surah(surah_number)
    return await _fetch_quran_cloud(f"/surah/{surah_number}/{edition}")


@router.get("/surahs/{surah_number}/info")
async def get_surah_info(
    surah_number: int = PathParameter(ge=1, le=114),
) -> Dict[str, Any]:
    return _surah_info(surah_number)


@router.get("/mushaf/15-line/pages/{page_number}")
async def get_qpc_15_line_page(
    page_number: int = PathParameter(ge=1, le=604),
) -> Dict[str, Any]:
    return _qpc_15_line_page(page_number)
