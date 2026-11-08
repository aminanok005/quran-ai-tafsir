"""HTTP endpoints for Quran translation audio."""

import httpx
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from ..config import settings
from ..services.translation_audio import TranslationAudioService

router = APIRouter(prefix="/quran/translation-audio", tags=["Quran translation audio"])


def create_translation_audio_service() -> TranslationAudioService:
    return TranslationAudioService(
        settings=settings,
        redis_client=redis.Redis.from_url(settings.redis_url, decode_responses=True),
        http_client=httpx.AsyncClient(),
    )


def get_translation_audio_service(request: Request) -> TranslationAudioService:
    service = getattr(request.app.state, "translation_audio_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Translation audio service is unavailable")
    return service


@router.get("/capabilities")
async def get_translation_audio_capabilities(
    service: TranslationAudioService = Depends(get_translation_audio_service),
) -> dict[str, object]:
    return service.capabilities()


@router.get("/{surah}/{ayah}")
async def get_translation_audio(
    surah: int,
    ayah: int,
    request: Request,
    edition: str = Query(...),
    speed: float = Query(1.0),
    service: TranslationAudioService = Depends(get_translation_audio_service),
) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    result = await service.synthesize(surah, ayah, edition, speed, client_ip)
    return Response(
        content=result.audio,
        media_type="audio/mpeg",
        headers={"X-Audio-Cache": "hit" if result.cached else "miss"},
    )
