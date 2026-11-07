"""Tafsir passage lookup and Thai translation for development and database sources."""

import logging
import time
from threading import Lock
from typing import Any, Dict
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ..config import settings
from ..services.quran_foundation_tafsir import (
    QuranFoundationTafsir,
    QuranFoundationTafsirClient,
    QuranFoundationTafsirError,
)
from ..services.tafsir_api_storage import upsert_development_qf_tafsir
from ..services.tafsir_translation import (
    TranslationProviderError,
    translate_tafsir_to_thai,
)
from ..services.tafsir_json import split_tafsir_text

router = APIRouter(prefix="/tafsir", tags=["Tafsir"])
logger = logging.getLogger(__name__)

BOOK_IDS = {
    "ibn_kathir": "tafsir_ibn_kathir",
    "al_tabari": "jami_al_bayan",
    "al_qurtubi": "jami_ahkam",
    "al_saadi": "taysir_karim",
}

_engine: Engine | None = None
_rate_lock = Lock()
_translation_requests: Dict[str, list[float]] = {}
_development_translations: Dict[str, str] = {}
_development_translation_lock = Lock()
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
        )
    return _qf_tafsir_client


def _translation_is_allowed(passage: Dict[str, Any]) -> bool:
    return (
        passage["permission_status"] == "approved"
        and passage["book_verification_status"] == "verified"
        and passage["registered_permission_status"] == "approved"
        and passage["registered_verification_status"] == "verified"
        and bool(passage["verification_evidence"])
        and bool(passage["license"])
        and bool(passage["source_url"])
    )


def _get_passage(
    engine: Engine,
    surah: int,
    ayah: int,
    book_id: str,
    *,
    include_development: bool = False,
) -> Dict[str, Any] | None:
    statement = text("""
        SELECT
            p.id::text AS passage_id,
            p.surah_number,
            p.ayah_start,
            p.ayah_end,
            p.arabic_text,
            p.thai_translation,
            p.volume,
            p.page,
            p.edition,
            p.source_url AS passage_source_url,
            p.verification_status::text AS evidence_status,
            b.book_id,
            b.metadata AS book_metadata,
            b.title AS book_title,
            b.title_ar AS book_title_ar,
            COALESCE(sp.license, b.license) AS license,
            b.source_url AS book_source_url,
            b.permission_status::text AS permission_status,
            b.verification_status::text AS book_verification_status,
            COALESCE(sp.verification_evidence, b.verification_evidence) AS verification_evidence,
            COALESCE(sp.source_url, b.source_url, p.source_url) AS source_url,
            s.name AS scholar_name,
            sp.permission_status::text AS registered_permission_status,
            sp.verification_status::text AS registered_verification_status
        FROM tafsir_passages AS p
        JOIN tafsir_books AS b ON b.id = p.book_id
        JOIN scholars AS s ON s.id = b.scholar_id
        LEFT JOIN source_permissions AS sp ON sp.source_id = b.book_id
        WHERE p.surah_number = :surah
          AND p.ayah_start <= :ayah
          AND p.ayah_end >= :ayah
          AND b.book_id = :book_id
          AND (
              :include_development = TRUE
              OR (
                  b.permission_status::text = 'approved'
                  AND b.verification_status::text = 'verified'
                  AND sp.permission_status::text = 'approved'
                  AND sp.verification_status::text = 'verified'
              )
          )
        ORDER BY p.created_at DESC
        LIMIT 1
    """)
    with engine.connect() as connection:
        row = connection.execute(
            statement,
            {
                "surah": surah,
                "ayah": ayah,
                "book_id": book_id,
                "include_development": include_development,
            },
        ).mappings().first()
    return dict(row) if row else None


def _public_passage(passage: Dict[str, Any]) -> Dict[str, Any]:
    translation_allowed = _translation_is_allowed(passage)
    is_development = passage["permission_status"] == "development_only"
    return {
        "id": passage["passage_id"],
        "surah_number": passage["surah_number"],
        "ayah_start": passage["ayah_start"],
        "ayah_end": passage["ayah_end"],
        "arabic_text": passage["arabic_text"],
        "thai_translation": passage["thai_translation"] if translation_allowed else None,
        "evidence_status": str(passage["evidence_status"]).upper(),
        "translation_allowed": translation_allowed,
        "translation_block_reason": (
            None if translation_allowed else
            "การแปลด้วย AI ถูกระงับจนกว่าสิทธิ์ ใบอนุญาต และหลักฐานการตรวจสอบแหล่งข้อมูลจะได้รับอนุมัติ"
        ),
        "development_mode": is_development,
        "source": {
            "book_id": passage["book_id"],
            "title": passage["book_title"],
            "title_ar": passage["book_title_ar"],
            "scholar": passage["scholar_name"],
            "edition": passage["edition"],
            "volume": passage["volume"],
            "page": passage["page"],
            "url": passage["passage_source_url"] or passage["book_source_url"],
            "permission_status": passage["permission_status"],
            "provider": (
                "Quran Foundation Content API"
                if str(passage["book_id"]).startswith("qf_tafsir_")
                else None
            ),
        },
    }


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


