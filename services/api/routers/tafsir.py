"""Fetch live Quran Foundation Tafsir and cache permission-approved translations."""

import hashlib
import logging
import time
from threading import Lock
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ..config import settings
from ..services.gemini_http import http_status_for
from ..services.gemini_provider import GeminiError
from ..services.gemini_translation import translate_ayah
from ..services.model_router import ModelRouter
from ..services.quran_foundation_tafsir import (
    QuranFoundationTafsir,
    QuranFoundationTafsirClient,
    QuranFoundationTafsirError,
)
from ..services.tafsir_translation import (
    TranslationProviderError,
    translate_tafsir_to_thai,
)

router = APIRouter(prefix="/tafsir", tags=["Tafsir"])
logger = logging.getLogger(__name__)

_engine: Engine | None = None
_rate_lock = Lock()
_translation_requests: Dict[str, list[float]] = {}
_TRANSLATION_RATE_LIMIT = 5
_TRANSLATION_RATE_WINDOW_SECONDS = 60
_qf_tafsir_client: QuranFoundationTafsirClient | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_qf_tafsir_client() -> QuranFoundationTafsirClient:
    global _qf_tafsir_client
    if _qf_tafsir_client is None:
        _qf_tafsir_client = QuranFoundationTafsirClient(
            api_base_url=settings.quran_api_base_url,
            auth_base_url=settings.quran_api_auth_base_url,
            client_id=settings.quran_api_client_id,
            client_secret=settings.quran_api_client_secret,
            scope=settings.quran_api_tafsir_scope,
            token_cache_ttl=settings.quran_api_token_cache_ttl,
            passage_cache_ttl=settings.quran_api_tafsir_cache_ttl,
        )
    return _qf_tafsir_client


def _translation_is_allowed(permission: Dict[str, Any] | None) -> bool:
    if permission is None:
        return False
    return (
        permission.get("permission_status") == "approved"
        and permission.get("verification_status") == "verified"
        and bool(permission.get("verification_evidence"))
        and bool(permission.get("license"))
        and bool(permission.get("source_url"))
    )


