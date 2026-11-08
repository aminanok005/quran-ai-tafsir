from __future__ import annotations

import asyncio
import hashlib

import pytest

from services.api.services.retrieval_scoring import (
    RELEVANCE_THRESHOLD,
    qualifying_sources,
    score_retrieved_sources,
)


def _passage(source_id: str, text: str) -> dict[str, object]:
    return {
        "passage_id": source_id,
        "resource_id": 168,
        "verse_key": "1:1",
        "arabic_text": text,
        "scholar_id": "ibn_kathir",
        "scholar_name": "Tafsir Ibn Kathir",
        "volume": None,
        "page": None,
        "source_kind": "tafsir",
    }


def test_scores_exact_question_and_selected_passage_texts_in_one_batch():
    observed: list[list[str]] = []

    async def embed(texts):
        observed.append(list(texts))
        return [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]]

    question = "  Explain this selected ayah  "
    passages = [_passage("source-1", "Passage one"), _passage("source-2", "Passage two")]

    scored = asyncio.run(score_retrieved_sources(question, passages, embed_texts_fn=embed))

    assert observed == [[question, "Passage one", "Passage two"]]
    assert [item["similarity"] for item in scored] == [1.0, 0.0]
    assert scored[0]["source_id"] == "source-1"
    assert scored[0]["content_hash"] == hashlib.sha256(b"Passage one").hexdigest()


def test_empty_retrieval_does_not_call_embedding_provider():
    async def embed(_texts):
        raise AssertionError("embedding must not run for an empty retrieval")

    assert asyncio.run(score_retrieved_sources("question", [], embed_texts_fn=embed)) == []


def test_rejects_mismatched_embedding_dimensions():
    async def embed(_texts):
        return [[1.0, 0.0], [1.0, 0.0, 0.0]]

    with pytest.raises(ValueError, match="matching dimensions"):
        asyncio.run(
            score_retrieved_sources(
                "question",
                [_passage("source-1", "passage")],
                embed_texts_fn=embed,
            )
        )


@pytest.mark.parametrize("invalid", [True, float("nan"), float("inf")])
def test_rejects_boolean_or_non_finite_embedding_values(invalid):
    async def embed(_texts):
        return [[1.0, 0.0], [invalid, 1.0]]

    with pytest.raises(ValueError, match="finite numeric"):
        asyncio.run(
            score_retrieved_sources(
                "question",
                [_passage("source-1", "passage")],
                embed_texts_fn=embed,
            )
        )


def test_rejects_zero_norm_embedding_vectors():
    async def embed(_texts):
        return [[0.0, 0.0], [1.0, 0.0]]

    with pytest.raises(ValueError, match="non-zero norm"):
        asyncio.run(
            score_retrieved_sources(
                "question",
                [_passage("source-1", "passage")],
                embed_texts_fn=embed,
            )
        )


def test_provider_error_propagates_for_answer_flow_to_handle():
    class ProviderFailure(RuntimeError):
        pass

    async def embed(_texts):
        raise ProviderFailure("provider unavailable")

    with pytest.raises(ProviderFailure, match="provider unavailable"):
        asyncio.run(
            score_retrieved_sources(
                "question",
                [_passage("source-1", "passage")],
                embed_texts_fn=embed,
            )
        )


def test_only_scores_at_or_above_0_72_are_eligible():
    sources = [
        {"source_id": "below", "similarity": RELEVANCE_THRESHOLD - 0.0001},
        {"source_id": "at", "similarity": RELEVANCE_THRESHOLD},
        {"source_id": "above", "similarity": RELEVANCE_THRESHOLD + 0.0001},
    ]

    assert [item["source_id"] for item in qualifying_sources(sources)] == ["at", "above"]
