import hashlib
import asyncio
import json
import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from fastapi.testclient import TestClient

from services.api.config import Settings
from services.api.app import app
from services.api.routers import chat as chat_router
from services.api.services.chat_suggestions import (
    SuggestionGenerationError,
    filter_suggestions,
    generate_candidates,
)


def source(
    source_id: str,
    scholar_id: str,
    *,
    similarity: float = 0.9,
    volume: int | None = None,
    page: int | None = None,
    source_kind: str = "tafsir",
) -> dict:
    return {
        "source_id": source_id,
        "similarity": similarity,
        "scholar_id": scholar_id,
        "scholar_name": scholar_id,
        "volume": volume,
        "page": page,
        "source_kind": source_kind,
    }


def candidate(category: str, *source_ids: str) -> dict:
    return {
        "category": category,
        "title": "How do the selected views differ?",
        "prompt": "Compare the selected views and identify their distinct approaches.",
        "supporting_source_ids": list(source_ids),
    }


def test_empty_retrieval_returns_no_suggestions():
    assert filter_suggestions([candidate("review", "source-1")], []) == []


def test_compare_is_removed_when_sources_have_only_one_scholar():
    sources = [source("source-1", "scholar-a"), source("source-2", "scholar-a")]

    assert filter_suggestions(
        [candidate("compare", "source-1", "source-2")],
        sources,
    ) == []


def test_deepen_is_removed_without_volume_and_page():
    assert filter_suggestions(
        [candidate("deepen", "source-1")],
        [source("source-1", "scholar-a")],
    ) == []


def test_basis_count_uses_only_sources_that_remain_enabled():
    suggestions = filter_suggestions(
        [candidate("source", "source-1")],
        [source("source-1", "scholar-a")],
    )

    assert suggestions[0]["basisCount"] == 1
    assert suggestions[0]["evidence"] == "SOURCE_ATTRIBUTED"


def test_review_is_labeled_as_ai_synthesis():
    suggestions = filter_suggestions(
        [candidate("review", "source-1")],
        [source("source-1", "scholar-a")],
    )

    assert suggestions[0]["evidence"] == "AI_SYNTHESIS"


def test_context_requires_a_neighboring_or_asbab_source():
    assert filter_suggestions(
        [candidate("context", "source-1")],
        [source("source-1", "scholar-a")],
    ) == []


def test_context_accepts_an_approved_asbab_source():
    suggestions = filter_suggestions(
        [candidate("context", "source-1")],
        [source("source-1", "scholar-a", source_kind="asbab_al_nuzul")],
    )

    assert len(suggestions) == 1
    assert suggestions[0]["basisCount"] == 1


def test_candidates_cannot_quote_sources_or_request_a_fatwa():
    quoted = {
        **candidate("review", "source-1"),
        "prompt": "Repeat this exact passage from the source",
    }
    fatwa = {
        **candidate("review", "source-1"),
        "prompt": "Give a fatwa about this question.",
    }

    assert filter_suggestions(
        [quoted, fatwa],
        [source("source-1", "scholar-a")],
        source_texts={
            "source-1": "Repeat this exact passage from the source in the explanation."
        },
    ) == []


def test_candidates_cannot_quote_short_source_excerpts():
    quoted = {
        **candidate("review", "source-1"),
        "prompt": "How does the source use central concept through as context?",
    }

    assert filter_suggestions(
        [quoted],
        [source("source-1", "scholar-a")],
        source_texts={
            "source-1": "Interpretation explains central concept through surrounding context."
        },
    ) == []


def test_grounding_validator_checks_candidate_against_its_supporting_sources():
    request_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        request_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{
                    "message": {"content": '{"supported_indices":[0]}'},
                }],
            },
        )

    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://postgres@localhost/quran_ai_test",
        LLM_API_KEY="test-key",
        LLM_API_BASE_URL="https://api.example.test/v1",
        LLM_MODEL="test-model",
    )
    supported_source = {
        **source("source-1", "scholar-a"),
        "arabic_text": "The source discusses the interpretation of this passage.",
    }
    candidates = [{
        **candidate("source", "source-1"),
        "title": "How does this source explain the passage?",
        "prompt": "Describe the interpretation supported by this passage.",
    }]

    async def verify() -> set[int]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await chat_router.validate_candidate_grounding(
                "How does the interpretation work?",
                candidates,
                [supported_source],
                config=settings,
                client=client,
            )

    assert asyncio.run(verify()) == {0}
    assert request_payloads[0]["messages"][0]["content"].find(
        "untrusted data"
    ) >= 0
    user_payload = json.loads(request_payloads[0]["messages"][1]["content"])
    assert user_payload["candidates"][0]["supporting_sources"][0]["text"] == (
        supported_source["arabic_text"]
    )
    assert user_payload["candidates"][0]["index"] == 0


