"""Score the exact selected source passages used for a grounded answer."""

from __future__ import annotations

import math
from collections.abc import Awaitable, Callable, Mapping, Sequence
from hashlib import sha256
from typing import Any

from .chat_message_store import SourceSnapshot
from .embedding import embed_texts

RELEVANCE_THRESHOLD = 0.72
EmbeddingFunction = Callable[[Sequence[str]], Awaitable[list[list[float]]]]


def _validated_vectors(vectors: object, expected_count: int) -> list[list[float]]:
    if not isinstance(vectors, (list, tuple)) or len(vectors) != expected_count:
        raise ValueError("Embedding provider returned an incomplete vector batch")

    normalized: list[list[float]] = []
    dimensions: int | None = None
    for vector in vectors:
        if not isinstance(vector, (list, tuple)) or not vector:
            raise ValueError("Embedding provider returned a malformed vector")
        if dimensions is None:
            dimensions = len(vector)
        if len(vector) != dimensions:
            raise ValueError("Embedding vectors must have matching dimensions")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in vector
        ):
            raise ValueError("Embedding vectors must contain finite numeric values")

        values = [float(value) for value in vector]
        norm = math.hypot(*values)
        if not math.isfinite(norm):
            raise ValueError("Embedding vector norm must be finite")
        if norm == 0:
            raise ValueError("Embedding vectors must have a non-zero norm")
        normalized.append([value / norm for value in values])
    return normalized


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    score = math.fsum(a * b for a, b in zip(left, right, strict=True))
    if not math.isfinite(score):
        raise ValueError("Cosine similarity must be finite")
    if score < -1 or score > 1:
        if -1 - 1e-6 <= score <= 1 + 1e-6:
            return max(-1.0, min(1.0, score))
        raise ValueError("Cosine similarity is outside [-1, 1]")
    return score


async def score_retrieved_sources(
    question: str,
    passages: Sequence[Mapping[str, Any]],
    *,
    embed_texts_fn: EmbeddingFunction = embed_texts,
) -> list[dict[str, Any]]:
    """Return exact source metadata with cosine scores and text hashes."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must not be empty")
    if not passages:
        return []

    passage_texts = [passage.get("arabic_text") for passage in passages]
    if any(not isinstance(text, str) or not text.strip() for text in passage_texts):
        raise ValueError("Every retrieved source must include non-empty arabic_text")

    vectors = _validated_vectors(
        await embed_texts_fn([question, *passage_texts]),
        len(passages) + 1,
    )
    question_vector = vectors[0]
    scored: list[dict[str, Any]] = []
    for passage, passage_text, passage_vector in zip(
        passages,
        passage_texts,
        vectors[1:],
        strict=True,
    ):
        candidate = SourceSnapshot.model_validate({
            "source_id": passage.get("passage_id"),
            "resource_id": passage.get("resource_id"),
            "verse_key": passage.get("verse_key"),
            "similarity": _cosine_similarity(question_vector, passage_vector),
            "content_hash": sha256(passage_text.encode("utf-8")).hexdigest(),
            "scholar_id": passage.get("scholar_id"),
            "scholar_name": passage.get("scholar_name"),
            "volume": passage.get("volume"),
            "page": passage.get("page"),
            "source_kind": passage.get("source_kind", "tafsir"),
        })
        scored.append(candidate.model_dump(mode="json"))
    return scored


def qualifying_sources(
    sources: Sequence[Mapping[str, Any]],
    *,
    threshold: float = RELEVANCE_THRESHOLD,
) -> list[Mapping[str, Any]]:
    """Keep only sources with a valid score at or above the relevance threshold."""
    if not math.isfinite(threshold) or not -1 <= threshold <= 1:
        raise ValueError("threshold must be a finite cosine score")

    qualifying: list[Mapping[str, Any]] = []
    for source in sources:
        score = source.get("similarity")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
            or not -1 <= score <= 1
        ):
            raise ValueError("retrieved source has an invalid similarity score")
        if score >= threshold:
            qualifying.append(source)
    return qualifying


__all__ = [
    "RELEVANCE_THRESHOLD",
    "qualifying_sources",
    "score_retrieved_sources",
]
