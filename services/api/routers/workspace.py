"""Browser-scoped notes and grounded Studio artifact generation."""

from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ..config import settings
from ..services.browser_identity import get_or_create_browser_id
from ..services.quran_foundation_tafsir import QuranFoundationTafsirError
from ..services.quran_metadata import is_valid_ayah
from ..services.studio_generation import StudioGenerationError, generate_artifact
from .tafsir import (
    _get_api_source_permission,
    _translation_is_allowed,
    get_qf_tafsir_client,
)

router = APIRouter(prefix="/workspace", tags=["Workspace"])
logger = logging.getLogger(__name__)
_engine: Engine | None = None
_studio_rate_lock = Lock()
_studio_requests: dict[UUID, list[float]] = {}
_STUDIO_LIMIT = 5
_STUDIO_WINDOW_SECONDS = 60
_LOCAL_LLM_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

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


def _is_loopback_provider_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname in _LOCAL_LLM_HOSTS
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )


def _trusted_qf_content_api_base(content_api_url: str) -> str:
    try:
        configured = urlsplit(settings.quran_api_base_url)
        content_api = urlsplit(content_api_url)
        _ = configured.port
        _ = content_api.port
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="Quran Foundation Content API URL is not safely configured",
        ) from None

    if (
        configured.scheme != "https"
        or content_api.scheme != "https"
        or configured.hostname is None
        or content_api.hostname != configured.hostname
        or configured.username is not None
        or configured.password is not None
        or content_api.username is not None
        or content_api.password is not None
        or content_api.query
        or content_api.fragment
    ):
        raise HTTPException(
            status_code=503,
            detail="Quran Foundation Content API URL is not safely configured",
        )
    return content_api_url.rstrip("/")


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
    if not is_valid_ayah(request.surah_number, request.ayah_number):
        raise HTTPException(status_code=422, detail="Selected Quran verse is invalid")
    if "quran" not in request.selected_sources:
        raise HTTPException(status_code=422, detail="Select the Quran source to ground this artifact")
    if settings.environment != "development":
        raise HTTPException(
            status_code=403,
            detail="Studio generation is available only in the development environment",
        )
    missing_settings = [
        name
        for name, value in (
            ("LLM_API_KEY", settings.translation_api_key),
            ("LLM_API_BASE_URL", settings.llm_api_base_url),
            ("LLM_MODEL", settings.llm_model),
        )
        if not value
    ]
    if missing_settings:
        raise HTTPException(
            status_code=503,
            detail=f"Studio generation is missing configuration: {', '.join(missing_settings)}",
        )
    if not _is_loopback_provider_url(settings.llm_api_base_url):
        raise HTTPException(
            status_code=503,
            detail="LLM_API_BASE_URL must use a valid loopback host for local Studio generation",
        )
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
            raise HTTPException(status_code=422, detail="Select an approved Quran Foundation Tafsir resource")
        resource_suffix = request.tafsir_book_id.removeprefix("qf_tafsir_")
        if (
            not resource_suffix.isdecimal()
            or request.tafsir_book_id != f"qf_tafsir_{resource_suffix}"
        ):
            raise HTTPException(status_code=422, detail="Select a configured Quran Foundation Tafsir resource")
        resource_id = int(resource_suffix)
        if resource_id not in settings.quran_tafsir_resource_map.values():
            raise HTTPException(
                status_code=403,
                detail="This Quran Foundation Tafsir resource is not configured for this application",
            )
        permission = _get_api_source_permission(get_engine(), resource_id)
        if not _translation_is_allowed(permission) or permission is None:
            raise HTTPException(
                status_code=403,
                detail="This Tafsir source has not been approved for AI-derived study artifacts",
            )
        try:
            client = get_qf_tafsir_client()
            passage = client.get_cached_ayah(
                resource_id,
                request.surah_number,
                request.ayah_number,
            )
        except QuranFoundationTafsirError as error:
            status_code = 503 if error.status_code is None or error.status_code >= 500 else 502
            logger.warning(
                "Quran Foundation Tafsir cache lookup failed for Studio (HTTP %s)",
                error.status_code or "network",
            )
            raise HTTPException(
                status_code=status_code,
                detail="Could not read the approved Quran Foundation Tafsir cache",
            ) from error
        expected_verse_key = f"{request.surah_number}:{request.ayah_number}"
        if passage is None:
            raise HTTPException(
                status_code=409,
                detail="Load the Tafsir passage first, then retry Studio generation",
            )
        if passage.verse_key != expected_verse_key:
            raise HTTPException(
                status_code=409,
                detail="The cached Tafsir passage does not match the selected Quran verse",
            )
        content_api_base = _trusted_qf_content_api_base(client.content_api_url)
        tafsir_context = {
            "text": passage.text,
            "title": f"Tafsir resource {resource_id}",
            "resource_id": str(resource_id),
            "source_url": (
                f"{content_api_base}/tafsirs/{resource_id}/by_ayah/{expected_verse_key}"
            ),
        }

    context_length = len(request.arabic_text) + len(request.translation)
    if tafsir_context:
        context_length += len(tafsir_context["text"])
    if context_length > 16000:
        raise HTTPException(status_code=413, detail="Selected source context is too long")

    source_context = {
        "reference": f"{request.surah_name} {request.surah_number}:{request.ayah_number}",
        "arabic": request.arabic_text,
        "translation": request.translation,
        "tafsir": tafsir_context["text"] if tafsir_context else "",
        "tafsir_source": tafsir_context["title"] if tafsir_context else "",
        "selected_sources": request.selected_sources,
        "source_ids": ["quran", *([f"tafsir-{tafsir_context['resource_id']}"] if tafsir_context else [])],
    }
    try:
        content = await generate_artifact(
            request.kind,
            source_context,
            api_key=settings.translation_api_key,
            model=settings.llm_model,
            base_url=settings.llm_api_base_url,
            wire_api=settings.llm_api_wire_api,
            allowed_source_ids=set(source_context["source_ids"]),
        )
    except httpx.HTTPStatusError as error:
        status = error.response.status_code
        logger.warning("Studio provider returned HTTP %s", status)
        raise HTTPException(
            status_code=503 if status >= 500 or status == 429 else 502,
            detail="The configured AI provider could not generate this artifact",
        ) from error
    except StudioGenerationError as error:
        if error.status_code is not None:
            logger.warning("Studio provider returned HTTP %s", error.status_code)
            raise HTTPException(
                status_code=(
                    503
                    if error.status_code >= 500 or error.status_code == 429
                    else 502
                ),
                detail="The configured AI provider could not generate this artifact",
            ) from error
        logger.warning("Studio generation failed: %s", type(error).__name__)
        raise HTTPException(status_code=502, detail="AI returned an invalid Studio artifact") from error
    except httpx.RequestError as error:
        logger.warning("Studio generation failed: %s", type(error).__name__)
        raise HTTPException(status_code=502, detail="AI returned an invalid Studio artifact") from error

    sources = [
        {
            "id": "quran",
            "label": f"Quran {request.surah_number}:{request.ayah_number}",
            "url": f"https://quran.com/{request.surah_number}/{request.ayah_number}",
        },
        *(
            [
                {
                    "id": f"tafsir-{tafsir_context['resource_id']}",
                    "label": tafsir_context["title"],
                    "url": tafsir_context["source_url"],
                }
            ]
            if tafsir_context
            else []
        ),
    ]
    if request.kind in {"audio", "quiz", "infographic"}:
        return {
            "success": True,
            "data": {
                "kind": request.kind,
                "artifact": content,
                "sources": sources,
                "evidence_status": "AI-SYNTHESIS",
            },
        }

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
            "sources": sources,
            "evidence_status": "AI-SYNTHESIS",
        },
    }
