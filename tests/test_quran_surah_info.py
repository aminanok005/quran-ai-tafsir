import asyncio
import json

import pytest
from fastapi import HTTPException

from services.api.routers.quran import _load_surah_info, get_surah_info


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


def _write_surah_info(path):
    path.write_text(
        json.dumps(
            {
                "1": {
                    "surah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "short_text": "Ringkasan surah.",
                    "text": "<p>Bagian pertama.</p><h2>Tema</h2><p>Bagian kedua.</p>"
                    "<script>unsafe()</script>",
                },
                "2": {
                    "surah_number": 2,
                    "surah_name": "Al-Baqarah",
                    "short_text": "",
                    "text": "<p>Ringkasan.</p>",
                },
            }
        ),
        encoding="utf-8",
    )


def test_surah_background_display_requires_explicit_rights(tmp_path, monkeypatch):
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(json.dumps({"sources": {}}), encoding="utf-8")
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    with pytest.raises(HTTPException) as error:
        asyncio.run(get_surah_info(1))

    assert error.value.status_code == 403


def test_surah_background_returns_clean_text_and_source_provenance(tmp_path, monkeypatch):
    dataset = tmp_path / "surah-info-id.json"
    _write_surah_info(dataset)
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(
        json.dumps(
            {"sources": {"qul:surah-info-id": _approved_display_rights()}}
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))
    monkeypatch.setenv("QURAN_SURAH_INFO_ID_PATH", str(dataset))

    result = asyncio.run(get_surah_info(1))

    assert result["data"]["surah_name"] == "Al-Fatihah"
    assert result["data"]["short_text"] == "Ringkasan surah."
    assert result["data"]["text"] == "Bagian pertama.\n\nTema\n\nBagian kedua."
    assert result["data"]["language"] == "id"
    assert result["data"]["source_id"] == "qul:surah-info-id"
    assert result["data"]["rights_status"] == "approved"
    assert result["data"]["rights_allowed_uses"] == ["display"]


def test_surah_background_rejects_malformed_dataset_records(tmp_path):
    dataset = tmp_path / "surah-info-id.json"
    dataset.write_text(json.dumps({"1": {"surah_number": 2}}), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid surah information record"):
        _load_surah_info(str(dataset), dataset.stat().st_mtime_ns, dataset.stat().st_size)
