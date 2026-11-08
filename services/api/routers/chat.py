"""Browser-scoped chat follow-up endpoints."""

from __future__ import annotations

import logging
from hashlib import sha256
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError

from ..services.chat_message_store import get_message_snapshot
from ..services.chat_suggestions import (
    Suggestion,
    SuggestionGenerationError,
    filter_suggestions,
    generate_candidates,
    validate_candidate_grounding,
)
from ..services.retrieval_scoring import qualifying_sources
from .agents import _approved_source_passages
from .tafsir import get_engine
from .workspace import current_browser_id

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


class SuggestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    message_id: UUID


class SuggestionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestions: list[Suggestion] = Field(max_length=4)


@router.post("/suggestions", response_model=SuggestionsResponse)
async def get_chat_suggestions(
    request: SuggestionRequest,
    browser_id: UUID = Depends(current_browser_id),
) -> SuggestionsResponse:
    try:
        snapshot = get_message_snapshot(
            get_engine(),
            browser_id=browser_id,
            session_id=request.session_id,
            message_id=request.message_id,
        )
        if snapshot is None:
            return SuggestionsResponse(suggestions=[])

        retrieval_sources = qualifying_sources(snapshot["sources"])
        if not retrieval_sources:
            return SuggestionsResponse(suggestions=[])

        selected_source_ids = set(snapshot["selected_source_ids"])
        selected_agent_ids = set(snapshot["selected_agent_ids"])
        current_passages = await _approved_source_passages(
            snapshot["surah_number"],
            snapshot["ayah_number"],
            snapshot["selected_agent_ids"],
        )
        current_by_id = {
            passage["passage_id"]: passage
            for passage in current_passages
            if passage["passage_id"] in selected_source_ids
        }

        validated_sources: list[dict[str, Any]] = []
        source_texts: dict[str, str] = {}
        for recorded in retrieval_sources:
            source_id = recorded["source_id"]
            live = current_by_id.get(source_id)
            if live is None:
                continue
            passage_text = live.get("arabic_text")
            if (
                not isinstance(passage_text, str)
                or not passage_text.strip()
                or live.get("resource_id") != recorded["resource_id"]
                or live.get("verse_key") != recorded["verse_key"]
                or live.get("scholar_id") not in selected_agent_ids
                or live.get("scholar_id") != recorded["scholar_id"]
                or sha256(passage_text.encode("utf-8")).hexdigest()
                != recorded["content_hash"]
            ):
                continue
            validated_sources.append({
                **recorded,
                "arabic_text": passage_text,
            })
            source_texts[source_id] = passage_text

        if not validated_sources:
            return SuggestionsResponse(suggestions=[])

        candidates = await generate_candidates(snapshot["question"], validated_sources)
        verified_candidate_indices = await validate_candidate_grounding(
            snapshot["question"],
            candidates,
            validated_sources,
        )
        return SuggestionsResponse(
            suggestions=[
                Suggestion.model_validate(suggestion)
                for suggestion in filter_suggestions(
                    candidates,
                    validated_sources,
                    source_texts=source_texts,
                    verified_candidate_indices=verified_candidate_indices,
                )
            ]
        )
    except (
        HTTPException,
        SQLAlchemyError,
        SuggestionGenerationError,
        RuntimeError,
        ValueError,
    ) as error:
        logger.warning(
            "Chat suggestions unavailable (%s)",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="Chat suggestions are temporarily unavailable",
        ) from error


__all__ = ["router"]
