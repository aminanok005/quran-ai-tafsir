import os
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/quran_ai_test")

from services.api.app import app
from services.api.routers.tafsir import (
    _public_passage,
    _translation_provider_http_exception,
    _translation_is_allowed,
)
from services.api.services.tafsir_translation import translate_tafsir_to_thai
from services.api.services.quran_foundation_tafsir import QuranFoundationTafsir
from services.api.services.tafsir_json import split_tafsir_text


class RuntimeSettingsTests(unittest.TestCase):
    def test_llm_and_retrieval_settings_load_from_environment(self):
        variables = {
            "DATABASE_URL": "postgresql://test:test@localhost/quran_ai_test",
            "LLM_PROVIDER": "openai",
            "LLM_API_BASE_URL": "https://llm.example.test/v1",
            "OPENAI_API_KEY": "new-openai-test-key",
            "LLM_API_KEY": "unit-test-key",
            "LLM_MODEL": "unit-test-model",
            "EMBEDDING_PROVIDER": "openai",
            "EMBEDDING_MODEL": "unit-test-embedding",
            "VECTOR_DIMENSIONS": "1234",
        }
        with patch.dict(os.environ, variables, clear=True):
            from services.api.config import Settings

            settings = Settings(_env_file=None)

        self.assertEqual(settings.llm_provider, "openai")
        self.assertEqual(settings.llm_api_base_url, "https://llm.example.test/v1")
        self.assertEqual(settings.llm_api_key, "unit-test-key")
        self.assertEqual(settings.openai_api_key, "new-openai-test-key")
        self.assertEqual(settings.translation_api_key, "unit-test-key")
        self.assertEqual(settings.llm_model, "unit-test-model")
        self.assertEqual(settings.embedding_provider, "openai")
        self.assertEqual(settings.embedding_model, "unit-test-embedding")
        self.assertEqual(settings.embedding_dimensions, 1234)

    def test_custom_provider_requires_its_own_llm_api_key(self):
        variables = {
            "DATABASE_URL": "postgresql+psycopg://postgres@localhost/quran_ai_test",
            "LLM_API_BASE_URL": "http://127.0.0.1:20128/v1",
            "OPENAI_API_KEY": "openai-key",
        }
        with patch.dict(os.environ, variables, clear=True):
            from services.api.config import Settings

            settings = Settings(_env_file=None)

        self.assertIsNone(settings.translation_api_key)

    def test_openai_key_is_used_for_official_openai_endpoint(self):
        variables = {
            "DATABASE_URL": "postgresql+psycopg://postgres@localhost/quran_ai_test",
            "LLM_API_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_API_KEY": "openai-key",
        }
        with patch.dict(os.environ, variables, clear=True):
            from services.api.config import Settings

            settings = Settings(_env_file=None)

        self.assertEqual(settings.translation_api_key, "openai-key")


def passage_record():
    return {
        "passage_id": "passage-1",
        "surah_number": 1,
        "ayah_start": 1,
        "ayah_end": 1,
        "arabic_text": "نص التفسير",
        "thai_translation": None,
        "volume": 1,
        "page": 2,
        "edition": "Test edition",
        "passage_source_url": "https://example.test/source",
        "evidence_status": "unverified",
        "book_id": "tafsir_ibn_kathir",
        "book_title": "Tafsir Ibn Kathir",
        "book_title_ar": "تفسير ابن كثير",
        "license": "approved license",
        "book_source_url": "https://example.test/source",
        "permission_status": "approved",
        "book_verification_status": "verified",
        "verification_evidence": "Reviewed source record",
        "scholar_name": "Ibn Kathir",
        "registered_permission_status": "approved",
        "registered_verification_status": "verified",
        "source_url": "https://example.test/source",
    }


