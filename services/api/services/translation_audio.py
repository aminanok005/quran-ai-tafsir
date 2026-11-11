"""Generate short audio for allowlisted Quran translations."""

import asyncio
import base64
import hashlib
import json
import logging
import shutil
import time
from collections import OrderedDict
from dataclasses import dataclass
from urllib.parse import urlsplit
from typing import Callable

import httpx
from fastapi import HTTPException
from redis.exceptions import RedisError

from ..config import Settings, settings

logger = logging.getLogger(__name__)

GEMINI_HOST = "generativelanguage.googleapis.com"
QURAN_CLOUD_URL = "https://api.alquran.cloud/v1/surah/{surah}/{edition}"
SUPPORTED_EDITIONS = {
    "th.thai": "th",
    "en.sahih": "en",
    "id.indonesian": "id",
}
SURAH_AYAH_COUNTS = (
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128,
    111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73,
    54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60,
    49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52,
    44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19,
    26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3,
    6, 3, 5, 4, 5, 6,
)

RATE_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if count > tonumber(ARGV[2]) then
    return 0
end
return 1
"""


async def compress_wav_to_mp3(wav: bytes, *, bitrate: str = "48k") -> bytes:
    """Shrink WAV speech to mono MP3; return the original if ffmpeg is unavailable or fails."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return wav
    try:
        process = await asyncio.create_subprocess_exec(
            ffmpeg, "-loglevel", "error", "-i", "pipe:0", "-ac", "1",
            "-c:a", "libmp3lame", "-b:a", bitrate, "-f", "mp3", "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        output, _ = await asyncio.wait_for(process.communicate(wav), timeout=15)
    except (OSError, asyncio.TimeoutError):
        return wav
    if process.returncode != 0 or not output or len(output) >= len(wav):
        return wav
    return output


@dataclass(frozen=True)
class AudioResult:
    audio: bytes
    cached: bool


class AudioCache:
    """Process-local TTL/LRU cache. Audio bytes are never persisted."""

    def __init__(
        self,
        max_entries: int = 128,
        ttl_seconds: int = 300,
        clock: Callable[[], float] = time.monotonic,
        max_bytes: int = 50_000_000,
    ):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self.max_bytes = max_bytes
        self.size_bytes = 0
        self._entries: OrderedDict[str, tuple[float, bytes]] = OrderedDict()

    def _remove_expired(self) -> None:
        now = self.clock()
        expired_keys = [
            key for key, (expires_at, _) in self._entries.items() if expires_at <= now
        ]
        for key in expired_keys:
            _, audio = self._entries.pop(key)
            self.size_bytes -= len(audio)

    @staticmethod
    def _key(
        edition: str,
        surah: int,
        ayah: int,
        source_text: str,
        model: str,
        voice: str,
        speed: float,
    ) -> str:
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        material = "\0".join(
            (edition, str(surah), str(ayah), source_hash, model, voice, str(speed))
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def get(
        self,
        edition: str,
        surah: int,
        ayah: int,
        source_text: str,
        model: str,
        voice: str,
        speed: float,
    ) -> bytes | None:
        self._remove_expired()
        key = self._key(edition, surah, ayah, source_text, model, voice, speed)
        entry = self._entries.get(key)
        if entry is None:
            return None
        _, audio = entry
        self._entries.move_to_end(key)
        return audio

    def set(
        self,
        edition: str,
        surah: int,
        ayah: int,
        source_text: str,
        model: str,
        voice: str,
        speed: float,
        audio: bytes,
    ) -> None:
        self._remove_expired()
        key = self._key(edition, surah, ayah, source_text, model, voice, speed)
        previous = self._entries.pop(key, None)
        if previous is not None:
            self.size_bytes -= len(previous[1])
        if len(audio) > self.max_bytes:
            return
        self._entries[key] = (self.clock() + self.ttl_seconds, audio)
        self.size_bytes += len(audio)
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_entries or self.size_bytes > self.max_bytes:
            _, (_, evicted_audio) = self._entries.popitem(last=False)
            self.size_bytes -= len(evicted_audio)


class TranslationAudioService:
    def __init__(
        self,
        settings: Settings = settings,
        redis_client=None,
        http_client: httpx.AsyncClient | None = None,
        cache: AudioCache | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.settings = settings
        self._clock = clock
        self._model_cooldowns: dict[str, float] = {}
        self.redis_client = redis_client
        self.http_client = http_client or httpx.AsyncClient()
        self._source_cache: dict[tuple[int, str], tuple[float, dict[int, str]]] = {}
        self.cache = cache or AudioCache(
            ttl_seconds=settings.tts_cache_ttl_seconds,
            max_bytes=settings.tts_cache_max_bytes,
        )

    def _configuration(self) -> tuple[list[str], list[str]]:
        cfg = self.settings
        if not (
            cfg.tts_enabled
            and cfg.tts_api_key
            and cfg.tts_model
            and cfg.tts_api_base_url
        ):
            raise HTTPException(status_code=503, detail="Translation audio is unavailable")

        editions = [
            edition
            for edition in cfg.tts_allowed_editions
            if edition in SUPPORTED_EDITIONS and SUPPORTED_EDITIONS[edition] in cfg.tts_voice_map
        ]
        if not editions:
            raise HTTPException(status_code=503, detail="Translation audio is unavailable")
        languages = list(dict.fromkeys(SUPPORTED_EDITIONS[edition] for edition in editions))
        return editions, languages

    def capabilities(self) -> dict[str, object]:
        try:
            editions, languages = self._configuration()
        except HTTPException:
            return {"available": False, "supported_languages": [], "enabled_editions": []}
        return {
            "available": True,
            "supported_languages": languages,
            "enabled_editions": editions,
        }

    def _validate_request(self, surah: int, ayah: int, edition: str, speed: float) -> str:
        enabled_editions, _ = self._configuration()
        if (
            not isinstance(surah, int)
            or isinstance(surah, bool)
            or not 1 <= surah <= len(SURAH_AYAH_COUNTS)
            or not isinstance(ayah, int)
            or isinstance(ayah, bool)
            or not 1 <= ayah <= SURAH_AYAH_COUNTS[surah - 1]
        ):
            raise HTTPException(status_code=422, detail="Invalid surah or ayah number")
        if edition not in SUPPORTED_EDITIONS or edition not in enabled_editions:
            raise HTTPException(status_code=422, detail="Unsupported translation edition")
        if (
            isinstance(speed, bool)
            or not isinstance(speed, (int, float))
            or not 0.25 <= speed <= 4.0
        ):
            raise HTTPException(status_code=422, detail="Invalid audio speed")
        if not self.settings.tts_voice_map.get(SUPPORTED_EDITIONS[edition]):
            raise HTTPException(status_code=503, detail="Translation audio is unavailable")
        return self.settings.tts_voice_map[SUPPORTED_EDITIONS[edition]]

    async def _allow_request(self, client_ip: str) -> None:
        if self.redis_client is None:
            raise HTTPException(
                status_code=503,
                detail="Translation audio is temporarily unavailable",
            )
        hashed_ip = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
        key = f"translation-audio:rate:{hashed_ip}"
        try:
            allowed = await self.redis_client.eval(
                RATE_LIMIT_SCRIPT,
                1,
                key,
                60,
                self.settings.tts_rate_limit_per_minute,
            )
        except RedisError as error:
            logger.warning("Translation audio rate limiter unavailable (%s)", type(error).__name__)
            raise HTTPException(
                status_code=503,
                detail="Translation audio is temporarily unavailable",
            ) from error
        if not allowed:
            raise HTTPException(status_code=429, detail="Translation audio request limit reached")

    async def _resolve_translation(self, surah: int, ayah: int, edition: str) -> str:
        cached = self._source_cache.get((surah, edition))
        if cached is not None and cached[0] > time.monotonic():
            return self._pick_ayah(cached[1], ayah)
        self._source_cache.pop((surah, edition), None)
        url = QURAN_CLOUD_URL.format(surah=surah, edition=edition)
        deadline = asyncio.timeout(self.settings.tts_timeout_seconds)

        async def fetch_source():
            async with self.http_client.stream(
                "GET",
                url,
                timeout=self.settings.tts_timeout_seconds,
            ) as response:
                response.raise_for_status()
                length = response.headers.get("content-length")
                if length is not None:
                    length = length.strip()
                    if not length or not length.isascii() or not length.isdigit():
                        raise HTTPException(
                            status_code=502,
                            detail="Invalid translation source response",
                        )
                    if int(length) > self.settings.tts_max_source_bytes:
                        raise HTTPException(
                            status_code=502,
                            detail="Translation source response is too large",
                        )
                chunks = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > self.settings.tts_max_source_bytes:
                        raise HTTPException(
                            status_code=502,
                            detail="Translation source response is too large",
                        )
                    chunks.append(chunk)
            return json.loads(b"".join(chunks))

        try:
            async with deadline:
                payload = await fetch_source()
        except HTTPException:
            raise
        except httpx.TimeoutException as error:
            logger.warning("Quran Cloud translation request timed out")
            raise HTTPException(status_code=504, detail="Translation source timed out") from error
        except TimeoutError as error:
            if not deadline.expired():
                raise
            logger.warning("Quran Cloud translation request timed out")
            raise HTTPException(status_code=504, detail="Translation source timed out") from error
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("Quran Cloud translation request failed (%s)", type(error).__name__)
            raise HTTPException(
                status_code=502,
                detail="Could not load the translation source",
            ) from error

        data = payload.get("data") if isinstance(payload, dict) else None
        edition_data = data.get("edition") if isinstance(data, dict) else None
        ayahs = data.get("ayahs") if isinstance(data, dict) else None
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("number"), int)
            or isinstance(data.get("number"), bool)
            or data.get("number") != surah
            or not isinstance(edition_data, dict)
            or edition_data.get("identifier") != edition
            or not isinstance(ayahs, list)
        ):
            raise HTTPException(status_code=502, detail="Invalid translation source response")
        by_ayah: dict[int, str] = {}
        for item in ayahs:
            number = item.get("numberInSurah") if isinstance(item, dict) else None
            text = item.get("text") if isinstance(item, dict) else None
            if isinstance(number, int) and not isinstance(number, bool) and number not in by_ayah:
                by_ayah[number] = text if isinstance(text, str) else ""
        if len(self._source_cache) >= 64:
            self._source_cache.clear()
        self._source_cache[(surah, edition)] = (time.monotonic() + 3600, by_ayah)
        return self._pick_ayah(by_ayah, ayah)

    def _pick_ayah(self, by_ayah: dict[int, str], ayah: int) -> str:
        text = by_ayah.get(ayah)
        if not text or not text.strip() or len(text) > self.settings.tts_max_text_chars:
            raise HTTPException(status_code=502, detail="Invalid translation source response")
        return text

    @staticmethod
    def _is_wav_audio(audio: bytes) -> bool:
        return len(audio) >= 12 and audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"

    def _is_gemini_native(self) -> bool:
        return urlsplit(self.settings.tts_api_base_url or "").hostname == GEMINI_HOST

    def _model_chain(self) -> list[str]:
        cfg = self.settings
        now = self._clock()
        chain = [m for m in dict.fromkeys([cfg.tts_model, *cfg.tts_fallback_models]) if m]
        ready = [m for m in chain if self._model_cooldowns.get(m, 0.0) <= now]
        # Every model cooling down: still try them in order rather than fail without a call.
        return ready or chain

    async def _request_gemini_audio(self, text: str, voice: str, model: str) -> bytes:
        cfg = self.settings
        endpoint = f"{cfg.tts_api_base_url.rstrip('/')}/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
            },
        }
        try:
            response = await self.http_client.post(
                endpoint,
                json=payload,
                headers={"x-goog-api-key": cfg.tts_api_key or ""},
                timeout=cfg.tts_timeout_seconds,
            )
            if response.status_code < 200 or response.status_code >= 300:
                logger.warning("Gemini TTS returned HTTP %s", response.status_code)
                if response.status_code == 429:
                    raise HTTPException(
                        status_code=429,
                        detail="Audio provider quota or rate limit reached; try again later",
                    )
                raise HTTPException(status_code=502, detail="Audio provider request failed")
            parts = response.json()["candidates"][0]["content"]["parts"]
            inline = next((part["inlineData"] for part in parts if "inlineData" in part), None)
            audio = base64.b64decode(inline["data"], validate=True) if inline else b""
        except HTTPException:
            raise
        except httpx.TimeoutException as error:
            raise HTTPException(status_code=504, detail="Audio generation timed out") from error
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            logger.warning("Gemini TTS request failed (%s)", type(error).__name__)
            raise HTTPException(status_code=502, detail="Could not generate audio") from error
        if len(audio) > cfg.tts_max_audio_bytes or not self._is_wav_audio(audio):
            raise HTTPException(status_code=502, detail="Audio provider returned invalid audio")
        return await compress_wav_to_mp3(audio)

    @staticmethod
    def _is_mpeg_audio(audio: bytes) -> bool:
        return len(audio) >= 4 and (
            audio.startswith(b"ID3")
            or (audio[0] == 0xFF and audio[1] & 0xE0 == 0xE0)
        )

    async def _request_gemini_with_fallback(self, text: str, voice: str) -> bytes:
        last: HTTPException | None = None
        for model in self._model_chain():
            try:
                return await self._request_gemini_audio(text, voice, model)
            except HTTPException as error:
                if error.status_code not in {429, 502, 503, 504}:
                    raise
                self._model_cooldowns[model] = self._clock() + self.settings.tts_model_cooldown_seconds
                logger.warning("TTS model %s unavailable (HTTP %s); trying next", model, error.status_code)
                last = error
        assert last is not None
        raise last

    async def _request_audio(self, text: str, voice: str, speed: float) -> bytes:
        deadline = asyncio.timeout(self.settings.tts_timeout_seconds)
        try:
            async with deadline:
                if self._is_gemini_native():
                    return await self._request_gemini_with_fallback(text, voice)
                return await self._request_audio_stream(text, voice, speed)
        except TimeoutError as error:
            if not deadline.expired():
                raise
            logger.warning("Translation audio provider timed out")
            raise HTTPException(status_code=504, detail="Audio generation timed out") from error

    async def _request_audio_stream(self, text: str, voice: str, speed: float) -> bytes:
        cfg = self.settings
        endpoint = f"{cfg.tts_api_base_url.rstrip('/')}/audio/speech"
        payload = {
            "model": cfg.tts_model,
            "input": text,
            "voice": voice,
            "response_format": "mp3",
            "speed": speed,
        }
        try:
            async with self.http_client.stream(
                "POST",
                endpoint,
                json=payload,
                headers={"Authorization": f"Bearer {cfg.tts_api_key}"},
                timeout=cfg.tts_timeout_seconds,
            ) as response:
                if response.status_code < 200 or response.status_code >= 300:
                    logger.warning(
                        "Translation audio provider returned HTTP %s",
                        response.status_code,
                    )
                    raise HTTPException(
                        status_code=502,
                        detail="Audio provider request failed",
                    )
                content_type = (
                    response.headers.get("content-type", "")
                    .split(";", 1)[0]
                    .strip()
                    .lower()
                )
                if content_type != "audio/mpeg":
                    raise HTTPException(
                        status_code=502,
                        detail="Audio provider returned an invalid format",
                    )
                length = response.headers.get("content-length")
                if length and int(length) > cfg.tts_max_audio_bytes:
                    raise HTTPException(
                        status_code=502,
                        detail="Audio provider response is too large",
                    )
                chunks = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > cfg.tts_max_audio_bytes:
                        raise HTTPException(
                            status_code=502,
                            detail="Audio provider response is too large",
                        )
                    chunks.append(chunk)
                audio = b"".join(chunks)
        except HTTPException:
            raise
        except httpx.TimeoutException as error:
            logger.warning("Translation audio provider timed out")
            raise HTTPException(status_code=504, detail="Audio generation timed out") from error
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("Translation audio provider request failed (%s)", type(error).__name__)
            raise HTTPException(status_code=502, detail="Could not generate audio") from error

        if not self._is_mpeg_audio(audio):
            raise HTTPException(status_code=502, detail="Audio provider returned invalid audio")
        return audio

    async def synthesize(
        self,
        surah: int,
        ayah: int,
        edition: str,
        speed: float,
        client_ip: str,
    ) -> AudioResult:
        voice = self._validate_request(surah, ayah, edition, speed)
        await self._allow_request(client_ip)
        source_text = await self._resolve_translation(surah, ayah, edition)
        model = self.settings.tts_model
        audio = self.cache.get(edition, surah, ayah, source_text, model, voice, speed)
        if audio is not None:
            return AudioResult(audio=audio, cached=True)
        audio = await self._request_audio(source_text, voice, speed)
        self.cache.set(edition, surah, ayah, source_text, model, voice, speed, audio)
        return AudioResult(audio=audio, cached=False)

    async def aclose(self) -> None:
        close_redis = getattr(self.redis_client, "aclose", None)
        try:
            await self.http_client.aclose()
        except BaseException as http_error:
            try:
                if close_redis:
                    await close_redis()
            except BaseException as redis_error:
                cancellation = next(
                    (
                        error
                        for error in (http_error, redis_error)
                        if isinstance(error, asyncio.CancelledError)
                    ),
                    None,
                )
                if cancellation is not None:
                    secondary_client = (
                        "Redis" if cancellation is http_error else "HTTP"
                    )
                    cancellation.add_note(
                        f"{secondary_client} client cleanup also failed"
                    )
                    raise cancellation from None
                raise BaseExceptionGroup(
                    "Translation audio resource cleanup failed",
                    [http_error, redis_error],
                )
            raise
        else:
            if close_redis:
                await close_redis()
