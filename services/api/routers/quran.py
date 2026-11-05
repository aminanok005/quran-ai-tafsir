"""
Quran data router

Handles all Quran Foundation API proxy endpoints for surahs, ayahs, translations,
and search functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models import AyahModel, TranslationModel, WordTranslationModel, SearchResponseModel
from ..services import QuranAPIService

router = APIRouter(tags=["Quran"])
logger = logging.getLogger(__name__)

# Initialize service
quran_service = QuranAPIService()

@router.get("/surahs", response_model=List[Dict[str, Any]])
async def get_surahs():
    """Get all surahs with basic information."""
    try:
        response = await quran_service.http_client.get("/surahs")
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching surahs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch surahs")

@router.get("/surahs/{surah_number}", response_model=Dict[str, Any])
async def get_surah(surah_number: int):
    """Get specific surah by number."""
    try:
        if not (1 <= surah_number <= 114):
            raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")

        response = await quran_service.http_client.get(f"/surahs/{surah_number}")
        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching surah {surah_number}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch surah")

@router.get("/ayahs/{surah_number}/{ayah_number}", response_model=Dict[str, Any])
async def get_ayah(surah_number: int, ayah_number: int):
    """Get specific ayah by surah and ayah numbers."""
    try:
        response = await quran_service.http_client.get(f"/ayahs/{surah_number}/{ayah_number}")
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching ayah {surah_number}:{ayah_number}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ayah")

@router.get("/ayahs/{surah_number}/{ayah_number}/translations", response_model=List[Dict[str, Any]])
async def get_translations(
    surah_number: int,
    ayah_number: int,
    language: Optional[str] = Query(default="th", description="Translation language")
):
    """Get translations for an ayah."""
    try:
        endpoint = f"/ayahs/{surah_number}/{ayah_number}/translations"
        params = {"language": language} if language else {}
        response = await quran_service.http_client.get(endpoint, params=params)
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching translations for {surah_number}:{ayah_number}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch translations")

@router.get("/ayahs/{surah_number}/{ayah_number}/words", response_model=List[Dict[str, Any]])
async def get_word_translations(
    surah_number: int,
    ayah_number: int
):
    """Get word-by-word translations for an ayah."""
    try:
        response = await quran_service.http_client.get(
            f"/ayahs/{surah_number}/{ayah_number}/words"
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching word translations for {surah_number}:{ayah_number}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch word translations")

@router.get("/search", response_model=Dict[str, Any])
async def search_quran(
    query: str = Query(..., description="Search query"),
    language: str = Query(default="ar", description="Search language"),
    surah_number: Optional[int] = Query(None, description="Filter by surah number"),
    page: int = Query(default=1, gt=0, description="Page number"),
    per_page: int = Query(default=10, gt=0, le=100, description="Items per page")
):
    """Search Quran text."""
    try:
        params = {
            "q": query,
            "language": language,
            "page": page,
            "per_page": per_page
        }

        if surah_number:
            params["surah"] = surah_number

        response = await quran_service.http_client.get("/search", params=params)
        return response.json()
    except Exception as e:
        logger.error(f"Error searching Quran: {e}")
        raise HTTPException(status_code=500, detail="Failed to search Quran")

@router.get("/surahs/{surah_number}/ayahs", response_model=List[Dict[str, Any]])
async def get_surah_ayahs(surah_number: int):
    """Get all ayahs for a specific surah."""
    try:
        if not (1 <= surah_number <= 114):
            raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")

        response = await quran_service.http_client.get(f"/surahs/{surah_number}/ayahs")
        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching surah ayahs {surah_number}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch surah ayahs")

@router.get("/random-ayah", response_model=Dict[str, Any])
async def get_random_ayah():
    """Get a random ayah."""
    try:
        response = await quran_service.http_client.get("/ayahs/random")
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching random ayah: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch random ayah")

@router.get("/metadata/languages", response_model=List[str])
async def get_supported_languages():
    """Get list of supported languages."""
    try:
        response = await quran_service.http_client.get("/metadata/languages")
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching supported languages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch supported languages")

@router.get("/metadata/surahs", response_model=List[Dict[str, Any]])
async def get_surah_metadata():
    """Get metadata for all surahs."""
    try:
        response = await quran_service.http_client.get("/metadata/surahs")
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching surah metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch surah metadata")

@router.get("/health/quran-api", response_model=Dict[str, Any])
async def quran_api_health():
    """Check Quran Foundation API health."""
    try:
        response = await quran_service.http_client.get("/health")
        return response.json()
    except Exception as e:
        logger.error(f"Quran API health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@router.get("/stats", response_model=Dict[str, Any])
async def get_api_stats():
    """Get API usage statistics."""
    try:
        # Get basic stats from Quran API
        surahs_response = await quran_service.http_client.get("/surahs")
        surahs_count = len(surahs_response.json())

        # This would typically include cache stats, rate limit stats, etc.
        return {
            "total_surahs": surahs_count,
            "total_ayahs": 6236,  # Quran has 6236 verses
            "supported_languages": ["th", "ar", "en"],
            "api_version": "v1",
            "timestamp": datetime.now().isoformat(),
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API stats")