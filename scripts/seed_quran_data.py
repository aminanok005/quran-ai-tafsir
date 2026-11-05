#!/usr/bin/env python3
"""Seed the canonical quran_ayahs table from the Quran API."""

import logging
import os
from typing import Any


EXPECTED_AYAH_COUNT = 6236
SURAH_COUNT = 114
QURAN_API_BASE_URL = os.environ.get(
    "QURAN_API_BASE_URL",
    "https://apis.quran.foundation",
).rstrip("/")

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

    ayah_number = ayah_data.get("ayah_number", ayah_data.get("number"))
    text_uthmani = ayah_data.get("text_uthmani")
    if not isinstance(ayah_number, int) or ayah_number < 1:
        raise ValueError(f"Invalid ayah number in surah {surah_number}")
    if not isinstance(text_uthmani, str) or not text_uthmani.strip():
        raise ValueError(f"Missing Uthmani text for {surah_number}:{ayah_number}")

    return {
        "surah_number": surah_number,
        "ayah_number": ayah_number,
        "text_uthmani": text_uthmani,
        "text_simple": ayah_data.get("text_simple"),
        "text_complex": ayah_data.get("text_complex"),
        "text_indopak": ayah_data.get("text_indopak"),
        "juz_number": ayah_data.get("juz_number"),
        "hizb_number": ayah_data.get("hizb_number"),
        "rub_el_hizb_number": ayah_data.get("rub_el_hizb_number"),
        "page_number": ayah_data.get("page_number"),
        "sajdah": bool(ayah_data.get("sajdah", False)),
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


def _json_list(response: Any, *keys: str) -> list[dict[str, Any]]:
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        for key in keys:
            if key in payload:
                payload = payload[key]
                break
    if not isinstance(payload, list) or not all(
        isinstance(item, dict) for item in payload
    ):
        raise ValueError("Quran API returned an invalid list response")
    return payload


def get_api_token() -> str:
    import requests

    client_id = os.environ.get("QURAN_API_CLIENT_ID")
    client_secret = os.environ.get("QURAN_API_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Set QURAN_API_CLIENT_ID and QURAN_API_CLIENT_SECRET before seeding"
        )

    response = requests.post(
        f"{QURAN_API_BASE_URL}/oauth/token",
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

    response = requests.get(
        f"{QURAN_API_BASE_URL}/surahs/{surah_number}/ayahs",
        headers={
            "Authorization": f"Bearer {token}",
            "X-API-Key": os.environ["QURAN_API_CLIENT_ID"],
        },
        timeout=30,
    )
    return _json_list(response, "ayahs", "data")


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