class TafsirRightsTests(unittest.TestCase):
    def test_translation_requires_approved_and_verified_source(self):
        source = passage_record()
        self.assertTrue(_translation_is_allowed(source))

        source["registered_permission_status"] = "pending"
        self.assertFalse(_translation_is_allowed(source))

    def test_unapproved_source_does_not_expose_cached_translation(self):
        source = passage_record()
        source["registered_permission_status"] = "pending"
        source["thai_translation"] = "คำแปลเดิม"

        public = _public_passage(source)
        self.assertIsNone(public["thai_translation"])
        self.assertFalse(public["translation_allowed"])
        self.assertEqual(public["arabic_text"], "نص التفسير")

    def test_translation_provider_errors_explain_configuration_failures(self):
        cases = (
            (401, "OPENAI_API_KEY"),
            (403, "OPENAI_API_KEY"),
            (404, "LLM_API_BASE_URL"),
            (400, "Chat Completions"),
            (503, "ขัดข้องชั่วคราว"),
        )
        for status_code, expected_detail in cases:
            with self.subTest(status_code=status_code):
                error = httpx.HTTPStatusError(
                    "provider error",
                    request=httpx.Request("POST", "https://llm.example.test/v1/chat/completions"),
                    response=httpx.Response(status_code, json={"error": {"message": "sensitive provider text"}}),
                )
                exception = _translation_provider_http_exception(error)
                self.assertIn(expected_detail, exception.detail)
                self.assertNotIn("sensitive provider text", exception.detail)

    def test_passage_endpoint_reads_database_row(self):
        source = passage_record()

        class FakeResult:
            def mappings(self):
                return self

            def first(self):
                return source

        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def execute(self, *_args):
                return FakeResult()

        class FakeEngine:
            def connect(self):
                return FakeConnection()

        with (
            patch("services.api.routers.tafsir.settings.environment", "production"),
            patch("services.api.routers.tafsir.get_engine", return_value=FakeEngine()),
        ):
            with TestClient(app) as client:
                response = client.get(
                    "/api/v1/tafsir/passages/1/1",
                    params={"agent_type": "ibn_kathir"},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["arabic_text"], "نص التفسير")
        self.assertEqual(response.json()["data"]["source"]["title"], "Tafsir Ibn Kathir")

    def test_development_passage_fetches_and_caches_qf_result(self):
        source = passage_record()
        source.update(
            {
                "book_id": "qf_tafsir_169",
                "permission_status": "development_only",
                "book_verification_status": "unverified",
                "verification_evidence": None,
                "license": None,
                "registered_permission_status": "development_only",
                "registered_verification_status": "unverified",
                "arabic_text": "Tafsir text from Quran Foundation",
            }
        )
        api_passage = QuranFoundationTafsir(
            resource_id=169,
            resource_name="Tafsir Ibn Kathir",
            language_name="english",
            slug="en-tafisr-ibn-kathir",
            verse_key="1:1",
            text="Tafsir text from Quran Foundation",
        )

        class FakeQfClient:
            content_api_url = "https://apis-prelive.quran.foundation/content/api/v4"

            async def fetch_ayah(self, *_args):
                return api_passage

        with (
            patch("services.api.routers.tafsir.settings.environment", "development"),
            patch("services.api.routers.tafsir.settings.quran_tafsir_resource_map", {"ibn_kathir": 169}),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch(
                "services.api.routers.tafsir._get_passage",
                side_effect=[None, source],
            ),
            patch("services.api.routers.tafsir.get_qf_tafsir_client", return_value=FakeQfClient()),
            patch("services.api.routers.tafsir.upsert_development_qf_tafsir") as upsert,
            TestClient(app) as client,
        ):
            response = client.get(
                "/api/v1/tafsir/passages/1/1",
                params={"agent_type": "ibn_kathir"},
            )

        self.assertEqual(response.status_code, 200)
        passage = response.json()["data"]
        self.assertTrue(passage["development_mode"])
        self.assertFalse(passage["translation_allowed"])
        self.assertEqual(passage["arabic_text"], "Tafsir text from Quran Foundation")
        self.assertEqual(passage["evidence_status"], "UNVERIFIED")
        self.assertEqual(
            passage["source"]["provider"],
            "Quran Foundation Content API",
        )
        upsert.assert_called_once()

    def test_development_passage_uses_cached_database_row_without_fetching(self):
        source = passage_record()
        source.update(
            {
                "book_id": "qf_tafsir_169",
                "permission_status": "development_only",
                "book_verification_status": "unverified",
                "verification_evidence": None,
                "license": None,
                "registered_permission_status": "development_only",
                "registered_verification_status": "unverified",
            }
        )
        with (
            patch("services.api.routers.tafsir.settings.environment", "development"),
            patch("services.api.routers.tafsir.settings.quran_tafsir_resource_map", {"ibn_kathir": 169}),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch("services.api.routers.tafsir._get_passage", return_value=source),
            patch("services.api.routers.tafsir.get_qf_tafsir_client") as get_client,
            TestClient(app) as client,
        ):
            response = client.get(
                "/api/v1/tafsir/passages/1/1",
                params={"agent_type": "ibn_kathir"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["development_mode"])
        get_client.assert_not_called()

    def test_production_does_not_fetch_or_expose_development_only_passage(self):
        with (
            patch("services.api.routers.tafsir.settings.environment", "production"),
            patch("services.api.routers.tafsir.settings.quran_tafsir_resource_map", {"ibn_kathir": 169}),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch("services.api.routers.tafsir._get_passage", return_value=None),
            patch("services.api.routers.tafsir.get_qf_tafsir_client") as get_client,
            TestClient(app) as client,
        ):
            response = client.get(
                "/api/v1/tafsir/passages/1/1",
                params={"agent_type": "ibn_kathir"},
            )

        self.assertEqual(response.status_code, 404)
        get_client.assert_not_called()

    def test_development_translation_blocks_unapproved_api_passage(self):
        source = passage_record()
        source.update(
            {
                "permission_status": "development_only",
                "book_verification_status": "unverified",
                "verification_evidence": None,
                "license": None,
                "registered_permission_status": "development_only",
                "registered_verification_status": "unverified",
            }
        )
        with (
            patch("services.api.routers.tafsir.settings.environment", "development"),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch("services.api.routers.tafsir._get_passage", return_value=source),
            patch("services.api.routers.tafsir.translate_tafsir_to_thai", new_callable=AsyncMock) as translator,
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/passages/dev/1/1/translate",
                params={"agent_type": "al_saadi"},
                json={},
            )

        self.assertEqual(response.status_code, 403)
        translator.assert_not_awaited()

    def test_development_translation_route_is_disabled_outside_development(self):
        with (
            patch("services.api.routers.tafsir.settings.environment", "production"),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/passages/dev/1/1/translate",
                params={"agent_type": "al_saadi"},
                json={},
            )

        self.assertEqual(response.status_code, 404)

    def test_development_translation_explains_exhausted_provider_quota(self):
        error = httpx.HTTPStatusError(
            "rate limited",
            request=httpx.Request("POST", "https://llm.example.test/v1/chat/completions"),
            response=httpx.Response(
                429,
                json={
                    "error": {
                        "type": "insufficient_quota",
                        "code": "credit_balance_exhausted",
                    },
                },
            ),
        )
        with (
            patch("services.api.routers.tafsir.settings.environment", "development"),
            patch("services.api.routers.tafsir.settings.llm_provider", "openai"),
            patch("services.api.routers.tafsir.settings.llm_api_key", "test-key"),
            patch("services.api.routers.tafsir.settings.llm_model", "test-model"),
            patch("services.api.routers.tafsir.settings.llm_api_base_url", "https://llm.example.test/v1"),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch("services.api.routers.tafsir._get_passage", return_value=passage_record()),
            patch("services.api.routers.tafsir.translate_tafsir_to_thai", new_callable=AsyncMock, side_effect=error),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/passages/dev/2/1/translate",
                params={"agent_type": "al_saadi"},
                json={},
            )

        self.assertEqual(response.status_code, 429)
        self.assertIn("เครดิตหรือโควตาการใช้งานหมด", response.json()["error"])
        self.assertIn("เติมเครดิต", response.json()["error"])

    def test_long_json_passages_split_without_losing_source_characters(self):
        source_text = ("نص عربي " * 1500).strip()
        chunks = split_tafsir_text(source_text)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 6000 for chunk in chunks))
        self.assertEqual(" ".join(chunks), source_text)

    def test_translation_endpoint_calls_openai_and_caches_result(self):
        source = passage_record()

        class FakeMappingsResult:
            def mappings(self):
                return self

            def first(self):
                return source

        class FakeScalarResult:
            def scalar_one_or_none(self):
                return "คำแปลจาก OpenAI"

        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def execute(self, statement, _params):
                if str(statement).lstrip().startswith("SELECT"):
                    return FakeMappingsResult()
                return FakeScalarResult()

        class FakeEngine:
            def connect(self):
                return FakeConnection()

            def begin(self):
                return FakeConnection()

        with (
            patch("services.api.routers.tafsir.get_engine", return_value=FakeEngine()),
            patch("services.api.routers.tafsir.translate_tafsir_to_thai", new_callable=AsyncMock, return_value="คำแปลจาก OpenAI") as translator,
            patch("services.api.routers.tafsir.settings.llm_provider", "openai"),
            patch("services.api.routers.tafsir.settings.llm_api_key", "test-key"),
            patch("services.api.routers.tafsir.settings.llm_model", "test-model"),
            patch("services.api.routers.tafsir.settings.llm_api_base_url", "https://llm.example.test/v1"),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/passages/00000000-0000-0000-0000-000000000001/translate",
                json={},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["thai_translation"], "คำแปลจาก OpenAI")
        self.assertFalse(response.json()["data"]["cached"])
        translator.assert_awaited_once_with(
            source["arabic_text"],
            api_key="test-key",
            model="test-model",
            base_url="https://llm.example.test/v1",
            wire_api="chat_completions",
        )


