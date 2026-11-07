"""Rights-filtered semantic search for Tafsir passages."""

import time
from threading import Lock
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from ..config import settings
from ..services.embedding import (
    EmbeddingConfigurationError,
    EmbeddingProviderError,
    embed_texts,
)
from ..services.tafsir_retrieval import search_tafsir
from .tafsir import get_engine

router = APIRouter(prefix="/tafsir", tags=["Tafsir retrieval"])
_search_lock = Lock()
_search_requests: dict[str, list[float]] = {}
_SEARCH_RATE_LIMIT = 30
_SEARCH_RATE_WINDOW_SECONDS = 60


def _enforce_search_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    cutoff = now - _SEARCH_RATE_WINDOW_SECONDS
    with _search_lock:
        for ip in list(_search_requests):
            recent = [item for item in _search_requests[ip] if item > cutoff]
            if recent:
                _search_requests[ip] = recent
            else:
                del _search_requests[ip]
        recent = _search_requests.setdefault(client_ip, [])
        if len(recent) >= _SEARCH_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Tafsir search limit reached; try again later")
        recent.append(now)


class TafsirSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    surah_number: int | None = Field(default=None, ge=1, le=114)
    ayah_number: int | None = Field(default=None, ge=1, le=286)
    scholar_id: str | None = Field(default=None, min_length=1, max_length=80)
    top_k: int = Field(default=5, ge=1, le=20)
    include_development: bool = False

    @model_validator(mode="after")
    def require_ayah_filter_pair(self) -> "TafsirSearchRequest":
        if (self.surah_number is None) != (self.ayah_number is None):
            raise ValueError("surah_number and ayah_number must be provided together")
        return self


@router.post("/search", response_model=dict[str, Any])
async def semantic_tafsir_search(
    payload: TafsirSearchRequest,
    request: Request,
) -> dict[str, Any]:
    """Search approved sources; development data requires an explicit dev-only request."""
    if payload.include_development and settings.environment.lower() != "development":
        raise HTTPException(
            status_code=403,
            detail="Development-only Tafsir search is disabled outside development.",
        )
    _enforce_search_rate_limit(request)

    try:
        vectors = await embed_texts([payload.query])
    except EmbeddingConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EmbeddingProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    results = search_tafsir(
        get_engine(),
        vectors[0],
        surah_number=payload.surah_number,
        ayah_number=payload.ayah_number,
        scholar_id=payload.scholar_id,
        top_k=payload.top_k,
        include_development=payload.include_development,
    )
    return {
        "success": True,
        "data": {
            "results": results,
            "count": len(results),
            "mode": "development" if payload.include_development else "approved",
        },
    }


__all__ = ["TafsirSearchRequest", "router", "semantic_tafsir_search"]
