"""OpenAI-compatible embedding client using a dedicated embedding credential."""

from __future__ import annotations

import math
from typing import Sequence
from urllib.parse import urlsplit

import httpx

from ..config import Settings, settings

DATABASE_VECTOR_DIMENSIONS = 1536


class EmbeddingConfigurationError(RuntimeError):
    """Raised when embedding configuration is missing or incompatible with the schema."""


class EmbeddingProviderError(RuntimeError):
    """Raised when the embedding provider cannot return valid vectors."""


def _embedding_endpoint(config: Settings) -> tuple[str, str, str, int]:
    provider = (config.embedding_provider or "openai").strip().lower()
    if provider not in {"openai", "openai_compatible"}:
        raise EmbeddingConfigurationError("Unsupported embedding provider.")

    api_key = config.embedding_api_key
    if not api_key:
        raise EmbeddingConfigurationError("EMBEDDING_API_KEY is required for vector search.")

    base_url = config.embedding_api_base_url
    if not base_url:
        if provider != "openai":
            raise EmbeddingConfigurationError(
                "EMBEDDING_API_BASE_URL is required for an OpenAI-compatible provider."
            )
        base_url = "https://api.openai.com/v1"

    parsed_url = urlsplit(base_url)
    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise EmbeddingConfigurationError("EMBEDDING_API_BASE_URL must be a valid HTTP(S) URL.")
    if parsed_url.scheme == "http" and parsed_url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise EmbeddingConfigurationError("HTTP embedding endpoints are allowed only on loopback.")

    dimensions = config.embedding_dimensions or DATABASE_VECTOR_DIMENSIONS
    if dimensions != DATABASE_VECTOR_DIMENSIONS:
        raise EmbeddingConfigurationError(
            f"Vector dimensions must match the database schema ({DATABASE_VECTOR_DIMENSIONS})."
        )
    model = config.embedding_model or "text-embedding-3-small"
    return f"{base_url.rstrip('/')}/embeddings", api_key, model, dimensions


async def embed_texts(
    texts: Sequence[str],
    *,
    client: httpx.AsyncClient | None = None,
    config: Settings = settings,
) -> list[list[float]]:
    """Embed text without logging request content or falling back to an LLM credential."""
    if not texts or any(not item.strip() for item in texts):
        raise ValueError("Embedding input must contain non-empty text.")

    endpoint, api_key, model, dimensions = _embedding_endpoint(config)
    request_client = client
    if request_client is None:
        async with httpx.AsyncClient(timeout=config.embedding_timeout_seconds) as owned_client:
            return await embed_texts(texts, client=owned_client, config=config)

    try:
        response = await request_client.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "input": list(texts), "dimensions": dimensions},
        )
        response.raise_for_status()
    except httpx.TimeoutException as error:
        raise EmbeddingProviderError("Embedding provider request timed out.") from error
    except httpx.HTTPStatusError as error:
        raise EmbeddingProviderError(
            f"Embedding provider returned HTTP {error.response.status_code}."
        ) from error
    except httpx.RequestError as error:
        raise EmbeddingProviderError("Embedding provider could not be reached.") from error

    try:
        payload = response.json()
    except ValueError as error:
        raise EmbeddingProviderError("Embedding provider returned invalid JSON.") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise EmbeddingProviderError("Embedding provider response is missing vectors.")

    vectors: list[list[float] | None] = [None] * len(texts)
    for item in payload["data"]:
        if not isinstance(item, dict):
            raise EmbeddingProviderError("Embedding provider returned a malformed vector.")
        index = item.get("index")
        vector = item.get("embedding")
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or index < 0
            or index >= len(texts)
            or vectors[index] is not None
            or not isinstance(vector, list)
            or len(vector) != dimensions
        ):
            raise EmbeddingProviderError("Embedding provider returned vectors with an invalid shape.")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in vector
        ):
            raise EmbeddingProviderError("Embedding provider returned non-numeric vector values.")
        vectors[index] = [float(value) for value in vector]

    if any(vector is None for vector in vectors):
        raise EmbeddingProviderError("Embedding provider returned an incomplete vector batch.")
    return [vector for vector in vectors if vector is not None]


__all__ = [
    "DATABASE_VECTOR_DIMENSIONS",
    "EmbeddingConfigurationError",
    "EmbeddingProviderError",
    "embed_texts",
]
