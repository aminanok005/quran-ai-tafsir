import asyncio
import json
from pathlib import Path

import pytest

from services.tafsir.agents import get_agent_config
from services.tafsir.dataset_builder import iter_rag_records
from services.tafsir.source_retrieval import TafsirSourceRetrieval


def _write_dataset(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "1:1": {
                    "text": "<p>ข้อความตัฟซีรต้นฉบับ</p>",
                    "ayah_keys": ["1:1", "1:2"],
                },
                "1:2": "1:1",
                "1:3": {"text": "", "ayah_keys": ["1:3"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _approved_rights(uses):
    return {
        "status": "approved",
        "license": "test license",
        "allowed_uses": uses,
        "reviewed_by": "test reviewer",
        "reviewed_at": "2025-01-01T00:00:00+00:00",
        "evidence_refs": ["https://example.test/permission"],
        "decision_note": "Synthetic fixture permission for tests",
    }


def test_json_retrieval_resolves_grouped_ayah_and_preserves_provenance(tmp_path):
    dataset = tmp_path / "ar-tafsir-ibn-kathir.json"
    _write_dataset(dataset)
    retrieval = TafsirSourceRetrieval(str(dataset))

    sources = asyncio.run(retrieval.retrieve("1:2", {}, "source-grounded"))

    assert len(sources) == 1
    assert sources[0]["original_text"] == "ข้อความตัฟซีรต้นฉบับ"
    assert sources[0]["source_backend"] == "qul_json"
    assert sources[0]["ayah_key"] == "1:2"
    assert sources[0]["group_ayah_key"] == "1:1"
    assert sources[0]["ayah_keys"] == ["1:1", "1:2"]
    assert sources[0]["ayah_range"] == "1:1-1:2"
    assert sources[0]["verified"] is False
    assert sources[0]["rights_status"] == "unknown"


def test_json_retrieval_does_not_create_citations_for_empty_or_invalid_keys(tmp_path):
    dataset = tmp_path / "ar-tafsir-ibn-kathir.json"
    _write_dataset(dataset)
    retrieval = TafsirSourceRetrieval(str(dataset))

    assert asyncio.run(retrieval.retrieve("1:3", {}, "source-grounded")) == []
    with pytest.raises(ValueError, match="Invalid Quran ayah key"):
        asyncio.run(retrieval.retrieve("0:1", {}, "source-grounded"))


def test_agent_config_prefers_json_and_keeps_database_fallback(tmp_path):
    json_source = tmp_path / "ar-tafsir-ibn-kathir.json"
    json_source.touch()

    assert get_agent_config("ibn-kathir", database_dir=tmp_path).database_path == json_source

    json_source.unlink()
    database = tmp_path / "ar-tafsir-ibn-kathir.db"
    database.touch()
    assert get_agent_config("ibn-kathir", database_dir=tmp_path).database_path == database


def test_json_rag_export_still_requires_storage_and_indexing_rights(tmp_path, monkeypatch):
    dataset = tmp_path / "ar-tafsir-ibn-kathir.json"
    _write_dataset(dataset)
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(json.dumps({"sources": {}}), encoding="utf-8")
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    with pytest.raises(PermissionError, match="storage and indexing"):
        list(iter_rag_records(dataset))


def test_json_rag_export_preserves_mapping_after_explicit_permission(tmp_path, monkeypatch):
    dataset = tmp_path / "ar-tafsir-ibn-kathir.json"
    _write_dataset(dataset)
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(
        json.dumps(
            {
                "sources": {
                    "qul:ar-tafsir-ibn-kathir": _approved_rights(["storage", "indexing"])
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    records = list(iter_rag_records(dataset))

    assert len(records) == 1
    assert records[0]["source_backend"] == "qul_json"
    assert records[0]["ayah_key"] == "1:1"
    assert records[0]["group_ayah_key"] == "1:1"
    assert records[0]["ayah_keys"] == ["1:1", "1:2"]
    assert records[0]["original_text"] == "ข้อความตัฟซีรต้นฉบับ"
