"""Browser-scoped notes and grounded Studio artifact generation."""

from __future__ import annotations

import json
import logging
import time
from threading import Lock
from typing import Any, Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ..config import settings
from ..services.browser_identity import get_or_create_browser_id
from ..services.studio_generation import StudioGenerationError, generate_artifact

router = APIRouter(prefix="/workspace", tags=["Workspace"])
logger = logging.getLogger(__name__)
_engine: Engine | None = None
_studio_rate_lock = Lock()
_studio_requests: dict[UUID, list[float]] = {}
_STUDIO_LIMIT = 5
_STUDIO_WINDOW_SECONDS = 60

ArtifactKind = Literal[
    "audio",
    "report",
    "slides",
    "video",
    "flashcards",
    "quiz",
    "infographic",
    "comparison",
]


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def current_browser_id(request: Request, response: Response) -> UUID:
    return get_or_create_browser_id(request, response)


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="", max_length=50000)
    surah_number: int | None = Field(default=None, ge=1, le=114)
    ayah_number: int | None = Field(default=None, ge=1, le=286)
    source_label: str = Field(default="", max_length=255)

    @field_validator("title")
    @classmethod
    def require_nonblank_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Note title cannot be blank")
        return normalized


class NoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=50000)

    @field_validator("title")
    @classmethod
    def require_nonblank_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Note title cannot be blank")
        return normalized


class ArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ArtifactKind
    surah_number: int = Field(ge=1, le=114)
    ayah_number: int = Field(ge=1, le=286)
    surah_name: str = Field(min_length=1, max_length=120)
    arabic_text: str = Field(min_length=1, max_length=8000)
    translation: str = Field(default="", max_length=8000)
    tafsir_book_id: str | None = Field(default=None, max_length=100)
    selected_sources: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("selected_sources")
    @classmethod
    def validate_selected_sources(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)) or any(value not in {"quran", "tafsir"} for value in values):
            raise ValueError("Selected source IDs are invalid")
        return values


@router.get("/notes")
def list_notes(
    response: Response,
    browser_id: UUID = Depends(current_browser_id),
) -> dict[str, Any]:
    with get_engine().connect() as connection:
        rows = connection.execute(
            text("""
                SELECT id::text AS id, title, content, surah_number, ayah_number,
                       source_label, created_at, updated_at
                FROM user_notes
                WHERE browser_id = :browser_id
                ORDER BY updated_at DESC
                LIMIT 200
            """),
            {"browser_id": browser_id},
        ).mappings().all()
    return {"success": True, "data": [dict(row) for row in rows]}


@router.post("/notes", status_code=201)
def create_note(
    note: NoteCreate,
    response: Response,
    browser_id: UUID = Depends(current_browser_id),
) -> dict[str, Any]:
    with get_engine().begin() as connection:
        row = connection.execute(
            text("""
                INSERT INTO user_notes (
                    browser_id, title, content, surah_number, ayah_number, source_label
                )
                VALUES (
                    :browser_id, :title, :content, :surah_number, :ayah_number, :source_label
                )
                RETURNING id::text AS id, title, content, surah_number, ayah_number,
                          source_label, created_at, updated_at
            """),
            {"browser_id": browser_id, **note.model_dump()},
        ).mappings().one()
    return {"success": True, "data": dict(row)}