async def _translate_development_passage(source_text: str) -> str:
    api_key = settings.translation_api_key
    provider = settings.llm_provider
    base_url = settings.llm_api_base_url
    model = settings.llm_model
    if not provider or not base_url or not api_key or not model:
        raise HTTPException(
            status_code=503,
            detail=(
                "LLM translation is not configured. Set LLM_API_KEY for custom providers; "
                "OPENAI_API_KEY is used only with api.openai.com."
            ),
        )
    translations = []
    for chunk in split_tafsir_text(source_text):
        translations.append(await translate_tafsir_to_thai(
            chunk,
            api_key=api_key,
            model=model,
            base_url=base_url,
            wire_api=settings.llm_api_wire_api,
        ))
    return "\n\n".join(translations)


@router.get("/passages/{surah}/{ayah}", response_model=Dict[str, Any])
async def get_tafsir_passage(surah: int, ayah: int, agent_type: str):
    """Return one source passage for the selected ayah and scholar."""
    if not 1 <= surah <= 114 or not 1 <= ayah <= 286:
        raise HTTPException(status_code=422, detail="Invalid surah or ayah number")
    resource_id = settings.quran_tafsir_resource_map.get(agent_type)
    book_id = f"qf_tafsir_{resource_id}" if resource_id else BOOK_IDS.get(agent_type)
    if book_id is None:
        raise HTTPException(status_code=404, detail="No imported tafsir source is available for this scholar")

    is_development = settings.environment.lower() == "development"
    engine = get_engine()
    passage = _get_passage(
        engine,
        surah,
        ayah,
        book_id,
        include_development=is_development,
    )
    if passage is not None:
        return {"success": True, "data": _public_passage(passage)}

    if settings.environment.lower() == "development":
        if not resource_id:
            raise HTTPException(status_code=404, detail="No Tafsir API resource is configured for this scholar")
        client = get_qf_tafsir_client()
        try:
            api_passage: QuranFoundationTafsir = await client.fetch_ayah(
                resource_id,
                surah,
                ayah,
            )
        except QuranFoundationTafsirError as error:
            status_code = 503 if error.status_code is None or error.status_code >= 500 else 502
            logger.warning(
                "Quran Foundation Tafsir request failed (HTTP %s)",
                error.status_code or "network",
            )
            raise HTTPException(status_code=status_code, detail=str(error)) from error
        source_url = (
            f"{client.content_api_url}/tafsirs/{resource_id}/by_ayah/{surah}:{ayah}"
        )
        try:
            upsert_development_qf_tafsir(engine, api_passage, source_url=source_url)
        except ValueError as error:
            logger.error("Quran Foundation Tafsir development cache write was refused")
            raise HTTPException(status_code=409, detail="Tafsir source is not development-only") from error
        passage = _get_passage(
            engine,
            surah,
            ayah,
            book_id,
            include_development=True,
        )
        if passage is None:
            raise HTTPException(status_code=503, detail="Fetched Tafsir passage was not persisted")
        return {"success": True, "data": _public_passage(passage)}

    raise HTTPException(status_code=404, detail="No approved Tafsir passage was found for this ayah")


@router.post("/passages/dev/{surah}/{ayah}/translate", response_model=Dict[str, Any])
async def translate_development_passage(surah: int, ayah: int, agent_type: str, request: Request):
    """Translate a passage only when its source has approved rights and verification."""
    if settings.environment.lower() != "development":
        raise HTTPException(status_code=404, detail="Development-only tafsir translation is unavailable")
    if not 1 <= surah <= 114 or not 1 <= ayah <= 286:
        raise HTTPException(status_code=422, detail="Invalid surah or ayah number")
    resource_id = settings.quran_tafsir_resource_map.get(agent_type)
    book_id = f"qf_tafsir_{resource_id}" if resource_id else BOOK_IDS.get(agent_type)
    if book_id is None:
        raise HTTPException(status_code=404, detail="No Tafsir source is configured for this scholar")
    passage = _get_passage(
        get_engine(),
        surah,
        ayah,
        book_id,
        include_development=True,
    )
    if passage is None:
        raise HTTPException(status_code=404, detail="No Tafsir passage was found for this ayah")
    if not _translation_is_allowed(passage):
        raise HTTPException(status_code=403, detail="Source rights and verification must be approved before translation")

    cache_key = str(passage["passage_id"])
    cached = _development_translations.get(cache_key)
    if cached:
        return {"success": True, "data": {"thai_translation": cached, "cached": True}}

    _enforce_translation_rate_limit(request)

    try:
        translation = await _translate_development_passage(passage["arabic_text"])
    except httpx.TimeoutException as error:
        logger.warning("OpenAI development tafsir translation timed out for %s", cache_key)
        raise HTTPException(status_code=504, detail="Thai translation timed out; please try again") from error
    except httpx.HTTPStatusError as error:
        logger.error("OpenAI returned HTTP %s for development tafsir %s", error.response.status_code, cache_key)
        raise _translation_provider_http_exception(error) from error
    except (httpx.RequestError, TranslationProviderError) as error:
        logger.error("OpenAI translation failed for development tafsir %s: %s", cache_key, type(error).__name__)
        raise HTTPException(status_code=502, detail="OpenAI could not translate this tafsir passage") from error

    with _development_translation_lock:
        existing_translation = _development_translations.get(cache_key)
        if existing_translation:
            return {
                "success": True,
                "data": {"thai_translation": existing_translation, "cached": True},
            }
        _development_translations[cache_key] = translation
    return {
        "success": True,
        "data": {
            "thai_translation": translation,
            "cached": False,
        },
    }


