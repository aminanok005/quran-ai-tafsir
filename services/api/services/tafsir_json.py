"""Read-only access to the repository's local tafsir JSON files."""

import html
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


TAFSIR_JSON_SOURCES = {
    "ibn_kathir": {
        "file": "ar-tafsir-ibn-kathir.json",
        "book_id": "tafsir_ibn_kathir",
        "title": "Tafsir al-Qur'an al-Azim",
        "title_ar": "تفسير القرآن العظيم",
        "scholar": "Ibn Kathir",
        "edition": "Dar Taybah",
        "url": "https://shamela.ws/book/16559",
    },
    "al_tabari": {
        "file": "ar-tafsir-al-tabari.json",
        "book_id": "jami_al_bayan",
        "title": "Jami' al-Bayan",
        "title_ar": "جامع البيان",
        "scholar": "Al-Tabari",
        "edition": "Dar al-Kutub al-Ilmiyah",
        "url": "https://shamela.ws/book/16558",
    },
    "al_qurtubi": {
        "file": "ar-tafseer-al-qurtubi.json",
        "book_id": "jami_ahkam",
        "title": "Al-Jami' li-Ahkam al-Qur'an",
        "title_ar": "الجامع لأحكام القرآن",
        "scholar": "Al-Qurtubi",
        "edition": "Dar al-Kutub al-Ilmiyah",
        "url": "https://shamela.ws/book/16560",
    },
    "al_saadi": {
        "file": "tafsir-as-saadi.json",
        "book_id": "taysir_karim",
        "title": "Taysir al-Karim al-Rahman",
        "title_ar": "تيسير الكريم الرحمن",
        "scholar": "Al-Sa'di",
        "edition": "Dar al-Kutub al-Ilmiyah",
        "url": "https://shamela.ws/book/16561",
    },
}

_DATA_DIRECTORY = Path(__file__).resolve().parents[3] / "data-tafsir"


class TafsirJsonDataError(RuntimeError):
    """Raised when a configured local tafsir JSON file cannot be read."""


@lru_cache(maxsize=len(TAFSIR_JSON_SOURCES))
def load_tafsir_json(agent_type: str) -> dict[str, Any]:
    source = TAFSIR_JSON_SOURCES.get(agent_type)
    if source is None:
        raise KeyError(agent_type)

    path = _DATA_DIRECTORY / source["file"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TafsirJsonDataError(f"Unable to read configured tafsir source: {agent_type}") from error
    if not isinstance(data, dict):
        raise TafsirJsonDataError(f"Configured tafsir source is not an object: {agent_type}")
    return data


def get_tafsir_json_text(agent_type: str, surah: int, ayah: int) -> str | None:
    data = load_tafsir_json(agent_type)
    entry = data.get(f"{surah}:{ayah}")
    if isinstance(entry, dict):
        raw_text = entry.get("text")
    else:
        raw_text = entry
    if not isinstance(raw_text, str):
        return None

    plain_text = re.sub(r"<[^>]+>", "", raw_text)
    return " ".join(html.unescape(plain_text).split())


def split_tafsir_text(source_text: str, chunk_size: int = 6000) -> list[str]:
    """Split long source passages on word boundaries for complete translation."""
    remaining = source_text.strip()
    chunks = []
    while len(remaining) > chunk_size:
        boundary = remaining.rfind(" ", 0, chunk_size + 1)
        if boundary < chunk_size // 2:
            boundary = chunk_size
        chunks.append(remaining[:boundary].strip())
        remaining = remaining[boundary:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks
