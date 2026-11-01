import asyncio
import json
import sqlite3
from pathlib import Path

import httpx
import pytest

from services.tafsir.agents import get_agent_config
from services.tafsir.chat_agent import TafsirChatAgent
from services.tafsir.dataset_builder import (
    approved_finetuning_records,
    iter_rag_records,
    write_rag_corpus,
)


def _create_dataset(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """CREATE TABLE tafsir (
                ayah_key TEXT,
                group_ayah_key TEXT,
                from_ayah TEXT,
                to_ayah TEXT,
                ayah_keys TEXT,
                text TEXT
            )"""
        )
        connection.executemany(
            "INSERT INTO tafsir VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("1:1", "1:1", "1:1", "1:2", "1:1,1:2", "<p>alpha beta gamma delta</p>"),
                ("1:2", "1:1", "", "", "", ""),
            ],
        )


def _approved_rights(allowed_uses):
    return {
        "status": "approved",
        "license": "test license",
        "allowed_uses": allowed_uses,
        "reviewed_by": "reviewer",
        "reviewed_at": "2025-01-01T00:00:00+00:00",
        "evidence_refs": ["https://example.test/license"],
        "decision_note": "Reviewed for test coverage",
    }


def _write_rights(path: Path, source_id: str, allowed_uses) -> None:
    path.write_text(
        json.dumps({"sources": {source_id: _approved_rights(allowed_uses)}}),
        encoding="utf-8",
    )


def test_rag_export_preserves_source_and_ayah_group_mapping(tmp_path, monkeypatch):
    database = tmp_path / "ar-tafsir-ibn-kathir.db"
    _create_dataset(database)
    rights_manifest = tmp_path / "rights.json"
    _write_rights(
        rights_manifest,
        "qul:ar-tafsir-ibn-kathir",
        ["display", "quotation", "ai_processing", "storage", "indexing"],
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    records = list(iter_rag_records(database, max_chars=10))

    assert len(records) > 1
    assert "".join(record["original_text"] for record in records).replace(" ", "") == (
        "alphabetagammadelta"
    )
    assert all(record["ayah_range"] == "1:1-1:2" for record in records)
    assert all(record["ayah_keys"] == ["1:1", "1:2"] for record in records)
    assert all(record["rights_status"] == "approved" for record in records)
    assert all(record["verification_status"] == "not_reviewed" for record in records)


def test_rag_export_requires_storage_and_indexing_rights(tmp_path, monkeypatch):
    database = tmp_path / "ar-tafsir-ibn-kathir.db"
    _create_dataset(database)
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(json.dumps({"sources": {}}), encoding="utf-8")
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    with pytest.raises(PermissionError, match="storage and indexing"):
        list(iter_rag_records(database))


def test_rag_export_fails_instead_of_silently_omitting_missing_books(tmp_path):
    with pytest.raises(FileNotFoundError, match="ar-tafsir-al-tabari.db"):
        write_rag_corpus(source_dir=tmp_path, output_path=tmp_path / "rag.jsonl")


def test_rag_export_carries_reviewed_rights_metadata(tmp_path, monkeypatch):
    database = tmp_path / "ar-tafsir-ibn-kathir.db"
    _create_dataset(database)
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(
        json.dumps(
            {
                "sources": {
                    "qul:ar-tafsir-ibn-kathir": {
                        **_approved_rights(
                            [
                                "display",
                                "quotation",
                                "ai_processing",
                                "storage",
                                "indexing",
                            ]
                        ),
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    record = next(iter_rag_records(database))

    assert record["schema_version"] == 1
    assert record["rights_status"] == "approved"
    assert record["license"] == "test license"
    assert record["allowed_uses"] == [
        "display",
        "quotation",
        "ai_processing",
        "storage",
        "indexing",
    ]


def test_finetuning_export_requires_explicit_rights_and_human_review():
    annotation = {
        "source_id": "qul:ar-tafsir-ibn-kathir",
        "ayah_key": "1:1",
        "human_reviewed": True,
        "reviewed_by": "reviewer-1",
        "messages": [
            {"role": "user", "content": "Explain ayah 1:1"},
            {"role": "assistant", "content": "Reviewed explanation"},
        ],
    }

    assert approved_finetuning_records([annotation], {"sources": {}}) == []

    rights = {
        "sources": {
            "qul:ar-tafsir-ibn-kathir": {
                **_approved_rights(["model_training"]),
            }
        }
    }
    assert approved_finetuning_records([annotation], rights) == [
        {
            "source_id": "qul:ar-tafsir-ibn-kathir",
            "ayah_key": "1:1",
            "reviewed_by": "reviewer-1",
            "messages": annotation["messages"],
        }
    ]
    assert approved_finetuning_records(
        [{**annotation, "human_reviewed": False}], rights
    ) == []


def test_chat_agent_returns_direct_source_separately_from_generated_thai(tmp_path, monkeypatch):
    database = tmp_path / "ar-tafsir-ibn-kathir.db"
    _create_dataset(database)
    config = get_agent_config("ibn-kathir", database_dir=tmp_path)
    monkeypatch.setenv("TAFSIR_LLM_API_KEY", "test-key")
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(
        json.dumps(
            {
                "sources": {
                    "qul:ar-tafsir-ibn-kathir": {
                        **_approved_rights(
                            ["display", "quotation", "ai_processing"]
                        ),
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    def llm_response(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert "alpha beta gamma delta" in payload["messages"][0]["content"]
        assert config.focus in payload["messages"][0]["content"]
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "คำอธิบายที่สร้างโดย AI"}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(llm_response))
    result = asyncio.run(
        TafsirChatAgent(config, http_client=client).respond("1:1", "อธิบายอายะฮ์นี้")
    )
    asyncio.run(client.aclose())

    assert result["answer_th"] == "คำอธิบายที่สร้างโดย AI"
    assert result["sources"][0]["original_text"] == "alpha beta gamma delta"
    assert result["sources"][0]["language"] == "ar"
    assert result["sources"][0]["rights_status"] == "approved"
    assert result["sources"][0]["license"] == "test license"
    assert result["sources"][0]["verification_status"] == "not_reviewed"
    assert "AI" in result["disclaimer_th"]


def test_saadi_agent_can_choose_indonesian_source(tmp_path):
    config = get_agent_config("al-saadi", source_language="id", database_dir=tmp_path)

    assert config.language == "id"
    assert config.database_path.name == "id-tafsir-as-saadi.db"
