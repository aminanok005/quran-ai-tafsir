import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from services.api.app import app
from services.api.services.browser_identity import COOKIE_NAME, _decode_cookie, _signature


class Result:
    def __init__(self, value=None, rowcount=1):
        self.value = value
        self.rowcount = rowcount

    def mappings(self):
        return self

    def all(self):
        return []

    def one(self):
        return self.value

    def first(self):
        return self.value


class NotesConnection:
    def __init__(self, row=None):
        self.row = row
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append((sql, params or {}))
        if "INSERT INTO user_notes" in sql:
            return Result({
                "id": str(uuid4()),
                "title": params["title"],
                "content": params["content"],
                "surah_number": params["surah_number"],
                "ayah_number": params["ayah_number"],
                "source_label": params["source_label"],
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            })
        if "UPDATE user_notes" in sql:
            return Result(self.row)
        if "DELETE FROM user_notes" in sql:
            return Result(rowcount=0)
        return Result()


class NotesEngine:
    def __init__(self, row=None):
        self.connection = NotesConnection(row)

    def connect(self):
        return self.connection

    def begin(self):
        return self.connection


class WorkspaceTests(unittest.TestCase):
    def test_signed_browser_cookie_rejects_tampering(self):
        browser_id = uuid4()
        token = f"{browser_id}.{_signature(browser_id)}"
        self.assertEqual(_decode_cookie(token), browser_id)
        self.assertIsNone(_decode_cookie(f"{browser_id}.{_signature(uuid4())}"))

    def test_notes_are_scoped_to_distinct_signed_browser_cookies(self):
        with (
            patch("services.api.routers.workspace.get_engine", return_value=NotesEngine()),
            TestClient(app) as client,
        ):
            first = client.get("/api/v1/workspace/notes")
            first_cookie = client.cookies.get(COOKIE_NAME)
            client.cookies.clear()
            second = client.get("/api/v1/workspace/notes")
            second_cookie = client.cookies.get(COOKIE_NAME)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first_cookie, second_cookie)
        self.assertNotIn("browser_id", first.json()["data"] and str(first.json()["data"]))

    def test_note_write_requires_valid_fields_and_creates_browser_identity(self):
        engine = NotesEngine()
        with (
            patch("services.api.routers.workspace.get_engine", return_value=engine),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/workspace/notes",
                json={
                    "title": "Al-Fatihah 1:1",
                    "content": "Ayah notes",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "source_label": "Quran",
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["title"], "Al-Fatihah 1:1")
        self.assertTrue(any("INSERT INTO user_notes" in sql for sql, _ in engine.connection.statements))

    def test_notes_cannot_be_updated_or_deleted_by_another_browser(self):
        engine = NotesEngine(row=None)
        with (
            patch("services.api.routers.workspace.get_engine", return_value=engine),
            TestClient(app) as client,
        ):
            client.get("/api/v1/workspace/notes")
            note_id = str(uuid4())
            update = client.patch(f"/api/v1/workspace/notes/{note_id}", json={"title": "Other user's note"})
            delete = client.delete(f"/api/v1/workspace/notes/{note_id}")

        self.assertEqual(update.status_code, 404)
        self.assertEqual(delete.status_code, 404)
        self.assertTrue(all("browser_id = :browser_id" in sql for sql, _ in engine.connection.statements if "UPDATE user_notes" in sql or "DELETE FROM user_notes" in sql))

    def test_studio_blocks_unapproved_tafsir_derivatives(self):
        with (
            patch("services.api.config.settings.llm_api_key", "test-key"),
            patch("services.api.config.settings.llm_api_base_url", "https://llm.example.test/v1"),
            patch("services.api.config.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.get_engine", return_value=NotesEngine()),
            patch("services.api.routers.workspace.generate_artifact", new_callable=AsyncMock) as generate,
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "report",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "tafsir_book_id": "qf_tafsir_169",
                    "selected_sources": ["quran", "tafsir"],
                },
            )

        self.assertEqual(response.status_code, 403)
        generate.assert_not_awaited()

    def test_studio_returns_source_citations_and_validated_artifact(self):
        artifact = {
            "title": "A lesson",
            "summary": "Summary",
            "sections": [],
            "slides": [],
            "scenes": [],
            "questions": [],
            "flashcards": [],
            "rows": [],
        }
        with (
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "https://llm.example.test/v1"),
            patch("services.api.routers.workspace.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.generate_artifact", new_callable=AsyncMock, return_value=artifact),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "report",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "selected_sources": ["quran"],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["sources"][0]["label"], "Al-Fatihah 1:1")
        self.assertEqual(response.json()["data"]["evidence_status"], "AI-SYNTHESIS")


if __name__ == "__main__":
    unittest.main()
