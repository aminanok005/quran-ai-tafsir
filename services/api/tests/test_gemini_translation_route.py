import os
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from fastapi.testclient import TestClient

from services.api.app import app
from services.api.routers import tafsir as tafsir_router
from services.api.services.gemini_provider import GeminiError, GeminiErrorKind

URL = "/api/v1/tafsir/gemini-translation?surah=1&ayah=1&agent_type=ibn_kathir"
PASSAGE = {"verse_key": "1:1", "passage_id": "qf:168:1:1", "arabic_text": "ARABIC", "scholar_id": "ibn_kathir",
           "scholar_name": "Ibn Kathir", "volume": None, "page": None}
RECORD = {"arabic_text": "ARABIC", "references": [{"source_id": "qf:168:1:1"}], "evidence_status": "SOURCE_ATTRIBUTED"}


class RouteTests(unittest.TestCase):
    def setUp(self):
        tafsir_router._translation_requests.clear()
        self.client = TestClient(app)

    def patches(self, passages, translate):
        return (
            patch("services.api.routers.agents._approved_source_passages", AsyncMock(return_value=passages)),
            patch.object(tafsir_router, "translate_ayah", translate),
        )

    def test_success_uses_server_arabic(self):
        translate = AsyncMock(return_value=RECORD)
        a, b = self.patches([PASSAGE], translate)
        with a, b:
            response = self.client.post(URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["arabic_text"], "ARABIC")
        kwargs = translate.await_args.kwargs
        self.assertEqual(kwargs["arabic_text"], "ARABIC")
        self.assertEqual(kwargs["sources"][0]["source_id"], "qf:168:1:1")

    def test_no_passages_503_without_provider_call(self):
        translate = AsyncMock()
        a, b = self.patches([], translate)
        with a, b:
            response = self.client.post(URL)
        self.assertEqual(response.status_code, 503)
        translate.assert_not_awaited()

    def test_provider_error_is_generic(self):
        translate = AsyncMock(side_effect=GeminiError(GeminiErrorKind.CONFIGURATION))
        a, b = self.patches([PASSAGE], translate)
        with a, b:
            response = self.client.post(URL)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("key", response.text.lower())

    def test_out_of_range_400(self):
        response = self.client.post("/api/v1/tafsir/gemini-translation?surah=999&ayah=1&agent_type=ibn_kathir")
        self.assertEqual(response.status_code, 400)