@router.patch("/notes/{note_id}")
def update_note(
    note_id: UUID,
    update: NoteUpdate,
    response: Response,
    browser_id: UUID = Depends(current_browser_id),
) -> dict[str, Any]:
    changes = update.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide a title or note body to update")
    assignments = ", ".join(f"{key} = :{key}" for key in changes)
    with get_engine().begin() as connection:
        row = connection.execute(
            text(f"""
                UPDATE user_notes
                SET {assignments}
                WHERE id = :note_id AND browser_id = :browser_id
                RETURNING id::text AS id, title, content, surah_number, ayah_number,
                          source_label, created_at, updated_at
            """),
            {**changes, "note_id": note_id, "browser_id": browser_id},
        ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True, "data": dict(row)}


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(
    note_id: UUID,
    response: Response,
    browser_id: UUID = Depends(current_browser_id),
) -> Response:
    with get_engine().begin() as connection:
        result = connection.execute(
            text("DELETE FROM user_notes WHERE id = :note_id AND browser_id = :browser_id"),
            {"note_id": note_id, "browser_id": browser_id},
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    response.status_code = 204
    return response


@router.post("/artifacts")
async def create_artifact(
    request: ArtifactRequest,
    browser_id: UUID = Depends(current_browser_id),
) -> dict[str, Any]:
    if "quran" not in request.selected_sources:
        raise HTTPException(status_code=422, detail="Select the Quran source to ground this artifact")
    if not settings.translation_api_key or not settings.llm_api_base_url or not settings.llm_model:
        raise HTTPException(status_code=503, detail="Studio generation is not configured")
    if len(request.arabic_text) + len(request.translation) > 16000:
        raise HTTPException(status_code=413, detail="Selected source context is too long")
    now = time.monotonic()
    with _studio_rate_lock:
        recent = [
            timestamp
            for timestamp in _studio_requests.get(browser_id, [])
            if now - timestamp < _STUDIO_WINDOW_SECONDS
        ]
        if len(recent) >= _STUDIO_LIMIT:
            raise HTTPException(status_code=429, detail="Studio generation is limited to five requests per minute")
        _studio_requests[browser_id] = [*recent, now]

    tafsir_context: dict[str, str] | None = None
    if "tafsir" in request.selected_sources:
        if not request.tafsir_book_id:
            raise HTTPException(status_code=422, detail="Select an approved Tafsir book")
        with get_engine().connect() as connection:
            row = connection.execute(
                text("""
                    SELECT p.arabic_text, b.title,
                           COALESCE(sp.source_url, b.source_url, p.source_url) AS source_url
                    FROM tafsir_passages AS p
                    JOIN tafsir_books AS b ON b.id = p.book_id
                    LEFT JOIN source_permissions AS sp ON sp.source_id = b.book_id
                    WHERE p.surah_number = :surah
                      AND p.ayah_start <= :ayah
                      AND p.ayah_end >= :ayah
                      AND b.book_id = :book_id
                      AND b.permission_status::text = 'approved'
                      AND b.verification_status::text = 'verified'
                      AND sp.permission_status::text = 'approved'
                      AND sp.verification_status::text = 'verified'
                    ORDER BY p.created_at DESC
                    LIMIT 1
                """),
                {
                    "surah": request.surah_number,
                    "ayah": request.ayah_number,
                    "book_id": request.tafsir_book_id,
                },
            ).mappings().first()
        if row is None:
            raise HTTPException(
                status_code=403,
                detail="This Tafsir source has not been approved for AI-derived study artifacts",
            )
        tafsir_context = {
            "text": row["arabic_text"],
            "title": row["title"],
            "source_url": row["source_url"] or "",
        }

    source_context = {
        "reference": f"{request.surah_name} {request.surah_number}:{request.ayah_number}",
        "arabic": request.arabic_text,
        "translation": request.translation,
        "tafsir": tafsir_context["text"] if tafsir_context else "",
        "tafsir_source": tafsir_context["title"] if tafsir_context else "",
        "selected_sources": request.selected_sources,
    }
    try:
        content = await generate_artifact(
            request.kind,
            source_context,
            api_key=settings.translation_api_key,
            model=settings.llm_model,
            base_url=settings.llm_api_base_url,
            wire_api=settings.llm_api_wire_api,
        )
    except httpx.HTTPStatusError as error:
        status = error.response.status_code
        logger.warning("Studio provider returned HTTP %s", status)
        raise HTTPException(
            status_code=503 if status >= 500 or status == 429 else 502,
            detail="The configured AI provider could not generate this artifact",
        ) from error
    except (httpx.RequestError, StudioGenerationError) as error:
        logger.warning("Studio generation failed: %s", type(error).__name__)
        raise HTTPException(status_code=502, detail="AI returned an invalid Studio artifact") from error

    return {
        "success": True,
        "data": {
            "kind": request.kind,
            "title": content["title"],
            "summary": content["summary"],
            "sections": content["sections"],
            "slides": content["slides"],
            "scenes": content["scenes"],
            "questions": content["questions"],
            "flashcards": content["flashcards"],
            "rows": content["rows"],
            "sources": [
                {
                    "id": "quran",
                    "label": source_context["reference"],
                    "url": f"https://quran.com/{request.surah_number}/{request.ayah_number}",
                },
                *(
                    [{
                        "id": "tafsir",
                        "label": tafsir_context["title"],
                        "url": tafsir_context["source_url"] or None,
                    }]
                    if tafsir_context
                    else []
                ),
            ],
            "evidence_status": "AI-SYNTHESIS",
        },
    }
