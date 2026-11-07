import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from services.api.app import app
from services.api.services.browser_identity import COOKIE_NAME, _decode_cookie, _signature
from services.api.services.quran_foundation_tafsir import QuranFoundationTafsir
from services.api.services.studio_generation import StudioGenerationError


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


class FakeQfClient:
    def __init__(self):
        self.content_api_url = "https://apis-prelive.quran.foundation/content/api/v4"
        self.cached_passages = {}
        self.cache_calls = []
        self.fetch_calls = []

    def add_cached_passage(self, resource_id=168, surah=1, ayah=1, *, verse_key="1:1"):
        passage = QuranFoundationTafsir(
            resource_id=resource_id,
            resource_name="Tafsir Ibn Kathir",
            language_name="english",
            slug="en-tafisr-ibn-kathir",
            verse_key=verse_key,
            text="Cached Quran Foundation Tafsir source",
        )
        self.cached_passages[(resource_id, surah, ayah)] = passage
        return passage

    def get_cached_ayah(self, *key):
        self.cache_calls.append(key)
        return self.cached_passages.get(key)

    async def fetch_ayah(self, *args):
        self.fetch_calls.append(args)
        raise AssertionError("Studio must not fetch Tafsir during artifact generation")


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
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.config.settings.quran_tafsir_resource_map", {"ibn_kathir": 168}),
            patch("services.api.config.settings.llm_api_key", "test-key"),
            patch("services.api.config.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
            patch("services.api.config.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.get_engine", return_value=object()),
            patch("services.api.routers.workspace._get_api_source_permission", return_value=None),
            patch("services.api.routers.workspace.get_qf_tafsir_client") as get_qf_client,
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
                    "tafsir_book_id": "qf_tafsir_168",
                    "selected_sources": ["quran", "tafsir"],
                },
            )

        self.assertEqual(response.status_code, 403)
        get_qf_client.assert_not_called()
        generate.assert_not_awaited()

    def test_studio_uses_only_cached_qf_tafsir_source(self):
        artifact = {
            "title": "A lesson",
            "summary": "Summary",
            "content": {"segments": []},
        }
        source_permission = {
            "permission_status": "approved",
            "verification_status": "verified",
            "license": "approved license",
            "verification_evidence": "Reviewed source record",
            "source_url": "https://example.test/source",
        }
        qf_client = FakeQfClient()
        qf_client.add_cached_passage()
        with (
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.routers.workspace.settings.quran_tafsir_resource_map", {"ibn_kathir": 168}),
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
            patch("services.api.routers.workspace.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.settings.quran_api_base_url", "https://apis-prelive.quran.foundation"),
            patch("services.api.routers.workspace.get_engine", return_value=object()),
            patch(
                "services.api.routers.workspace._get_api_source_permission",
                return_value=source_permission,
            ),
            patch("services.api.routers.workspace.get_qf_tafsir_client", return_value=qf_client),
            patch(
                "services.api.routers.workspace.generate_artifact",
                new_callable=AsyncMock,
                return_value=artifact,
            ) as generate,
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "audio",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "tafsir_book_id": "qf_tafsir_168",
                    "selected_sources": ["quran", "tafsir"],
                },
            )

        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(qf_client.cache_calls, [(168, 1, 1)])
        self.assertEqual(qf_client.fetch_calls, [])
        self.assertEqual(
            generate.await_args.args[1]["tafsir"],
            "Cached Quran Foundation Tafsir source",
        )
        self.assertEqual(
            response.json()["data"]["sources"][1]["url"],
            "https://apis-prelive.quran.foundation/content/api/v4/tafsirs/168/by_ayah/1:1",
        )
        self.assertEqual(
            response.json()["data"]["sources"],
            [
                {"id": "quran", "label": "Quran 1:1", "url": "https://quran.com/1/1"},
                {
                    "id": "tafsir-168",
                    "label": "Tafsir resource 168",
                    "url": "https://apis-prelive.quran.foundation/content/api/v4/tafsirs/168/by_ayah/1:1",
                },
            ],
        )
        self.assertEqual(set(response.json()["data"]["artifact"]), {"title", "summary", "content"})
        self.assertEqual(
            response.json()["data"]["sources"][1],
            {
                "id": "tafsir-168",
                "label": "Tafsir resource 168",
                "url": "https://apis-prelive.quran.foundation/content/api/v4/tafsirs/168/by_ayah/1:1",
            },
        )

    def test_studio_rejects_non_development_or_non_loopback_provider(self):
        scenarios = [
            ("production", "http://127.0.0.1:9000/v1", 403),
            ("development", "https://provider.example.test/v1", 503),
            ("development", "not a URL", 503),
        ]
        for environment, base_url, expected_status in scenarios:
            with self.subTest(environment=environment, base_url=base_url):
                with (
                    patch("services.api.routers.workspace.settings.environment", environment),
                    patch(
                        "services.api.routers.workspace.settings.secret_key",
                        "test-secret-key-for-browser-identity-32",
                    ),
                    patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
                    patch("services.api.routers.workspace.settings.llm_api_base_url", base_url),
                    patch("services.api.routers.workspace.settings.llm_model", "test-model"),
                    patch(
                        "services.api.routers.workspace.generate_artifact",
                        new_callable=AsyncMock,
                    ) as generate,
                    TestClient(app) as client,
                ):
                    response = client.post(
                        "/api/v1/workspace/artifacts",
                        json={
                            "kind": "audio",
                            "surah_number": 1,
                            "ayah_number": 1,
                            "surah_name": "Al-Fatihah",
                            "arabic_text": "Ayah",
                            "selected_sources": ["quran"],
                        },
                    )

                self.assertEqual(response.status_code, expected_status, response.json())
                generate.assert_not_awaited()

    def test_studio_reports_each_missing_provider_setting(self):
        settings_to_clear = (
            ("llm_api_key", "LLM_API_KEY"),
            ("llm_api_base_url", "LLM_API_BASE_URL"),
            ("llm_model", "LLM_MODEL"),
        )
        for setting_name, expected_name in settings_to_clear:
            values = {
                "llm_api_key": "test-key",
                "llm_api_base_url": "http://127.0.0.1:9000/v1",
                "llm_model": "test-model",
            }
            values[setting_name] = None
            with self.subTest(setting=setting_name):
                with (
                    patch("services.api.routers.workspace.settings.environment", "development"),
                    patch("services.api.routers.workspace.settings.llm_api_key", values["llm_api_key"]),
                    patch(
                        "services.api.routers.workspace.settings.llm_api_base_url",
                        values["llm_api_base_url"],
                    ),
                    patch("services.api.routers.workspace.settings.llm_model", values["llm_model"]),
                    TestClient(app) as client,
                ):
                    response = client.post(
                        "/api/v1/workspace/artifacts",
                        json={
                            "kind": "audio",
                            "surah_number": 1,
                            "ayah_number": 1,
                            "surah_name": "Al-Fatihah",
                            "arabic_text": "Ayah",
                            "selected_sources": ["quran"],
                        },
                    )

                self.assertEqual(response.status_code, 503)
                self.assertIn(expected_name, response.json()["error"])

    def test_studio_rejects_invalid_ayah_before_generation(self):
        with (
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
            patch("services.api.routers.workspace.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.generate_artifact", new_callable=AsyncMock) as generate,
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "audio",
                    "surah_number": 1,
                    "ayah_number": 8,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "selected_sources": ["quran"],
                },
            )

        self.assertEqual(response.status_code, 422)
        generate.assert_not_awaited()

    def test_studio_requires_quran_source(self):
        with (
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
            patch("services.api.routers.workspace.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.generate_artifact", new_callable=AsyncMock) as generate,
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "audio",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "selected_sources": [],
                },
            )

        self.assertEqual(response.status_code, 422)
        generate.assert_not_awaited()

    def test_studio_cache_miss_is_actionable_and_never_fetches(self):
        permission = {
            "permission_status": "approved",
            "verification_status": "verified",
            "license": "approved license",
            "verification_evidence": "Reviewed source record",
            "source_url": "https://example.test/source",
        }
        qf_client = FakeQfClient()
        with (
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.routers.workspace.settings.quran_tafsir_resource_map", {"ibn_kathir": 168}),
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
            patch("services.api.routers.workspace.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.get_engine", return_value=object()),
            patch("services.api.routers.workspace._get_api_source_permission", return_value=permission),
            patch("services.api.routers.workspace.get_qf_tafsir_client", return_value=qf_client),
            patch("services.api.routers.workspace.generate_artifact", new_callable=AsyncMock) as generate,
            TestClient(app, raise_server_exceptions=False) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "audio",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "tafsir_book_id": "qf_tafsir_168",
                    "selected_sources": ["quran", "tafsir"],
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("load the tafsir passage first", response.json()["error"].lower())
        self.assertEqual(qf_client.fetch_calls, [])
        generate.assert_not_awaited()

    def test_studio_rejects_cached_verse_mismatch(self):
        permission = {
            "permission_status": "approved",
            "verification_status": "verified",
            "license": "approved license",
            "verification_evidence": "Reviewed source record",
            "source_url": "https://example.test/source",
        }
        qf_client = FakeQfClient()
        qf_client.add_cached_passage(verse_key="2:1")
        with (
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.routers.workspace.settings.quran_tafsir_resource_map", {"ibn_kathir": 168}),
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
            patch("services.api.routers.workspace.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.get_engine", return_value=object()),
            patch("services.api.routers.workspace._get_api_source_permission", return_value=permission),
            patch("services.api.routers.workspace.get_qf_tafsir_client", return_value=qf_client),
            patch("services.api.routers.workspace.generate_artifact", new_callable=AsyncMock) as generate,
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "audio",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "tafsir_book_id": "qf_tafsir_168",
                    "selected_sources": ["quran", "tafsir"],
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(qf_client.fetch_calls, [])
        generate.assert_not_awaited()

    def test_studio_rejects_tafsir_citation_with_untrusted_content_api_url(self):
        permission = {
            "permission_status": "approved",
            "verification_status": "verified",
            "license": "approved license",
            "verification_evidence": "Reviewed source record",
            "source_url": "https://example.test/source",
        }
        qf_client = FakeQfClient()
        qf_client.content_api_url = "http://apis-prelive.quran.foundation/content/api/v4"
        qf_client.add_cached_passage()
        with (
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.routers.workspace.settings.quran_tafsir_resource_map", {"ibn_kathir": 168}),
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
            patch("services.api.routers.workspace.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.settings.quran_api_base_url", "https://apis-prelive.quran.foundation"),
            patch("services.api.routers.workspace.get_engine", return_value=object()),
            patch("services.api.routers.workspace._get_api_source_permission", return_value=permission),
            patch("services.api.routers.workspace.get_qf_tafsir_client", return_value=qf_client),
            patch("services.api.routers.workspace.generate_artifact", new_callable=AsyncMock) as generate,
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "audio",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "tafsir_book_id": "qf_tafsir_168",
                    "selected_sources": ["quran", "tafsir"],
                },
            )

        self.assertEqual(response.status_code, 503)
        generate.assert_not_awaited()

    def test_studio_rejects_tafsir_citation_with_mismatched_content_api_host(self):
        permission = {
            "permission_status": "approved",
            "verification_status": "verified",
            "license": "approved license",
            "verification_evidence": "Reviewed source record",
            "source_url": "https://example.test/source",
        }
        qf_client = FakeQfClient()
        qf_client.content_api_url = "https://attacker.example.test/content/api/v4"
        qf_client.add_cached_passage()
        with (
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.routers.workspace.settings.quran_tafsir_resource_map", {"ibn_kathir": 168}),
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
            patch("services.api.routers.workspace.settings.llm_model", "test-model"),
            patch("services.api.routers.workspace.settings.quran_api_base_url", "https://apis-prelive.quran.foundation"),
            patch("services.api.routers.workspace.get_engine", return_value=object()),
            patch("services.api.routers.workspace._get_api_source_permission", return_value=permission),
            patch("services.api.routers.workspace.get_qf_tafsir_client", return_value=qf_client),
            patch("services.api.routers.workspace.generate_artifact", new_callable=AsyncMock) as generate,
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/workspace/artifacts",
                json={
                    "kind": "audio",
                    "surah_number": 1,
                    "ayah_number": 1,
                    "surah_name": "Al-Fatihah",
                    "arabic_text": "Ayah",
                    "tafsir_book_id": "qf_tafsir_168",
                    "selected_sources": ["quran", "tafsir"],
                },
            )

        self.assertEqual(response.status_code, 503)
        generate.assert_not_awaited()

    def test_studio_returns_target_artifact_envelope_and_server_citations(self):
        for kind in ("audio", "quiz", "infographic"):
            artifact = {"title": "Artifact", "summary": "", "content": {"value": kind}}
            with self.subTest(kind=kind):
                with (
                    patch("services.api.routers.workspace.settings.environment", "development"),
                    patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
                    patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
                    patch("services.api.routers.workspace.settings.llm_model", "test-model"),
                    patch(
                        "services.api.routers.workspace.generate_artifact",
                        new_callable=AsyncMock,
                        return_value=artifact,
                    ),
                    TestClient(app) as client,
                ):
                    response = client.post(
                        "/api/v1/workspace/artifacts",
                        json={
                            "kind": kind,
                            "surah_number": 1,
                            "ayah_number": 1,
                            "surah_name": "untrusted label",
                            "arabic_text": "Ayah",
                            "selected_sources": ["quran"],
                        },
                    )

                self.assertEqual(response.status_code, 200, response.json())
                data = response.json()["data"]
                self.assertEqual(set(data), {"kind", "artifact", "sources", "evidence_status"})
                self.assertEqual(data["kind"], kind)
                self.assertEqual(set(data["artifact"]), {"title", "summary", "content"})
                self.assertEqual(
                    data["sources"],
                    [{"id": "quran", "label": "Quran 1:1", "url": "https://quran.com/1/1"}],
                )
                self.assertEqual(data["evidence_status"], "AI-SYNTHESIS")

    def test_studio_maps_provider_status_without_exposing_provider_details(self):
        for provider_status, expected_status in ((401, 502), (429, 503), (503, 503)):
            with self.subTest(provider_status=provider_status):
                with (
                    patch("services.api.routers.workspace.settings.environment", "development"),
                    patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
                    patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
                    patch("services.api.routers.workspace.settings.llm_model", "test-model"),
                    patch(
                        "services.api.routers.workspace.generate_artifact",
                        new_callable=AsyncMock,
                        side_effect=StudioGenerationError(
                            "Studio provider request failed",
                            status_code=provider_status,
                        ),
                    ),
                    TestClient(app) as client,
                ):
                    response = client.post(
                        "/api/v1/workspace/artifacts",
                        json={
                            "kind": "audio",
                            "surah_number": 1,
                            "ayah_number": 1,
                            "surah_name": "Al-Fatihah",
                            "arabic_text": "private source passage",
                            "selected_sources": ["quran"],
                        },
                    )

                self.assertEqual(response.status_code, expected_status)
                self.assertNotIn("test-key", response.text)
                self.assertNotIn("private source passage", response.text)

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
            patch("services.api.routers.workspace.settings.environment", "development"),
            patch("services.api.routers.workspace.settings.llm_api_key", "test-key"),
            patch("services.api.routers.workspace.settings.llm_api_base_url", "http://127.0.0.1:9000/v1"),
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
        self.assertEqual(
            response.json()["data"]["sources"][0],
            {"id": "quran", "label": "Quran 1:1", "url": "https://quran.com/1/1"},
        )
        self.assertEqual(response.json()["data"]["evidence_status"], "AI-SYNTHESIS")


if __name__ == "__main__":
    unittest.main()