class OpenAITranslationTests(unittest.IsolatedAsyncioTestCase):
    async def test_translates_and_returns_openai_thai_text(self):
        async def openai_response(request):
            self.assertEqual(request.headers["authorization"], "Bearer test-key")
            payload = json.loads(request.content)
            self.assertEqual(str(request.url), "https://llm.example.test/v1/chat/completions")
            self.assertEqual(payload["model"], "test-model")
            self.assertIn("complete passage", payload["messages"][0]["content"])
            self.assertIn("Arabic source", payload["messages"][1]["content"])
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "คำแปลภาษาไทย"}}]},
            )

        result = await translate_tafsir_to_thai(
            "Arabic source",
            api_key="test-key",
            model="test-model",
            base_url="https://llm.example.test/v1",
            transport=httpx.MockTransport(openai_response),
        )
        self.assertEqual(result, "คำแปลภาษาไทย")

    async def test_supports_responses_api_wire_format(self):
        async def openai_response(request):
            payload = json.loads(request.content)
            self.assertEqual(str(request.url), "https://llm.example.test/v1/responses")
            self.assertEqual(payload["model"], "test-model")
            self.assertIn("input", payload)
            return httpx.Response(200, json={"output_text": "คำแปลภาษาไทยจาก Responses API"})

        result = await translate_tafsir_to_thai(
            "Arabic source",
            api_key="test-key",
            model="test-model",
            base_url="https://llm.example.test/v1",
            wire_api="responses",
            transport=httpx.MockTransport(openai_response),
        )
        self.assertEqual(result, "คำแปลภาษาไทยจาก Responses API")

    async def test_rejects_empty_provider_response(self):
        async def openai_response(_request):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "  "}}]},
            )

        with self.assertRaisesRegex(RuntimeError, "empty translation"):
            await translate_tafsir_to_thai(
                "Arabic source",
                api_key="test-key",
                model="test-model",
                base_url="https://llm.example.test/v1",
                transport=httpx.MockTransport(openai_response),
            )


if __name__ == "__main__":
    unittest.main()