def _get_api_source_permission(
    engine: Engine,
    resource_id: int,
) -> Dict[str, Any] | None:
    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT source_id, source_url, license,
                       permission_status::text AS permission_status,
                       verification_status::text AS verification_status,
                       verification_evidence
                FROM source_permissions
                WHERE source_id = :source_id
            """),
            {"source_id": f"qf_tafsir_{resource_id}"},
        ).mappings().first()
    return dict(row) if row else None


def _api_source_url(client: QuranFoundationTafsirClient, resource_id: int, verse_key: str) -> str:
    return f"{client.content_api_url}/tafsirs/{resource_id}/by_ayah/{verse_key}"


def _public_api_passage(
    passage: QuranFoundationTafsir,
    source_url: str,
    permission: Dict[str, Any] | None,
    thai_translation: str | None,
) -> Dict[str, Any]:
    is_approved = _translation_is_allowed(permission)
    return {
        "id": f"qf:{passage.resource_id}:{passage.verse_key}",
        "surah_number": int(passage.verse_key.split(":", 1)[0]),
        "ayah_start": int(passage.verse_key.split(":", 1)[1]),
        "ayah_end": int(passage.verse_key.split(":", 1)[1]),
        "arabic_text": passage.text,
        "thai_translation": thai_translation if is_approved else None,
        "evidence_status": "SOURCE-ATTRIBUTED",
        "translation_allowed": is_approved,
        "translation_block_reason": None if is_approved else (
            "การแปลด้วย AI ถูกระงับจนกว่าสิทธิ์ ใบอนุญาต และหลักฐานการตรวจสอบแหล่งข้อมูลจะได้รับอนุมัติ"
        ),
        "development_mode": False,
        "source": {
            "book_id": f"qf_tafsir_{passage.resource_id}",
            "title": passage.resource_name,
            "title_ar": None,
            "scholar": passage.resource_name,
            "edition": passage.slug or None,
            "volume": None,
            "page": None,
            "url": source_url,
            "permission_status": permission.get("permission_status", "pending") if permission else "pending",
            "provider": "Quran Foundation Content API",
            "resource_id": passage.resource_id,
            "language_name": passage.language_name,
            "slug": passage.slug,
        },
    }


def _cached_api_translation(
    engine: Engine,
    resource_id: int,
    surah: int,
    ayah: int,
    source_hash: str,
) -> str | None:
    with engine.connect() as connection:
        return connection.execute(
            text("""
                SELECT translated_text
                FROM tafsir_api_translations
                WHERE resource_id = :resource_id
                  AND surah_number = :surah
                  AND ayah_number = :ayah
                  AND target_language = 'th'
                  AND source_hash = :source_hash
            """),
            {
                "resource_id": resource_id,
                "surah": surah,
                "ayah": ayah,
                "source_hash": source_hash,
            },
        ).scalar_one_or_none()


def _save_api_translation(
    engine: Engine,
    passage: QuranFoundationTafsir,
    source_url: str,
    source_hash: str,
    translation: str,
) -> str:
    with engine.begin() as connection:
        return connection.execute(
            text("""
                INSERT INTO tafsir_api_translations (
                    resource_id, surah_number, ayah_number, target_language,
                    translated_text, source_hash, source_url, model
                )
                VALUES (
                    :resource_id, :surah, :ayah, 'th',
                    :translation, :source_hash, :source_url, :model
                )
                ON CONFLICT (
                    resource_id, surah_number, ayah_number,
                    target_language, source_hash
                )
                DO UPDATE SET translated_text = tafsir_api_translations.translated_text
                RETURNING translated_text
            """),
            {
                "resource_id": passage.resource_id,
                "surah": int(passage.verse_key.split(":", 1)[0]),
                "ayah": int(passage.verse_key.split(":", 1)[1]),
                "translation": translation,
                "source_hash": source_hash,
                "source_url": source_url,
                "model": settings.llm_model,
            },
        ).scalar_one()


def _enforce_translation_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    cutoff = now - _TRANSLATION_RATE_WINDOW_SECONDS
    with _rate_lock:
        for ip in list(_translation_requests):
            recent = [item for item in _translation_requests[ip] if item > cutoff]
            if recent:
                _translation_requests[ip] = recent
            else:
                del _translation_requests[ip]
        recent = _translation_requests.setdefault(client_ip, [])
        if len(recent) >= _TRANSLATION_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Translation request limit reached; try again later")
        recent.append(now)


def _translation_provider_http_exception(error: httpx.HTTPStatusError) -> HTTPException:
    try:
        payload = error.response.json()
    except ValueError:
        payload = {}
    provider_error = payload.get("error", {}) if isinstance(payload, dict) else {}
    error_type = provider_error.get("type") if isinstance(provider_error, dict) else None
    error_code = provider_error.get("code") if isinstance(provider_error, dict) else None
    status_code = error.response.status_code
    logger.error(
        "Translation provider returned HTTP %s (type=%s, code=%s)",
        status_code,
        error_type if isinstance(error_type, str) else "unknown",
        error_code if isinstance(error_code, str) else "unknown",
    )

    if status_code in (401, 403):
        return HTTPException(
            status_code=502,
            detail=(
                "ผู้ให้บริการแปลปฏิเสธ API key กรุณาตรวจ LLM_API_KEY สำหรับ custom endpoint "
                "หรือ OPENAI_API_KEY เมื่อเชื่อมต่อ api.openai.com"
            ),
        )
    if status_code == 404:
        return HTTPException(
            status_code=502,
            detail="ไม่พบ OpenAI endpoint หรือ model ที่ตั้งค่าไว้ กรุณาตรวจ LLM_API_BASE_URL และ LLM_MODEL",
        )
    if status_code == 400:
        return HTTPException(
            status_code=502,
            detail="OpenAI ปฏิเสธรูปแบบคำขอแปล กรุณาตรวจว่า LLM_MODEL รองรับ Chat Completions",
        )
    if status_code >= 500:
        return HTTPException(
            status_code=503,
            detail="OpenAI ขัดข้องชั่วคราว กรุณารอสักครู่แล้วลองใหม่",
        )

    if status_code != 429:
        return HTTPException(
            status_code=502,
            detail=f"ผู้ให้บริการแปลปฏิเสธคำขอ (HTTP {status_code}) กรุณาตรวจการตั้งค่า OpenAI",
        )

    if error_type == "insufficient_quota" or error_code in {
        "insufficient_quota",
        "credit_balance_exhausted",
    }:
        return HTTPException(
            status_code=429,
            detail=(
                "OpenAI แจ้งว่าเครดิตหรือโควตาการใช้งานหมด "
                "กรุณาเติมเครดิตหรือเพิ่มวงเงินในบัญชี OpenAI ที่ผูกกับ API key "
                "หรือเปลี่ยนไปใช้ผู้ให้บริการที่มีโควตาพร้อมใช้งาน"
            ),
        )
    return HTTPException(
        status_code=429,
        detail="OpenAI จำกัดจำนวนคำขอชั่วคราว กรุณารอสักครู่แล้วลองใหม่",
    )


@router.get("/passages/{surah}/{ayah}", response_model=Dict[str, Any])
async def get_tafsir_passage(surah: int, ayah: int, agent_type: str):
    """Fetch the current source passage from Quran Foundation, never local corpus data."""
    if not 1 <= surah <= 114 or not 1 <= ayah <= 286:
        raise HTTPException(status_code=422, detail="Invalid surah or ayah number")
    resource_id = settings.quran_tafsir_resource_map.get(agent_type)
    if resource_id is None:
        raise HTTPException(status_code=404, detail="No Quran Foundation Tafsir resource is configured for this scholar")
    try:
        client = get_qf_tafsir_client()
        api_passage = await client.fetch_ayah(resource_id, surah, ayah)
    except QuranFoundationTafsirError as error:
        status_code = 503 if error.status_code is None or error.status_code >= 500 else 502
        logger.warning(
            "Quran Foundation Tafsir request failed (HTTP %s)",
            error.status_code or "network",
        )
        raise HTTPException(status_code=status_code, detail=str(error)) from error

    source_url = _api_source_url(client, resource_id, api_passage.verse_key)
    engine = get_engine()
    permission = _get_api_source_permission(engine, resource_id)
    source_hash = hashlib.sha256(api_passage.text.encode("utf-8")).hexdigest()
    translated_text = (
        _cached_api_translation(
            engine,
            resource_id,
            surah,
            ayah,
            source_hash,
        )
        if _translation_is_allowed(permission)
        else None
    )
    return {
        "success": True,
        "data": _public_api_passage(
            api_passage,
            source_url,
            permission,
            translated_text,
        ),
    }


async def _translate_api_passage(
    surah: int,
    ayah: int,
    agent_type: str,
    request: Request,
) -> Dict[str, Any]:
    if not 1 <= surah <= 114 or not 1 <= ayah <= 286:
        raise HTTPException(status_code=422, detail="Invalid surah or ayah number")
    resource_id = settings.quran_tafsir_resource_map.get(agent_type)
    if resource_id is None:
        raise HTTPException(status_code=404, detail="No Quran Foundation Tafsir resource is configured for this scholar")

    try:
        client = get_qf_tafsir_client()
        passage = await client.fetch_ayah(resource_id, surah, ayah)
    except QuranFoundationTafsirError as error:
        status_code = 503 if error.status_code is None or error.status_code >= 500 else 502
        logger.warning(
            "Quran Foundation Tafsir request failed during translation (HTTP %s)",
            error.status_code or "network",
        )
        raise HTTPException(status_code=status_code, detail=str(error)) from error

    source_url = _api_source_url(client, resource_id, passage.verse_key)
    engine = get_engine()
    permission = _get_api_source_permission(engine, resource_id)
    if not _translation_is_allowed(permission):
        raise HTTPException(
            status_code=403,
            detail="Source rights and verification must be approved before translation",
        )
    source_hash = hashlib.sha256(passage.text.encode("utf-8")).hexdigest()
    cached = _cached_api_translation(engine, resource_id, surah, ayah, source_hash)
    if cached:
        return {"success": True, "data": {"thai_translation": cached, "cached": True}}

    api_key = settings.translation_api_key
    if not settings.llm_provider or not settings.llm_api_base_url or not api_key or not settings.llm_model:
        raise HTTPException(
            status_code=503,
            detail=(
                "LLM translation is not configured. Set LLM_API_KEY for custom providers; "
                "OPENAI_API_KEY is used only with api.openai.com."
            ),
        )
    if len(passage.text) > 30000:
        raise HTTPException(status_code=413, detail="This Tafsir passage is too long to translate in one request")
    _enforce_translation_rate_limit(request)

    try:
        translation = await translate_tafsir_to_thai(
            passage.text,
            api_key=api_key,
            model=settings.llm_model,
            base_url=settings.llm_api_base_url,
            wire_api=settings.llm_api_wire_api,
        )
    except httpx.TimeoutException as error:
        logger.warning("Tafsir API translation timed out for resource %s", resource_id)
        raise HTTPException(status_code=504, detail="Thai translation timed out; please try again") from error
    except httpx.HTTPStatusError as error:
        logger.error("Translation provider returned HTTP %s", error.response.status_code)
        raise _translation_provider_http_exception(error) from error
    except (httpx.RequestError, TranslationProviderError) as error:
        logger.error("Tafsir translation failed (%s)", type(error).__name__)
        raise HTTPException(status_code=502, detail="Could not translate this Tafsir passage") from error

    saved_translation = _save_api_translation(
        engine,
        passage,
        source_url,
        source_hash,
        translation,
    )
    return {
        "success": True,
        "data": {
            "thai_translation": saved_translation,
            "cached": saved_translation != translation,
        },
    }


@router.post("/passages/api/{surah}/{ayah}/translate", response_model=Dict[str, Any])
async def translate_api_passage(surah: int, ayah: int, agent_type: str, request: Request):
    """Translate a live API passage and persist only the generated translation."""
    return await _translate_api_passage(surah, ayah, agent_type, request)


@router.post("/gemini-translation", response_model=Dict[str, Any])
async def gemini_translation(surah: int, ayah: int, agent_type: str, request: Request):
    """Grounded Arabic-to-Thai translation; Arabic text and sources come from approved passages."""
    if not (1 <= surah <= 114 and 1 <= ayah <= 200):
        raise HTTPException(status_code=400, detail="Ayah is out of range")
    _enforce_translation_rate_limit(request)
    from . import agents as agents_router

    passages = await agents_router._approved_source_passages(surah, ayah, [agent_type])
    if not passages:
        raise HTTPException(
            status_code=503,
            detail="No approved, verified Tafsir passages are available for this ayah",
        )
    passage = passages[0]
    sources = [
        {
            "source_id": item["passage_id"],
            "scholar_name": item.get("scholar_name"),
            "text": item["arabic_text"],
            "volume": item.get("volume"),
            "page": item.get("page"),
        }
        for item in passages
    ]
    try:
        record = await translate_ayah(
            ModelRouter(),
            verse_key=passage["verse_key"],
            arabic_text=passage["arabic_text"],
            sources=sources,
        )
    except GeminiError as error:
        raise HTTPException(
            status_code=http_status_for(error),
            detail="Translation provider is unavailable",
        ) from error
    return {"success": True, "data": record}


@router.post("/passages/{passage_id}/translate", response_model=Dict[str, Any])
async def translate_passage(passage_id: str, request: Request):
    """Reject legacy database passage IDs; source Tafsir is fetched from Quran Foundation."""
    raise HTTPException(
        status_code=410,
        detail="Local Tafsir passage translation is retired; use the Quran Foundation API route",
    )
