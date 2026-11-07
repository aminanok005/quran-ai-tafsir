"""Authenticated access to Quran Foundation Content API Tafsir passages."""

from __future__ import annotations

from dataclasses import dataclass
import html
import re
import time
from typing import Any
from urllib.parse import urlsplit

import httpx


AUTH_BASE_URLS = {
    "apis.quran.foundation": "https://oauth2.quran.foundation",
    "apis-prelive.quran.foundation": "https://prelive-oauth2.quran.foundation",
}


class QuranFoundationTafsirError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class QuranFoundationTafsir:
    resource_id: int
    resource_name: str
    language_name: str
    slug: str
    verse_key: str
    text: str


def resolve_auth_base_url(api_base_url: str, configured_url: str | None = None) -> str:
    if configured_url:
        return configured_url.rstrip("/")
    api_host = urlsplit(api_base_url).hostname
    auth_base_url = AUTH_BASE_URLS.get(api_host or "")
    if auth_base_url is None:
        raise QuranFoundationTafsirError(
            "Set QURAN_API_AUTH_BASE_URL for this Quran Foundation API host"
        )
    return auth_base_url


def _plain_text(value: str) -> str:
    text = " ".join(html.unescape(re.sub(r"<[^>]*>", " ", value)).split())
    return re.sub(r"\s+([.,!?;:،؛؟])", r"\1", text)


class QuranFoundationTafsirClient:
    def __init__(
        self,
        *,
        api_base_url: str,
        client_id: str,
        client_secret: str,
        scope: str = "content.tafsirs.read",
        auth_base_url: str | None = None,
        token_cache_ttl: int = 3300,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        if self.api_base_url.endswith("/content/api/v4"):
            self.content_api_url = self.api_base_url
            self.api_base_url = self.api_base_url.removesuffix("/content/api/v4")
        else:
            self.content_api_url = f"{self.api_base_url}/content/api/v4"
        if not client_id or client_id.startswith("REPLACE_WITH"):
            raise QuranFoundationTafsirError("QURAN_API_CLIENT_ID is not configured")
        if not client_secret or client_secret.startswith("REPLACE_WITH"):
            raise QuranFoundationTafsirError("QURAN_API_CLIENT_SECRET is not configured")
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.auth_url = f"{resolve_auth_base_url(self.api_base_url, auth_base_url)}/oauth2/token"
        self.token_cache_ttl = token_cache_ttl
        self.transport = transport
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock: Any = None

    async def _get_access_token(self) -> str:
        now = time.monotonic()
        if self._access_token and now < self._token_expires_at:
            return self._access_token
        if self._token_lock is None:
            import asyncio

            self._token_lock = asyncio.Lock()
        async with self._token_lock:
            now = time.monotonic()
            if self._access_token and now < self._token_expires_at:
                return self._access_token
            async with httpx.AsyncClient(
                timeout=30.0,
                transport=self.transport,
            ) as client:
                try:
                    response = await client.post(
                        self.auth_url,
                        auth=(self.client_id, self.client_secret),
                        data={"grant_type": "client_credentials", "scope": self.scope},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    response.raise_for_status()
                    payload = response.json()
                except httpx.HTTPStatusError as error:
                    raise QuranFoundationTafsirError(
                        "Quran Foundation authentication failed",
                        status_code=error.response.status_code,
                    ) from error
                except (httpx.RequestError, ValueError) as error:
                    raise QuranFoundationTafsirError(
                        "Quran Foundation authentication request failed"
                    ) from error

            token = payload.get("access_token") if isinstance(payload, dict) else None
            if not isinstance(token, str) or not token:
                raise QuranFoundationTafsirError(
                    "Quran Foundation token response is invalid"
                )
            expires_in = payload.get("expires_in")
            ttl = expires_in if isinstance(expires_in, (int, float)) and expires_in > 0 else self.token_cache_ttl
            self._access_token = token
            self._token_expires_at = time.monotonic() + min(ttl, self.token_cache_ttl)
            return token

    async def fetch_ayah(self, resource_id: int, surah: int, ayah: int) -> QuranFoundationTafsir:
        token = await self._get_access_token()
        verse_key = f"{surah}:{ayah}"
        async with httpx.AsyncClient(
            timeout=30.0,
            transport=self.transport,
        ) as client:
            try:
                response = await client.get(
                    f"{self.content_api_url}/tafsirs/{resource_id}/by_ayah/{verse_key}",
                    headers={
                        "x-auth-token": token,
                        "x-client-id": self.client_id,
                    },
                )
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as error:
                raise QuranFoundationTafsirError(
                    "Quran Foundation Tafsir request failed",
                    status_code=error.response.status_code,
                ) from error
            except (httpx.RequestError, ValueError) as error:
                raise QuranFoundationTafsirError(
                    "Quran Foundation Tafsir request failed"
                ) from error

        tafsir = payload.get("tafsir") if isinstance(payload, dict) else None
        if not isinstance(tafsir, dict):
            raise QuranFoundationTafsirError("Quran Foundation Tafsir response is invalid")
        response_resource_id = tafsir.get("resource_id")
        response_text = tafsir.get("text")
        verses = tafsir.get("verses")
        if (
            response_resource_id != resource_id
            or not isinstance(verses, dict)
            or verse_key not in verses
            or not isinstance(response_text, str)
        ):
            raise QuranFoundationTafsirError(
                "Quran Foundation returned a mismatched Tafsir passage"
            )
        plain_text = _plain_text(response_text)
        if not plain_text:
            raise QuranFoundationTafsirError("Quran Foundation returned an empty Tafsir passage")
        return QuranFoundationTafsir(
            resource_id=resource_id,
            resource_name=str(tafsir.get("resource_name") or f"Tafsir resource {resource_id}"),
            language_name=str(tafsir.get("language_name") or "unknown"),
            slug=str(tafsir.get("slug") or ""),
            verse_key=verse_key,
            text=plain_text,
        )