@router.post("/passages/{passage_id}/translate", response_model=Dict[str, Any])
async def translate_passage(passage_id: UUID, request: Request):
    """Translate an approved source passage to Thai and cache it in the database."""
    _enforce_translation_rate_limit(request)
    api_key = settings.translation_api_key
    provider = settings.llm_provider
    base_url = settings.llm_api_base_url
    model = settings.llm_model
    engine = get_engine()
    statement = text("""
        SELECT
            p.id::text AS passage_id,
            p.arabic_text,
            p.thai_translation,
            p.permission_status::text AS permission_status,
            p.book_verification_status::text AS book_verification_status,
            p.registered_permission_status::text AS registered_permission_status,
            p.registered_verification_status::text AS registered_verification_status,
            p.verification_evidence,
            p.license,
            p.source_url
        FROM (
            SELECT
                p.id,
                p.arabic_text,
                p.thai_translation,
                b.permission_status,
                b.verification_status AS book_verification_status,
                sp.permission_status AS registered_permission_status,
                sp.verification_status AS registered_verification_status,
                COALESCE(sp.verification_evidence, b.verification_evidence) AS verification_evidence,
                COALESCE(sp.license, b.license) AS license,
                COALESCE(sp.source_url, b.source_url, p.source_url) AS source_url
            FROM tafsir_passages AS p
            JOIN tafsir_books AS b ON b.id = p.book_id
            LEFT JOIN source_permissions AS sp ON sp.source_id = b.book_id
            WHERE p.id = :passage_id
        ) AS p
    """)
    with engine.connect() as connection:
        row = connection.execute(statement, {"passage_id": str(passage_id)}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Tafsir passage not found")

    passage = dict(row)
    if not _translation_is_allowed(passage):
        raise HTTPException(status_code=403, detail="Source rights and verification must be approved before translation")
    if passage["thai_translation"]:
        return {"success": True, "data": {"thai_translation": passage["thai_translation"], "cached": True}}
    if not provider or not base_url or not api_key or not model:
        raise HTTPException(
            status_code=503,
            detail=(
                "LLM translation is not configured. Set LLM_API_KEY for custom providers; "
                "OPENAI_API_KEY is used only with api.openai.com."
            ),
        )
    if len(passage["arabic_text"]) > 30000:
        raise HTTPException(status_code=413, detail="This tafsir passage is too long to translate in one request")

    try:
        translation = await translate_tafsir_to_thai(
            passage["arabic_text"],
            api_key=api_key,
            model=model,
            base_url=base_url,
            wire_api=settings.llm_api_wire_api,
        )
    except httpx.TimeoutException as error:
        logger.warning("OpenAI tafsir translation timed out for passage %s", passage_id)
        raise HTTPException(status_code=504, detail="Thai translation timed out; please try again") from error
    except httpx.HTTPStatusError as error:
        logger.error("OpenAI returned HTTP %s for tafsir passage %s", error.response.status_code, passage_id)
        raise _translation_provider_http_exception(error) from error
    except (httpx.RequestError, TranslationProviderError) as error:
        logger.error("OpenAI translation failed for tafsir passage %s: %s", passage_id, type(error).__name__)
        raise HTTPException(status_code=502, detail="OpenAI could not translate this tafsir passage") from error

    update = text("""
        UPDATE tafsir_passages
        SET thai_translation = :translation, updated_at = CURRENT_TIMESTAMP
        WHERE id = :passage_id
          AND (thai_translation IS NULL OR btrim(thai_translation) = '')
        RETURNING thai_translation
    """)
    with engine.begin() as connection:
        result = connection.execute(
            update,
            {"passage_id": str(passage_id), "translation": translation},
        ).scalar_one_or_none()
        if result is None:
            result = connection.execute(
                text("SELECT thai_translation FROM tafsir_passages WHERE id = :passage_id"),
                {"passage_id": str(passage_id)},
            ).scalar_one()
            return {"success": True, "data": {"thai_translation": result, "cached": True}}

    return {"success": True, "data": {"thai_translation": result, "cached": False}}