def test_candidate_generation_uses_the_configured_provider_key():
    def handler(request: httpx.Request) -> httpx.Response:
        authorization = request.headers.get("Authorization", "")
        assert authorization == f"Bearer {settings.translation_api_key}"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"suggestions":[]}'}}]},
        )

    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://postgres@localhost/quran_ai_test",
        LLM_API_KEY="test-key",
        LLM_API_BASE_URL="https://api.example.test/v1",
        LLM_MODEL="test-model",
    )
    assert settings.translation_api_key == "test-key"

    async def generate() -> list[object]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await generate_candidates(
                "How does the interpretation work?",
                [{
                    **source("source-1", "scholar-a"),
                    "arabic_text": "The source discusses the interpretation of this passage.",
                }],
                config=settings,
                client=client,
            )

    assert asyncio.run(generate()) == []


class ChatSuggestionsRouteTests(unittest.TestCase):
    def setUp(self):
        self.browser_id = uuid4()
        self.session_id = uuid4()
        self.message_id = uuid4()
        self.source_text = "A live approved source passage for this ayah."
        self.source_id = "qf:168:1:1"
        self.snapshot = {
            "browser_id": str(self.browser_id),
            "session_id": str(self.session_id),
            "message_id": str(self.message_id),
            "question": "How do the selected views differ?",
            "surah_number": 1,
            "ayah_number": 1,
            "selected_agent_ids": ["ibn_kathir"],
            "selected_source_ids": [self.source_id],
            "sources": [{
                "source_id": self.source_id,
                "resource_id": 168,
                "verse_key": "1:1",
                "similarity": 0.9,
                "content_hash": hashlib.sha256(self.source_text.encode()).hexdigest(),
                "scholar_id": "ibn_kathir",
                "scholar_name": "Scholar",
                "volume": None,
                "page": None,
                "source_kind": "tafsir",
            }],
        }
        self.live_source = {
            "passage_id": self.source_id,
            "resource_id": 168,
            "verse_key": "1:1",
            "arabic_text": self.source_text,
            "scholar_id": "ibn_kathir",
            "scholar_name": "Scholar",
            "volume": None,
            "page": None,
            "source_kind": "tafsir",
        }
        app.dependency_overrides[chat_router.current_browser_id] = lambda: self.browser_id
        self.client = TestClient(app)
        self.request_body = {
            "session_id": str(self.session_id),
            "message_id": str(self.message_id),
        }

    def tearDown(self):
        app.dependency_overrides.pop(chat_router.current_browser_id, None)
        self.client.close()

    def test_suggestions_endpoint_returns_empty_for_unknown_browser_message(self):
        with patch.object(chat_router, "get_engine"), patch.object(
            chat_router, "get_message_snapshot", return_value=None
        ):
            response = self.client.post("/api/v1/chat/suggestions", json=self.request_body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"suggestions": []})

    def test_endpoint_revalidates_exact_live_source_before_generation(self):
        with (
            patch.object(chat_router, "get_engine"),
            patch.object(chat_router, "get_message_snapshot", return_value=self.snapshot),
            patch.object(
                chat_router,
                "_approved_source_passages",
                new=AsyncMock(return_value=[self.live_source]),
            ),
            patch.object(
                chat_router,
                "generate_candidates",
                new=AsyncMock(return_value=[candidate("review", self.source_id)]),
            ) as generate,
            patch.object(
                chat_router,
                "validate_candidate_grounding",
                new=AsyncMock(return_value={0}),
            ) as validate,
        ):
            response = self.client.post("/api/v1/chat/suggestions", json=self.request_body)

        self.assertEqual(response.status_code, 200)
        suggestions = response.json()["suggestions"]
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["basisCount"], 1)
        self.assertEqual(suggestions[0]["evidence"], "AI_SYNTHESIS")
        generate.assert_awaited_once()
        validate.assert_awaited_once()

    def test_endpoint_drops_candidates_that_fail_grounding_validation(self):
        unsupported = {
            **candidate("review", self.source_id),
            "title": "What does this source say about dietary law?",
            "prompt": "Explain dietary law based on this unrelated source.",
        }
        with (
            patch.object(chat_router, "get_engine"),
            patch.object(chat_router, "get_message_snapshot", return_value=self.snapshot),
            patch.object(
                chat_router,
                "_approved_source_passages",
                new=AsyncMock(return_value=[self.live_source]),
            ),
            patch.object(
                chat_router,
                "generate_candidates",
                new=AsyncMock(return_value=[unsupported]),
            ),
            patch.object(
                chat_router,
                "validate_candidate_grounding",
                new=AsyncMock(return_value=set()),
                create=True,
            ) as validate,
        ):
            response = self.client.post("/api/v1/chat/suggestions", json=self.request_body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"suggestions": []})
        validate.assert_awaited_once()

    def test_suggestion_provider_failure_returns_retryable_service_error(self):
        with (
            patch.object(chat_router, "get_engine"),
            patch.object(chat_router, "get_message_snapshot", return_value=self.snapshot),
            patch.object(
                chat_router,
                "_approved_source_passages",
                new=AsyncMock(return_value=[self.live_source]),
            ),
            patch.object(
                chat_router,
                "generate_candidates",
                new=AsyncMock(side_effect=SuggestionGenerationError("private provider details")),
            ),
        ):
            response = self.client.post("/api/v1/chat/suggestions", json=self.request_body)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "Chat suggestions are temporarily unavailable")
        self.assertNotIn("private provider details", json.dumps(response.json()))

    def test_endpoint_does_not_generate_when_source_content_changed(self):
        changed_source = {**self.live_source, "arabic_text": "Changed source text."}
        with (
            patch.object(chat_router, "get_engine"),
            patch.object(chat_router, "get_message_snapshot", return_value=self.snapshot),
            patch.object(
                chat_router,
                "_approved_source_passages",
                new=AsyncMock(return_value=[changed_source]),
            ),
            patch.object(
                chat_router,
                "generate_candidates",
                new=AsyncMock(),
            ) as generate,
        ):
            response = self.client.post("/api/v1/chat/suggestions", json=self.request_body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"suggestions": []})
        generate.assert_not_awaited()

    def test_disabled_source_is_removed_from_generation_and_basis_count(self):
        extra_text = "A second source that is no longer enabled."
        second_source_id = "qf:170:1:1"
        snapshot = {
            **self.snapshot,
            "selected_agent_ids": ["ibn_kathir", "al_tabari"],
            "selected_source_ids": [self.source_id, second_source_id],
            "sources": [
                *self.snapshot["sources"],
                {
                    "source_id": second_source_id,
                    "resource_id": 170,
                    "verse_key": "1:1",
                    "similarity": 0.88,
                    "content_hash": hashlib.sha256(extra_text.encode()).hexdigest(),
                    "scholar_id": "al_tabari",
                    "scholar_name": "Second scholar",
                    "volume": None,
                    "page": None,
                    "source_kind": "tafsir",
                },
            ],
        }
        with (
            patch.object(chat_router, "get_engine"),
            patch.object(chat_router, "get_message_snapshot", return_value=snapshot),
            patch.object(
                chat_router,
                "_approved_source_passages",
                new=AsyncMock(return_value=[self.live_source]),
            ),
            patch.object(
                chat_router,
                "generate_candidates",
                new=AsyncMock(return_value=[candidate("review", self.source_id)]),
            ) as generate,
            patch.object(
                chat_router,
                "validate_candidate_grounding",
                new=AsyncMock(return_value={0}),
            ),
        ):
            response = self.client.post("/api/v1/chat/suggestions", json=self.request_body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["suggestions"][0]["basisCount"], 1)
        self.assertEqual(len(generate.await_args.args[1]), 1)

    def test_below_threshold_retrieval_never_reaches_generator(self):
        snapshot = {
            **self.snapshot,
            "sources": [{**self.snapshot["sources"][0], "similarity": 0.71}],
        }
        with (
            patch.object(chat_router, "get_engine"),
            patch.object(chat_router, "get_message_snapshot", return_value=snapshot),
            patch.object(chat_router, "_approved_source_passages", new=AsyncMock()) as fetch,
            patch.object(chat_router, "generate_candidates", new=AsyncMock()) as generate,
        ):
            response = self.client.post("/api/v1/chat/suggestions", json=self.request_body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"suggestions": []})
        fetch.assert_not_awaited()
        generate.assert_not_awaited()
