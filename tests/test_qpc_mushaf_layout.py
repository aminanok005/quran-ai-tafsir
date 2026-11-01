import asyncio
import json
import sqlite3

import pytest
from fastapi import HTTPException

from services.api.routers.quran import (
    _load_qpc_15_line_layout,
    _qpc_15_line_page,
    get_qpc_15_line_page,
)


def _write_layout_database(path):
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE info (name TEXT, number_of_pages INTEGER, "
            "lines_per_page INTEGER, font_name TEXT)"
        )
        connection.execute(
            "INSERT INTO info VALUES (?, ?, ?, ?)",
            ("KFGQPC V4 Tajweed", 604, 15, "v4-tajweed"),
        )
        connection.execute(
            "CREATE TABLE pages (page_number INTEGER, line_number INTEGER, "
            "line_type TEXT, is_centered INTEGER, first_word_id INTEGER, "
            "last_word_id INTEGER, surah_number INTEGER)"
        )
        connection.executemany(
            "INSERT INTO pages VALUES (?, 1, 'ayah', 0, ?, ?, NULL)",
            [(page, page, page) for page in range(1, 605)],
        )


def _write_qpc_words(path):
    path.write_text(
        json.dumps(
            {
                f"1:{word_id}:1": {
                    "id": word_id,
                    "surah": "1",
                    "ayah": str(word_id),
                    "word": "1",
                    "location": f"1:{word_id}:1",
                    "text": "x",
                }
                for word_id in range(1, 605)
            }
        ),
        encoding="utf-8",
    )


def _approved_display_rights():
    return {
        "status": "approved",
        "license": "test license",
        "allowed_uses": ["display"],
        "reviewed_by": "test reviewer",
        "reviewed_at": "2025-01-01T00:00:00+00:00",
        "evidence_refs": ["https://example.test/permission"],
        "decision_note": "Synthetic fixture permission for tests",
    }


def test_qpc_layout_parser_validates_604_pages_and_15_line_declaration(tmp_path):
    database = tmp_path / "layout.db"
    _write_layout_database(database)

    layout = _load_qpc_15_line_layout(
        str(database.resolve()), database.stat().st_mtime_ns, database.stat().st_size
    )

    assert layout["total_pages"] == 604
    assert layout["lines_per_page"] == 15
    assert layout["last_word_id"] == 604
    assert len(layout["pages"]) == 604


def test_qpc_page_api_maps_word_ranges_to_ayah_references(tmp_path, monkeypatch):
    database = tmp_path / "layout.db"
    qpc_words = tmp_path / "qpc-v4.json"
    _write_layout_database(database)
    _write_qpc_words(qpc_words)
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(
        json.dumps({"sources": {"qul:qpc-v4-tajweed-15-lines": _approved_display_rights()}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))
    monkeypatch.setenv("QURAN_QPC_15_LINE_LAYOUT_PATH", str(database))
    monkeypatch.setenv("QURAN_QPC_V4_PATH", str(qpc_words))

    page = asyncio.run(get_qpc_15_line_page(1))["data"]

    assert page["page_number"] == 1
    assert page["total_pages"] == 604
    assert page["lines_per_page"] == 15
    assert page["glyph_rendering_enabled"] is False
    assert page["font_status"] == "unpublished_pending_proofreading"
    assert page["lines"][0]["verse_keys"] == ["1:1"]


def test_qpc_page_api_denies_display_without_source_permission(tmp_path, monkeypatch):
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(json.dumps({"sources": {}}), encoding="utf-8")
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    with pytest.raises(HTTPException) as error:
        _qpc_15_line_page(1)

    assert error.value.status_code == 403
