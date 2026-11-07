"""Canonical Quran structure metadata shared by API and data-seeding code."""

import json
from pathlib import Path
from typing import Sequence

EXPECTED_AYAH_COUNT = 6236
SURAH_COUNT = 114
_COUNTS_PATH = Path(__file__).resolve().parents[1] / "data" / "surah_ayah_counts.json"


def validate_surah_ayah_counts(counts: Sequence[object]) -> tuple[int, ...]:
    """Validate and freeze the canonical ayah count for each surah."""
    if len(counts) != SURAH_COUNT:
        raise ValueError(f"Expected {SURAH_COUNT} surah ayah counts, received {len(counts)}")
    if any(type(count) is not int for count in counts):
        raise ValueError("Surah ayah counts must be integers")
    if any(count <= 0 for count in counts):
        raise ValueError("Surah ayah counts must be positive")
    if sum(counts) != EXPECTED_AYAH_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_AYAH_COUNT} Quran ayahs, received {sum(counts)}"
        )
    return tuple(counts)


with _COUNTS_PATH.open(encoding="utf-8") as _counts_file:
    SURAH_AYAH_COUNTS = validate_surah_ayah_counts(json.load(_counts_file))


def is_valid_ayah(surah_number: int, ayah_number: int) -> bool:
    """Return whether a surah and ayah pair is within the canonical Quran bounds."""
    if type(surah_number) is not int or type(ayah_number) is not int:
        return False
    if not 1 <= surah_number <= SURAH_COUNT:
        return False
    return 1 <= ayah_number <= SURAH_AYAH_COUNTS[surah_number - 1]
