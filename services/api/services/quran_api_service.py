"""
Quran Foundation API service

This service handles all interactions with the Quran Foundation API,
including authentication, rate limiting, and caching.
"""

import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel
import json
from functools import wraps

from ..models import SurahModel, AyahModel, TranslationModel, WordTranslationModel
from ..config import settings

class QuranAPIError(Exception):
    """Custom exception for Quran API errors."""
    pass

class QuranAPIService:
    """Service for Quran Foundation API interactions."""

    def __init__(self):
        self.base_url = settings.quran_api_base_url.rstrip('/')
        self.client_id = settings.quran_api_client_id
        self.client_secret = settings.quran_api_client_secret
        self.token_cache: Dict[str, Dict[str, Any]] = {}
        self.http_client: Optional[httpx.AsyncClient] = None
        self.rate_limiter = RateLimiter(
            requests_per_minute=settings.rate_limit_per_minute,
            requests_per_hour=settings.rate_limit_per_hour
        )

    async def __aenter__(self):
        """Async context manager entry."""
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(30.0),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.http_client:
            await self.http_client.aclose()

    async def _get_token(self) -> str:
        """Get or refresh OAuth2 token."""
        current_time = datetime.now()

        # Check if we have a valid cached token
        if "access_token" in self.token_cache:
            token_data = self.token_cache["access_token"]
            expires_at = token_data.get("expires_at")
            if expires_at and current_time < expires_at:
                return token_data["token"]

        # Request new token
        try:
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }

            response = await self.http_client.post(
                "/oauth/token",
                data=auth_data,
                timeout=30.0
            )

            if response.status_code != 200:
                raise QuranAPIError(f"Token request failed: {response.text}")

            token_info = response.json()
            token_info["expires_at"] = current_time + timedelta(
                seconds=token_info.get("expires_in", settings.quran_api_token_cache_ttl)
            )

            self.token_cache["access_token"] = token_info

            return token_info["access_token"]

        except httpx.HTTPError as e:
            raise QuranAPIError(f"Failed to get token: {str(e)}")
        except json.JSONDecodeError:
            raise QuranAPIError("Invalid token response format")

    async def _rate_limit(self, operation: str):
        """Apply rate limiting."""
        await self.rate_limiter.acquire(operation)

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request."""
        operation = f"{method} {endpoint}"

        # Apply rate limiting
        await self.rate_limit(operation)

        # Get token
        token = await self._get_token()

        # Prepare headers
        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {token}",
            "X-API-Key": self.client_id,
        })

        # Make request
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )

            if response.status_code == 401:
                # Token expired, clear cache and retry
                self.token_cache.pop("access_token", None)
                token = await self._get_token()
                headers["Authorization"] = f"Bearer {token}"
                response = await self.http_client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise QuranAPIError("Rate limit exceeded")
            elif e.response.status_code == 404:
                raise QuranAPIError(f"Resource not found: {endpoint}")
            elif e.response.status_code == 403:
                raise QuranAPIError("Access forbidden")
            else:
                raise QuranAPIError(f"API request failed: {e.response.text}")
        except httpx.RequestError as e:
            raise QuranAPIError(f"Network error: {str(e)}")

    async def get_surah(self, surah_number: int) -> SurahModel:
        """Get Surah by number."""
        await self._rate_limit("get_surah")
        data = await self._make_request("GET", f"/surahs/{surah_number}")
        return SurahModel(**data)

    async def get_ayah(self, surah_number: int, ayah_number: int) -> AyahModel:
        """Get Ayah by surah and ayah numbers."""
        await self._rate_limit("get_ayah")
        data = await self._make_request("GET", f"/ayahs/{surah_number}/{ayah_number}")
        return AyahModel(**data)

    async def get_ayahs(self, surah_number: int) -> List[AyahModel]:
        """Get all ayahs for a surah."""
        await self._rate_limit("get_ayahs")
        data = await self._make_request("GET", f"/surahs/{surah_number}/ayahs")
        return [AyahModel(**ayah) for ayah in data]

    async def get_translations(self, surah_number: int, ayah_number: int) -> List[TranslationModel]:
        """Get translations for an ayah."""
        await self._rate_limit("get_translations")
        endpoint = f"/ayahs/{surah_number}/{ayah_number}/translations"
        data = await self._make_request("GET", endpoint)

        # Filter for Thai translation if available
        thai_translations = [
            TranslationModel(**translation) for translation in data
            if translation["language"] == "th"
        ]

        # If no Thai translation, use English as fallback
        if not thai_translations:
            thai_translations = [
                TranslationModel(**translation) for translation in data
                if translation["language"] == "en"
            ]

        return thai_translations

    async def get_word_translations(self, surah_number: int, ayah_number: int) -> List[WordTranslationModel]:
        """Get word-by-word translations for an ayah."""
        await self._rate_limit("get_word_translations")
        endpoint = f"/ayahs/{surah_number}/{ayah_number}/words"
        data = await self._make_request("GET", endpoint)
        return [WordTranslationModel(**word) for word in data]

    async def search_ayahs(self, query: str, language: str = "ar") -> List[Dict[str, Any]]:
        """Search for ayahs by text."""
        await self._rate_limit("search_ayahs")
        params = {"q": query, "language": language}
        data = await self._make_request("GET", "/search", params=params)
        return data.get("results", [])

class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, requests_per_minute: int, requests_per_hour: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_counters: Dict[str, List[datetime]] = {}
        self.hour_counters: Dict[str, List[datetime]] = {}

    async def acquire(self, operation: str):
        """Acquire a rate-limited operation."""
        now = datetime.now()

        # Clean old entries
        self._clean_old_entries(self.minute_counters, now, timedelta(minutes=1))
        self._clean_old_entries(self.hour_counters, now, timedelta(hours=1))

        # Check minute limit
        if operation not in self.minute_counters:
            self.minute_counters[operation] = []

        minute_count = len([
            req_time for req_time in self.minute_counters[operation]
            if now - req_time < timedelta(minutes=1)
        ])

        if minute_count >= self.requests_per_minute:
            wait_time = 60 - (now - self.minute_counters[operation][-1]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                # Clean up again after waiting
                self._clean_old_entries(self.minute_counters, now, timedelta(minutes=1))

        # Add current request
        self.minute_counters[operation].append(now)

        # Check hour limit
        if operation not in self.hour_counters:
            self.hour_counters[operation] = []

        hour_count = len([
            req_time for req_time in self.hour_counters[operation]
            if now - req_time < timedelta(hours=1)
        ])

        if hour_count >= self.requests_per_hour:
            raise QuranAPIError(f"Rate limit exceeded for {operation}")

        # Add to hour counter as well
        self.hour_counters[operation].append(now)

    def _clean_old_entries(self, counters: Dict[str, List[datetime]], now: datetime, time_window: timedelta):
        """Clean old entries from counters."""
        for operation, timestamps in list(counters.items()):
            counters[operation] = [
                ts for ts in timestamps if now - ts < time_window
            ]
            if not counters[operation]:
                del counters[operation]