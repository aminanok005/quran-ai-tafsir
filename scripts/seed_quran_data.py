#!/usr/bin/env python3
"""Seed the canonical quran_ayahs table from the Quran API."""

import logging
import os
from typing import Any


EXPECTED_AYAH_COUNT = 6236
SURAH_AYAH_COUNTS = (
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128,
    111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73,
    54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60,
    49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52,
    44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19,
    26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3,
    6, 3, 5, 4, 5, 6,
)
SURAH_COUNT = len(SURAH_AYAH_COUNTS)
VERSES_PER_PAGE = 50
VERSE_FIELDS = (
    "text_uthmani,text_uthmani_simple,text_imlaei,text_indopak,juz_number,"
    "hizb_number,rub_el_hizb_number,page_number,sajdah_type,sajdah_number"
)
QURAN_API_BASE_URL = os.environ.get(
    "QURAN_API_BASE_URL",
    "https://apis.quran.foundation",
).rstrip("/")
CONTENT_API_BASE_URL = (
    QURAN_API_BASE_URL
    if QURAN_API_BASE_URL.endswith("/content/api/v4")
    else f"{QURAN_API_BASE_URL}/content/api/v4"
)

INSERT_AYAH_SQL = """
    INSERT INTO quran_ayahs (
        surah_number, ayah_number, text_uthmani, text_simple, text_complex,
        text_indopak, juz_number, hizb_number, rub_el_hizb_number, page_number,
        sajdah, sajdah_number, text_checksum
    ) VALUES (
        :surah_number, :ayah_number, :text_uthmani, :text_simple, :text_complex,
        :text_indopak, :juz_number, :hizb_number, :rub_el_hizb_number, :page_number,
        :sajdah, :sajdah_number, :text_checksum
    )
    ON CONFLICT (surah_number, ayah_number) DO UPDATE SET
        text_uthmani = EXCLUDED.text_uthmani,
        text_simple = EXCLUDED.text_simple,
        text_complex = EXCLUDED.text_complex,
        text_indopak = EXCLUDED.text_indopak,
        juz_number = EXCLUDED.juz_number,
        hizb_number = EXCLUDED.hizb_number,
        rub_el_hizb_number = EXCLUDED.rub_el_hizb_number,
        page_number = EXCLUDED.page_number,
        sajdah = EXCLUDED.sajdah,
        sajdah_number = EXCLUDED.sajdah_number,
        text_checksum = EXCLUDED.text_checksum,
        updated_at = CURRENT_TIMESTAMP
"""

logger = logging.getLogger(__name__)


def normalize_ayah(surah_number: int, data: dict[str, Any]) -> dict[str, Any]:
    """Map one API ayah to columns in the canonical database schema."""
    ayah_data = data.get("ayah", data)
    if not isinstance(ayah_data, dict):
        raise ValueError(f"Invalid ayah payload for surah {surah_number}")

    ayah_number = ayah_data.get(
        "verse_number",
        ayah_data.get("ayah_number", ayah_data.get("number")),
    )
    text_uthmani = ayah_data.get("text_uthmani")
    if not isinstance(ayah_number, int) or ayah_number < 1:
        raise ValueError(f"Invalid ayah number in surah {surah_number}")
    if not isinstance(text_uthmani, str) or not text_uthmani.strip():
        raise ValueError(f"Missing Uthmani text for {surah_number}:{ayah_number}")

    sajdah_type = ayah_data.get("sajdah_type")
    if sajdah_type is not None and sajdah_type not in {"obligatory", "recommended"}:
        raise ValueError(f"Invalid sajdah type for {surah_number}:{ayah_number}")

    return {
        "surah_number": surah_number,
        "ayah_number": ayah_number,
        "text_uthmani": text_uthmani,
        "text_simple": ayah_data.get(
            "text_uthmani_simple",
            ayah_data.get("text_simple"),
        ),
        "text_complex": ayah_data.get("text_imlaei", ayah_data.get("text_complex")),
        "text_indopak": ayah_data.get("text_indopak"),
        "juz_number": ayah_data.get("juz_number"),
        "hizb_number": ayah_data.get("hizb_number"),
        "rub_el_hizb_number": ayah_data.get("rub_el_hizb_number"),
        "page_number": ayah_data.get("page_number"),
        "sajdah": (
            sajdah_type is not None
            if "sajdah_type" in ayah_data
            else bool(ayah_data.get("sajdah", False))
        ),
        "sajdah_number": ayah_data.get("sajdah_number"),
        "text_checksum": ayah_data.get("text_checksum"),
    }


