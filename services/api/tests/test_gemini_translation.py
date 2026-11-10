import json
import unittest

from services.api.services.gemini_provider import GeminiResult, Usage
from services.api.services.gemini_translation import translate_ayah


class FakeRouter:
    def __init__(self, draft, review):
        self.replies = [draft, review]

    async def run(self, task, messages, **kw):
        return GeminiResult("x", Usage("m"), self.replies.pop(0))


SOURCES = [{"source_id": "qf:1:1:1", "scholar_name": "A", "text": "t", "volume": 1, "page": 2}]
DRAFT = {"literal_th": "ก", "contextual_th": "ข", "ambiguities": [], "source_ids_used": ["qf:1:1:1", "fake:9"]}


class TranslationTests(unittest.IsolatedAsyncioTestCase):
    async def test_arabic_preserved_and_fake_citation_dropped(self):
        out = await translate_ayah(FakeRouter(DRAFT, {"terminology_preserved": True, "meaning_preserved": True}),
                                   verse_key="1:1", arabic_text="ARABIC", sources=SOURCES)
        self.assertEqual(out["arabic_text"], "ARABIC")
        self.assertEqual([r["source_id"] for r in out["references"]], ["qf:1:1:1"])
        self.assertEqual(out["evidence_status"], "SOURCE_ATTRIBUTED")
        self.assertTrue(out["ai_generated"])

    async def test_no_valid_source_is_unverified_and_bad_review_tolerated(self):
        draft = {**DRAFT, "source_ids_used": ["fake:9"]}
        out = await translate_ayah(FakeRouter(draft, {"bad": 1}), verse_key="1:1", arabic_text="A", sources=SOURCES)
        self.assertEqual(out["evidence_status"], "UNVERIFIED")
        self.assertIsNone(out["quality_review"])

    async def test_invalid_draft_raises(self):
        with self.assertRaises(Exception):
            await translate_ayah(FakeRouter({"x": 1}, {}), verse_key="1:1", arabic_text="A", sources=SOURCES)
