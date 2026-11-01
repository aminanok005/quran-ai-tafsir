import json
import sqlite3

from fastapi.testclient import TestClient

from services.api.main import app
from services.api.routers import tafsir


def _create_database(path):
    with sqlite3.connect(path) as connection:
        connection.execute(
            """CREATE TABLE tafsir (
                ayah_key TEXT, group_ayah_key TEXT, from_ayah TEXT, to_ayah TEXT,
                ayah_keys TEXT, text TEXT
            )"""
        )


def test_tafsir_chat_endpoint_contract_and_agent_selection(tmp_path, monkeypatch):
    _create_database(tmp_path / "ar-tafsir-ibn-kathir.db")
    monkeypatch.setenv("QURAN_TAFSIR_DB_DIR", str(tmp_path))
    rights_manifest = tmp_path / "rights.json"
    rights_manifest.write_text(
        json.dumps(
            {
                "sources": {
                    "qul:ar-tafsir-ibn-kathir": {
                        "status": "approved",
                        "license": "test license",
                        "reviewed_by": "reviewer",
                        "reviewed_at": "2025-01-01T00:00:00+00:00",
                        "evidence_refs": ["https://example.test/license"],
                        "decision_note": "Reviewed for test coverage",
                        "allowed_uses": ["display", "quotation", "ai_processing"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(rights_manifest))

    class FakeAgent:
        def __init__(self, config):
            self.config = config

        async def respond(self, ayah_key, message, history):
            return {
                "status": "answered",
                "ayah_key": ayah_key,
                "answer_language": "th",
                "answer_th": "คำอธิบายจากแหล่งอ้างอิง",
                "sources": [{"language": self.config.language}],
                "history_count": len(history),
            }

    monkeypatch.setattr(tafsir, "TafsirChatAgent", FakeAgent)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tafsir/chat",
            json={
                "surah": 1,
                "ayah": 1,
                "scholar_id": "ibn-kathir",
                "message": "ช่วยอธิบายอายะฮ์นี้",
                "history": [{"role": "user", "content": "คำถามก่อนหน้า"}],
            },
        )
        agents_response = client.get("/api/v1/tafsir/agents")

    assert response.status_code == 200
    assert response.json()["ayah_key"] == "1:1"
    assert response.json()["answer_language"] == "th"
    assert response.json()["history_count"] == 1
    assert agents_response.status_code == 200
    assert agents_response.json()["agents"][0]["database_available"] is True
    assert agents_response.json()["agents"][0]["enabled"] is True


def test_tafsir_chat_rejects_unknown_scholar(tmp_path, monkeypatch):
    monkeypatch.setenv("QURAN_TAFSIR_DB_DIR", str(tmp_path))
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tafsir/chat",
            json={
                "surah": 1,
                "ayah": 1,
                "scholar_id": "unknown-scholar",
                "message": "อธิบาย",
            },
        )

    assert response.status_code == 422


def test_tafsir_chat_blocks_unapproved_corpus(tmp_path, monkeypatch):
    _create_database(tmp_path / "ar-tafsir-ibn-kathir.db")
    monkeypatch.setenv("QURAN_TAFSIR_DB_DIR", str(tmp_path))
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(tmp_path / "missing-rights.json"))

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tafsir/chat",
            json={
                "surah": 1,
                "ayah": 1,
                "scholar_id": "ibn-kathir",
                "message": "อธิบาย",
            },
        )

    assert response.status_code == 403