def validate_ayahs(
    ayahs: list[dict[str, Any]],
    expected_count: int = EXPECTED_AYAH_COUNT,
) -> None:
    """Reject incomplete or duplicate API results before writing to the database."""
    if len(ayahs) != expected_count:
        raise ValueError(
            f"Expected {expected_count} Quran ayahs, received {len(ayahs)}"
        )

    keys = [(ayah["surah_number"], ayah["ayah_number"]) for ayah in ayahs]
    if len(set(keys)) != len(keys):
        raise ValueError("Quran API returned duplicate surah/ayah numbers")

    actual_counts = [0] * SURAH_COUNT
    for surah_number, ayah_number in keys:
        if not 1 <= surah_number <= SURAH_COUNT:
            raise ValueError(f"Invalid surah number: {surah_number}")
        actual_counts[surah_number - 1] += 1
        if not 1 <= ayah_number <= SURAH_AYAH_COUNTS[surah_number - 1]:
            raise ValueError(f"Invalid ayah number: {surah_number}:{ayah_number}")

    if tuple(actual_counts) != SURAH_AYAH_COUNTS:
        raise ValueError("Quran API returned an incomplete or invalid surah ayah set")


def _json_list(response: Any, key: str) -> tuple[list[dict[str, Any]], Any]:
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Quran API returned an invalid object response")
    items = payload.get(key)
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError("Quran API returned an invalid list response")
    return items, payload.get("pagination")


def get_api_token() -> str:
    import requests

    client_id = os.environ.get("QURAN_API_CLIENT_ID")
    client_secret = os.environ.get("QURAN_API_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Set QURAN_API_CLIENT_ID and QURAN_API_CLIENT_SECRET before seeding"
        )

    response = requests.post(
        f"{QURAN_API_BASE_URL.removesuffix('/content/api/v4')}/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("Quran API token response did not contain an access token")
    return token


def fetch_surah_ayahs(surah_number: int, token: str) -> list[dict[str, Any]]:
    import requests

    ayahs = []
    page = 1
    total_pages = None
    while total_pages is None or page <= total_pages:
        response = requests.get(
            f"{CONTENT_API_BASE_URL}/verses/by_chapter/{surah_number}",
            headers={
                "x-auth-token": token,
                "x-client-id": os.environ["QURAN_API_CLIENT_ID"],
            },
            params={
                "fields": VERSE_FIELDS,
                "per_page": VERSES_PER_PAGE,
                "page": page,
            },
            timeout=30,
        )
        page_ayahs, pagination = _json_list(response, "verses")
        if not isinstance(pagination, dict):
            raise ValueError("Quran API response is missing pagination metadata")
        response_page = pagination.get("current_page")
        response_total_pages = pagination.get("total_pages")
        if response_page != page or not isinstance(response_total_pages, int):
            raise ValueError("Quran API returned invalid pagination metadata")
        if total_pages is None:
            if response_total_pages < 1:
                raise ValueError("Quran API returned an empty pagination range")
            total_pages = response_total_pages
        elif response_total_pages != total_pages:
            raise ValueError("Quran API pagination changed while fetching a surah")

        ayahs.extend(page_ayahs)
        page += 1

    expected_count = SURAH_AYAH_COUNTS[surah_number - 1]
    if len(ayahs) != expected_count:
        raise ValueError(
            f"Expected {expected_count} ayahs for surah {surah_number}, received {len(ayahs)}"
        )
    return ayahs


def fetch_all_ayahs(token: str) -> list[dict[str, Any]]:
    ayahs = [
        normalize_ayah(surah_number, item)
        for surah_number in range(1, SURAH_COUNT + 1)
        for item in fetch_surah_ayahs(surah_number, token)
    ]
    validate_ayahs(ayahs)
    return ayahs


def seed_quran_data() -> int:
    from sqlalchemy import create_engine, text

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Set DATABASE_URL before seeding")

    token = get_api_token()
    ayahs = fetch_all_ayahs(token)

    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(INSERT_AYAH_SQL), ayahs)
    finally:
        engine.dispose()

    logger.info("Seeded %s Quran ayahs", len(ayahs))
    return len(ayahs)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    seed_quran_data()
