"""Gemini adapter over Google's OpenAI-compatible chat endpoint (server-side only)."""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional

import httpx

from ..config import Settings, settings as default_settings

logger = logging.getLogger(__name__)


class GeminiErrorKind(str, Enum):
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    SERVER = "server"
    BAD_REQUEST = "bad_request"
    MALFORMED = "malformed_response"
    TRUNCATED = "truncated"


class GeminiError(RuntimeError):
    """Generic, secret-free provider error."""

    def __init__(self, kind: GeminiErrorKind, status_code: Optional[int] = None):
        self.kind = kind
        self.status_code = status_code
        super().__init__(f"Gemini request failed ({kind.value})")

    @property
    def retryable(self) -> bool:
        return self.kind in {GeminiErrorKind.RATE_LIMIT, GeminiErrorKind.TIMEOUT, GeminiErrorKind.SERVER}


def classify_status(status: int) -> GeminiErrorKind:
    if status in (401, 403):
        return GeminiErrorKind.AUTHENTICATION
    if status == 429:
        return GeminiErrorKind.RATE_LIMIT
    if status >= 500:
        return GeminiErrorKind.SERVER
    return GeminiErrorKind.BAD_REQUEST


@dataclass(frozen=True)
class Usage:
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: Optional[float] = None


@dataclass(frozen=True)
class GeminiResult:
    text: str
    usage: Usage
    data: Optional[Any] = None


def _cost(prices: Mapping[str, Mapping[str, float]], model: str, prompt: int, completion: int) -> Optional[float]:
    price = prices.get(model)
    if not price:
        return None
    return (prompt * price.get("input_per_million", 0.0) + completion * price.get("output_per_million", 0.0)) / 1_000_000


class GeminiProvider:
    def __init__(self, config: Settings = default_settings, client: Optional[httpx.AsyncClient] = None):
        self.config = config
        self._client = client
        self._semaphore = asyncio.Semaphore(config.gemini_max_concurrency)

    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        json_output: bool = False,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> GeminiResult:
        key = self.config.gemini_api_key
        if not key or not model:
            raise GeminiError(GeminiErrorKind.CONFIGURATION)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or self.config.llm_max_tokens,
            "temperature": self.config.llm_temperature if temperature is None else temperature,
        }
        if json_output and self.config.gemini_json_mode:
            payload["response_format"] = {"type": "json_object"}

        attempts = self.config.gemini_max_retries + 1
        last: Optional[GeminiError] = None
        for attempt in range(attempts):
            try:
                async with self._semaphore:
                    body = await self._post(payload, key)
                return self._parse(model, body, json_output)
            except GeminiError as error:
                last = error
                if not error.retryable or attempt == attempts - 1:
                    break
                delay = min(8.0, 0.5 * 2**attempt) + random.uniform(0, 0.25)
                logger.warning("Gemini %s; retrying (%s/%s)", error.kind.value, attempt + 1, attempts - 1)
                await asyncio.sleep(delay)
        assert last is not None
        raise last

    async def _post(self, payload: dict[str, Any], key: str) -> Any:
        url = f"{self.config.gemini_api_base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {key}"}
        try:
            if self._client is not None:
                response = await self._client.post(url, json=payload, headers=headers, timeout=self.config.gemini_timeout_seconds)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, headers=headers, timeout=self.config.gemini_timeout_seconds)
        except httpx.TimeoutException as error:
            raise GeminiError(GeminiErrorKind.TIMEOUT) from error
        except httpx.HTTPError as error:
            raise GeminiError(GeminiErrorKind.SERVER) from error
        if response.status_code >= 400:
            logger.warning("Gemini HTTP %s", response.status_code)
            raise GeminiError(classify_status(response.status_code), response.status_code)
        try:
            return response.json()
        except ValueError as error:
            raise GeminiError(GeminiErrorKind.MALFORMED) from error

    def _parse(self, model: str, body: Any, json_output: bool) -> GeminiResult:
        try:
            text = body["choices"][0]["message"].get("content")
        except (KeyError, IndexError, TypeError) as error:
            raise GeminiError(GeminiErrorKind.MALFORMED) from error
        if not isinstance(text, str) or not text.strip():
            finish = body["choices"][0].get("finish_reason") if isinstance(body, dict) else None
            kind = GeminiErrorKind.TRUNCATED if finish == "length" else GeminiErrorKind.MALFORMED
            raise GeminiError(kind)
        raw = body.get("usage") if isinstance(body, dict) else None
        raw = raw if isinstance(raw, dict) else {}
        prompt = int(raw.get("prompt_tokens") or 0)
        completion = int(raw.get("completion_tokens") or 0)
        usage = Usage(model, prompt, completion, _cost(self.config.gemini_model_prices, model, prompt, completion))
        data = None
        if json_output:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                cleaned = cleaned[4:] if cleaned.lower().startswith("json") else cleaned
            try:
                data = json.loads(cleaned)
            except ValueError as error:
                raise GeminiError(GeminiErrorKind.MALFORMED) from error
        return GeminiResult(text, usage, data)
