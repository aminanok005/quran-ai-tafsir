import json
import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from services.api.app import app
from services.api.routers.tafsir import (
    _public_api_passage,
    _translation_is_allowed,
    _translation_provider_http_exception,
)
from services.api.services.quran_foundation_tafsir import QuranFoundationTafsir
from services.api.services.tafsir_json import split_tafsir_text
from services.api.services.tafsir_translation import translate_tafsir_to_thai


def permission_record():
    return {
        "source_id": "qf_tafsir_168",
        "source_url": "https://example.test/source",
        "license": "approved license",
        "permission_status": "approved",
        "verification_status": "verified",
        "verification_evidence": "Reviewed source record",
    }


def api_passage():
    return QuranFoundationTafsir(
        resource_id=168,
        resource_name="Tafsir Ibn Kathir",
        language_name="english",
        slug="en-tafisr-ibn-kathir",
        verse_key="1:1",
        text="Tafsir text from Quran Foundation",
    )


class FakeQfClient:
    content_api_url = "https://apis-prelive.quran.foundation/content/api/v4"

    def __init__(self, passage=None):
        self.passage = passage or api_passage()
        self.calls = []

    async def fetch_ayah(self, *args):
        self.calls.append(args)
        return self.passage


class RuntimeSettingsTests(unittest.TestCase):
    def test_tafsir_runtime_defaults_to_live_api_cache_and_resource(self):
        variables = {
            "DATABASE_URL": "postgresql+psycopg://postgres@localhost/quran_ai_test",
        }
        with patch.dict(os.environ, variables, clear=True):
            from services.api.config import Settings

            settings = Settings(_env_file=None)
        self.assertEqual(settings.quran_api_tafsir_cache_ttl, 300)
        self.assertEqual(settings.quran_tafsir_resource_map, {"ibn_kathir": 168})

    def test_llm_and_retrieval_settings_load_from_environment(self):
        variables = {
            "DATABASE_URL": "postgresql+psycopg://postgres@localhost/quran_ai_test",
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


class TafsirRightsTests(unittest.TestCase):
    def test_translation_requires_approved_and_verified_source(self):
        permission = permission_record()
        self.assertTrue(_translation_is_allowed(permission))
        permission["permission_status"] = "pending"
        self.assertFalse(_translation_is_allowed(permission))

    def test_unapproved_source_does_not_expose_cached_translation(self):
        permission = permission_record()
        permission["permission_status"] = "pending"
        public = _public_api_passage(
            api_passage(),
            "https://example.test/source",
            permission,
            "cached translation",
        )
        self.assertIsNone(public["thai_translation"])
        self.assertFalse(public["translation_allowed"])
        self.assertEqual(public["evidence_status"], "SOURCE-ATTRIBUTED")
        self.assertEqual(public["arabic_text"], "Tafsir text from Quran Foundation")

    def test_translation_provider_errors_do_not_expose_provider_response(self):
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
                    response=httpx.Response(
                        status_code, json={"error": {"message": "sensitive provider text"}}
                    ),
                )
                exception = _translation_provider_http_exception(error)
                self.assertIn(expected_detail, exception.detail)
                self.assertNotIn("sensitive provider text", exception.detail)

    def test_reader_fetches_live_qf_source_and_never_uses_local_passages(self):
        qf_client = FakeQfClient()
        with (
            patch("services.api.routers.tafsir.settings.environment", "production"),
            patch(
                "services.api.routers.tafsir.settings.quran_tafsir_resource_map",
                {"ibn_kathir": 168},
            ),
            patch("services.api.routers.tafsir.get_qf_tafsir_client", return_value=qf_client),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch("services.api.routers.tafsir._get_api_source_permission", return_value=None),
            patch("services.api.routers.tafsir._cached_api_translation") as cached_translation,
            patch("services.api.routers.tafsir._get_passage", create=True) as legacy_lookup,
            TestClient(app) as client,
        ):
            response = client.get(
                "/api/v1/tafsir/passages/1/1",
                params={"agent_type": "ibn_kathir"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"]["arabic_text"], "Tafsir text from Quran Foundation"
        )
        self.assertEqual(response.json()["data"]["source"]["title"], "Tafsir Ibn Kathir")
        self.assertEqual(qf_client.calls, [(168, 1, 1)])
        self.assertFalse(response.json()["data"]["translation_allowed"])
        cached_translation.assert_not_called()
        legacy_lookup.assert_not_called()

    def test_reader_uses_translation_cache_only_when_permission_is_approved(self):
        with (
            patch(
                "services.api.routers.tafsir.settings.quran_tafsir_resource_map",
                {"ibn_kathir": 168},
            ),
            patch("services.api.routers.tafsir.get_qf_tafsir_client", return_value=FakeQfClient()),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch(
                "services.api.routers.tafsir._get_api_source_permission",
                return_value=permission_record(),
            ),
            patch(
                "services.api.routers.tafsir._cached_api_translation", return_value="คำแปลที่บันทึกแล้ว"
            ) as cached,
            TestClient(app) as client,
        ):
            response = client.get(
                "/api/v1/tafsir/passages/1/1",
                params={"agent_type": "ibn_kathir"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["thai_translation"], "คำแปลที่บันทึกแล้ว")
        self.assertTrue(response.json()["data"]["translation_allowed"])
        cached.assert_called_once()

    def test_api_translation_blocks_unapproved_source(self):
        translator = AsyncMock()
        with (
            patch(
                "services.api.routers.tafsir.settings.quran_tafsir_resource_map",
                {"ibn_kathir": 168},
            ),
            patch("services.api.routers.tafsir.get_qf_tafsir_client", return_value=FakeQfClient()),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch("services.api.routers.tafsir._get_api_source_permission", return_value=None),
            patch("services.api.routers.tafsir.translate_tafsir_to_thai", translator),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/passages/api/1/1/translate",
                params={"agent_type": "ibn_kathir"},
                json={},
            )
        self.assertEqual(response.status_code, 403)
        translator.assert_not_awaited()

    def test_translation_persists_only_generated_text_after_permission_check(self):
        qf_client = FakeQfClient()
        translator = AsyncMock(return_value="คำแปลจาก AI")
        with (
            patch(
                "services.api.routers.tafsir.settings.quran_tafsir_resource_map",
                {"ibn_kathir": 168},
            ),
            patch("services.api.routers.tafsir.settings.llm_provider", "openai"),
            patch("services.api.routers.tafsir.settings.llm_api_key", "test-key"),
            patch("services.api.routers.tafsir.settings.llm_model", "test-model"),
            patch(
                "services.api.routers.tafsir.settings.llm_api_base_url",
                "https://llm.example.test/v1",
            ),
            patch("services.api.routers.tafsir.get_qf_tafsir_client", return_value=qf_client),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch(
                "services.api.routers.tafsir._get_api_source_permission",
                return_value=permission_record(),
            ),
            patch("services.api.routers.tafsir._cached_api_translation", return_value=None),
            patch("services.api.routers.tafsir.translate_tafsir_to_thai", translator),
            patch(
                "services.api.routers.tafsir._save_api_translation", return_value="คำแปลจาก AI"
            ) as save,
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/passages/api/1/1/translate",
                params={"agent_type": "ibn_kathir"},
                json={},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["thai_translation"], "คำแปลจาก AI")
        translator.assert_awaited_once_with(
            "Tafsir text from Quran Foundation",
            api_key="test-key",
            model="test-model",
            base_url="https://llm.example.test/v1",
            wire_api="chat_completions",
        )
        save.assert_called_once()
        self.assertEqual(save.call_args.args[1], api_passage())
        self.assertEqual(save.call_args.args[4], "คำแปลจาก AI")

    def test_legacy_passage_id_translation_is_gone(self):
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/tafsir/passages/00000000-0000-0000-0000-000000000001/translate",
                json={},
            )
        self.assertEqual(response.status_code, 410)

    def test_translation_explains_exhausted_provider_quota(self):
        error = httpx.HTTPStatusError(
            "rate limited",
            request=httpx.Request("POST", "https://llm.example.test/v1/chat/completions"),
            response=httpx.Response(
                429,
                json={
                    "error": {
                        "type": "insufficient_quota",
                        "code": "credit_balance_exhausted",
                    }
                },
            ),
        )
        with (
            patch(
                "services.api.routers.tafsir.settings.quran_tafsir_resource_map",
                {"ibn_kathir": 168},
            ),
            patch("services.api.routers.tafsir.settings.llm_provider", "openai"),
            patch("services.api.routers.tafsir.settings.llm_api_key", "test-key"),
            patch("services.api.routers.tafsir.settings.llm_model", "test-model"),
            patch(
                "services.api.routers.tafsir.settings.llm_api_base_url",
                "https://llm.example.test/v1",
            ),
            patch("services.api.routers.tafsir.get_qf_tafsir_client", return_value=FakeQfClient()),
            patch("services.api.routers.tafsir.get_engine", return_value=object()),
            patch(
                "services.api.routers.tafsir._get_api_source_permission",
                return_value=permission_record(),
            ),
            patch("services.api.routers.tafsir._cached_api_translation", return_value=None),
            patch(
                "services.api.routers.tafsir.translate_tafsir_to_thai",
                new_callable=AsyncMock,
                side_effect=error,
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/passages/api/1/2/translate",
                params={"agent_type": "ibn_kathir"},
                json={},
            )
        self.assertEqual(response.status_code, 429)
        self.assertIn("เครดิตหรือโควตาการใช้งานหมด", response.json()["error"])

    def test_long_json_passages_split_without_losing_source_characters(self):
        source = "alpha beta gamma delta"
        chunks = split_tafsir_text(source, chunk_size=10)
        self.assertEqual(" ".join(chunks), source)
        self.assertTrue(all(len(chunk) <= 10 for chunk in chunks))


class OpenAITranslationTests(unittest.IsolatedAsyncioTestCase):
    async def test_translates_and_returns_openai_thai_text(self):
        async def openai_response(request):
            self.assertEqual(request.headers["authorization"], "Bearer test-key")
            payload = json.loads(request.content)
            self.assertEqual(str(request.url), "https://llm.example.test/v1/chat/completions")
            self.assertEqual(payload["model"], "test-model")
            self.assertIn("complete passage", payload["messages"][0]["content"])
            self.assertIn("Arabic source", payload["messages"][1]["content"])
            return httpx.Response(200, json={"choices": [{"message": {"content": "คำแปลภาษาไทย"}}]})

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
            return httpx.Response(200, json={"choices": [{"message": {"content": "  "}}]})

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
