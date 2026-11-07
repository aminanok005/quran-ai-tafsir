import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from services.api.app import app
from services.api.config import Settings
from services.api.routers import retrieval
from services.api.services.embedding import (
    DATABASE_VECTOR_DIMENSIONS,
    EmbeddingConfigurationError,
    EmbeddingProviderError,
    embed_texts,
)
from services.api.services.tafsir_retrieval import SEARCH_SQL
from services.api.services.tafsir_retrieval import _evidence_label


def embedding_settings(**overrides):
    variables = {
        "DATABASE_URL": "postgresql+psycopg://postgres@localhost/quran_ai_test",
        "EMBEDDING_PROVIDER": "openai_compatible",
        "EMBEDDING_API_BASE_URL": "http://127.0.0.1:20128/v1",
        "EMBEDDING_API_KEY": "embedding-test-secret",
        "EMBEDDING_MODEL": "test-embedding-model",
        "VECTOR_DIMENSIONS": str(DATABASE_VECTOR_DIMENSIONS),
    }
    variables.update(overrides)
    return Settings(_env_file=None, **variables)


class EmbeddingClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_embeddings_are_validated_and_credentials_remain_in_header(self):
        observed = {}

        def handler(request):
            observed["authorization"] = request.headers.get("authorization")
            observed["url"] = str(request.url)
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"index": 0, "embedding": [0.25] * DATABASE_VECTOR_DIMENSIONS},
                        {"index": 1, "embedding": [0.5] * DATABASE_VECTOR_DIMENSIONS},
                    ]
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            vectors = await embed_texts(
                ["first query", "second query"],
                client=client,
                config=embedding_settings(),
            )

        self.assertEqual(len(vectors), 2)
        self.assertEqual(len(vectors[0]), DATABASE_VECTOR_DIMENSIONS)
        self.assertEqual(observed["authorization"], "Bearer embedding-test-secret")
        self.assertNotIn("embedding-test-secret", observed["url"])

    async def test_http_provider_error_does_not_expose_provider_body(self):
        def handler(_request):
            return httpx.Response(503, json={"error": "secret provider diagnostic"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(EmbeddingProviderError) as raised:
                await embed_texts(["query"], client=client, config=embedding_settings())

        self.assertIn("HTTP 503", str(raised.exception))
        self.assertNotIn("secret provider diagnostic", str(raised.exception))

    async def test_bad_vector_dimensions_are_rejected(self):
        def handler(_request):
            return httpx.Response(200, json={"data": [{"index": 0, "embedding": [1.0, 2.0]}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(EmbeddingProviderError):
                await embed_texts(["query"], client=client, config=embedding_settings())

    async def test_timeout_is_reported_as_provider_error(self):
        def handler(_request):
            raise httpx.ReadTimeout("sensitive query text")

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaisesRegex(EmbeddingProviderError, "timed out"):
                await embed_texts(["query"], client=client, config=embedding_settings())

    async def test_incompatible_dimensions_and_remote_http_are_rejected(self):
        with self.assertRaises(EmbeddingConfigurationError):
            await embed_texts(
                ["query"],
                client=AsyncMock(),
                config=embedding_settings(VECTOR_DIMENSIONS="768"),
            )
        with self.assertRaises(EmbeddingConfigurationError):
            await embed_texts(
                ["query"],
                client=AsyncMock(),
                config=embedding_settings(EMBEDDING_API_BASE_URL="http://10.0.0.2/v1"),
            )
        with self.assertRaises(EmbeddingConfigurationError):
            await embed_texts(
                ["query"],
                client=AsyncMock(),
                config=embedding_settings(
                    EMBEDDING_API_BASE_URL="https://embeddings.example.test/v1?token=unsafe"
                ),
            )


class TafsirSearchEndpointTests(unittest.TestCase):
    def test_search_returns_passage_trace_and_does_not_promote_evidence(self):
        result = {
            "passage_id": "passage-1",
            "arabic_text": "نص",
            "thai_translation": None,
            "evidence_status": "UNVERIFIED",
            "source": {"url": "https://example.test/tafsir"},
        }
        with (
            patch.object(retrieval, "embed_texts", new=AsyncMock(return_value=[[0.1] * 1536])) as embed,
            patch.object(retrieval, "get_engine", return_value=object()),
            patch.object(retrieval, "search_tafsir", return_value=[result]) as search,
            patch("services.api.routers.tafsir.settings.environment", "development"),
        ):
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/tafsir/search",
                    json={"query": "คำถามอ้างอิง", "surah_number": 4, "ayah_number": 1},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["results"][0]["evidence_status"], "UNVERIFIED")
        self.assertEqual(response.json()["data"]["results"][0]["source"]["url"], result["source"]["url"])
        embed.assert_awaited_once()
        self.assertEqual(search.call_args.kwargs["surah_number"], 4)
        self.assertFalse(search.call_args.kwargs["include_development"])

    def test_search_requires_surah_and_ayah_together(self):
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/tafsir/search",
                json={"query": "query", "surah_number": 4},
            )
        self.assertEqual(response.status_code, 422)

    def test_development_search_is_disabled_outside_development(self):
        with (
            patch("services.api.routers.retrieval.settings.environment", "production"),
            patch.object(retrieval, "embed_texts", new=AsyncMock()) as embed,
        ):
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/tafsir/search",
                    json={"query": "query", "include_development": True},
                )
        self.assertEqual(response.status_code, 403)
        embed.assert_not_awaited()

    def test_query_has_isolated_development_and_approved_source_filters(self):
        sql = " ".join(str(SEARCH_SQL).lower().split())
        self.assertIn("sp.permission_status::text = 'development_only'", sql)
        self.assertIn("sp.verification_status::text = 'verified'", sql)
        self.assertIn("p.verification_status::text in ('verified', 'source_attributed', 'scholarly_difference')", sql)
        self.assertIn("p.embedding <=> cast(:embedding as vector)", sql)

    def test_evidence_labels_keep_the_existing_public_vocabulary(self):
        self.assertEqual(_evidence_label("source_attributed"), "SOURCE-ATTRIBUTED")
        self.assertEqual(_evidence_label("scholarly_difference"), "SCHOLARLY DIFFERENCE")
        self.assertEqual(_evidence_label("unverified"), "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
