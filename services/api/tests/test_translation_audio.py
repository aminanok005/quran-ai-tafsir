import asyncio
import hashlib
import json
import os
import threading
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from starlette.requests import Request

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from services.api.app import app
from services.api.config import Settings
from services.api.routers import translation_audio as translation_audio_router
from services.api.routers.translation_audio import get_translation_audio_service
from services.api.services.translation_audio import AudioCache, TranslationAudioService

HTTPX_ASYNC_CLIENT = httpx.AsyncClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


SOURCE_TEXT = "คำแปลต้นฉบับอย่างถูกต้อง"
AUDIO_BYTES = b"\xff\xfb\x90\x64" + b"\x00" * 24
SOURCE_URL = "https://api.alquran.cloud/v1/surah/1/th.thai"


def enabled_settings(**overrides):
    values = {
        "DATABASE_URL": "postgresql+psycopg://postgres@localhost/quran_ai_test",
        "TTS_ENABLED": True,
        "TTS_API_KEY": "tts-secret",
        "TTS_MODEL": "speech-model",
        "TTS_API_BASE_URL": "https://tts.example.test/v1",
        "TTS_ALLOWED_EDITIONS": ["th.thai", "en.sahih", "id.indonesian"],
        "TTS_VOICE_MAP": {"th": "thai-voice", "en": "english-voice", "id": "indonesian-voice"},
        **overrides,
    }
    return Settings(_env_file=None, **values)


class FakeRedis:
    def __init__(self, clock=None):
        self.values = {}
        self.expiries = {}
        self.calls = []
        self.lock = threading.Lock()
        self.error = None
        self.clock = clock or (lambda: 0.0)

    async def eval(self, script, numkeys, key, window, limit):
        if self.error:
            raise self.error
        self.calls.append((script, numkeys, key, window, limit))
        assert numkeys == 1
        with self.lock:
            now = self.clock()
            if self.expiries.get(key, float("inf")) <= now:
                self.values.pop(key, None)
                self.expiries.pop(key, None)
            self.values[key] = self.values.get(key, 0) + 1
            if self.values[key] == 1:
                self.expiries[key] = now + int(window)
            return int(self.values[key] <= int(limit))


def mock_http(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def valid_source_response(text=SOURCE_TEXT, *, surah=1, ayah=1, edition="th.thai"):
    return {
        "data": {
            "number": surah,
            "edition": {"identifier": edition},
            "ayahs": [{"numberInSurah": ayah, "text": text}],
        }
    }


def provider_success(request):
    return httpx.Response(
        200,
        headers={"content-type": "audio/mpeg"},
        content=AUDIO_BYTES,
    )


def service_for(
    source_handler=None,
    provider_handler=None,
    *,
    settings=None,
    redis=None,
    cache=None,
):
    async def default_handler(request):
        if str(request.url) == SOURCE_URL:
            return httpx.Response(200, json=valid_source_response())
        return provider_success(request)

    async def handler(request):
        if source_handler and str(request.url).startswith("https://api.alquran.cloud/"):
            return await source_handler(request)
        if provider_handler:
            return await provider_handler(request)
        return await default_handler(request)

    return TranslationAudioService(
        settings=settings or enabled_settings(),
        redis_client=redis or FakeRedis(),
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        cache=cache,
    )


@pytest.mark.anyio
async def test_resolves_fixed_quran_cloud_endpoint_and_passes_exact_translation_to_tts():
    seen = []

    async def handler(request):
        seen.append(request)
        if str(request.url) == SOURCE_URL:
            return httpx.Response(200, json=valid_source_response())
        payload = json.loads(request.content)
        assert payload["input"] == SOURCE_TEXT
        assert payload["voice"] == "thai-voice"
        assert payload["speed"] == 1.0
        assert payload["model"] == "speech-model"
        assert payload["response_format"] == "mp3"
        assert request.headers["authorization"] == expected_authorization
        assert request.headers["authorization"] != chr(42) * 6
        return provider_success(request)

    service = service_for(provider_handler=handler)
    expected_authorization = f"Bearer {service.settings.tts_api_key}"
    result = await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert result.audio == AUDIO_BYTES
    assert result.cached is False
    assert str(seen[0].url) == SOURCE_URL
    assert str(seen[1].url) == "https://tts.example.test/v1/audio/speech"
    await service.aclose()


@pytest.mark.anyio
async def test_rejects_disabled_or_incomplete_tts_configuration_before_external_calls():
    source = AsyncMock()
    provider = AsyncMock()
    for settings in (
        enabled_settings(TTS_ENABLED=False),
        enabled_settings(TTS_API_KEY=None),
    ):
        service = service_for(
            source_handler=source,
            provider_handler=provider,
            settings=settings,
        )
        with pytest.raises(Exception) as error:
            await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
        assert getattr(error.value, "status_code", None) == 503
        await service.aclose()
    source.assert_not_awaited()
    provider.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("surah", "ayah", "edition", "speed"),
    [
        (0, 1, "th.thai", 1.0),
        (115, 1, "th.thai", 1.0),
        (1, 0, "th.thai", 1.0),
        (1, 8, "th.thai", 1.0),
        (1, 287, "th.thai", 1.0),
        (1, 1, "ar.mishary", 1.0),
        (1, 1, "fr.french", 1.0),
        (1, 1, "id.indonesian", 1.0),
        (1, 1, "th.thai", 0.1),
        (1, 1, "th.thai", 4.1),
    ],
)
async def test_rejects_invalid_verse_edition_and_speed_before_source_or_provider(
    surah, ayah, edition, speed
):
    source = AsyncMock()
    provider = AsyncMock()
    service = service_for(
        source_handler=source,
        provider_handler=provider,
        settings=enabled_settings(TTS_ALLOWED_EDITIONS=["th.thai"]),
    )
    with pytest.raises(Exception) as error:
        await service.synthesize(surah, ayah, edition, speed, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 422
    source.assert_not_awaited()
    provider.assert_not_awaited()
    await service.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {"data": {"number": 2, "edition": {"identifier": "th.thai"}, "ayahs": []}},
        {"data": {"number": 1, "edition": {"identifier": "en.sahih"}, "ayahs": []}},
        {"data": {"number": 1, "edition": {"identifier": "th.thai"}, "ayahs": []}},
        {
            "data": {
                "number": 1,
                "edition": {"identifier": "th.thai"},
                "ayahs": [{"numberInSurah": 2, "text": "wrong verse"}],
            }
        },
        {
            "data": {
                "number": 1,
                "edition": {"identifier": "th.thai"},
                "ayahs": [{"numberInSurah": 1, "text": " " * 3}],
            }
        },
    ],
)
async def test_rejects_missing_or_mismatched_quran_cloud_verse(payload):
    async def handler(request):
        if str(request.url).startswith("https://api.alquran.cloud/"):
            return httpx.Response(200, json=payload)
        pytest.fail("provider must not be called for an invalid source response")

    service = service_for(source_handler=handler)
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) in {502, 503}
    await service.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {
            "data": {
                "number": True,
                "edition": {"identifier": "th.thai"},
                "ayahs": [{"numberInSurah": 1, "text": SOURCE_TEXT}],
            }
        },
        {
            "data": {
                "number": 1,
                "edition": {"identifier": "th.thai"},
                "ayahs": [{"numberInSurah": True, "text": SOURCE_TEXT}],
            }
        },
        {
            "data": {
                "number": "1",
                "edition": {"identifier": "th.thai"},
                "ayahs": [{"numberInSurah": 1, "text": SOURCE_TEXT}],
            }
        },
        {
            "data": {
                "number": 1,
                "edition": {"identifier": "th.thai"},
                "ayahs": [{"numberInSurah": "1", "text": SOURCE_TEXT}],
            }
        },
    ],
)
async def test_rejects_non_integer_quran_cloud_identifiers_before_provider_call(payload):
    provider = AsyncMock(return_value=provider_success(None))

    async def source_handler(request):
        return httpx.Response(200, json=payload)

    service = service_for(source_handler=source_handler, provider_handler=provider)
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 502
    provider.assert_not_awaited()
    await service.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("provider_response", "expected_status"),
    [
        (httpx.Response(503, text="provider-secret-detail"), 502),
        (httpx.Response(200, headers={"content-type": "application/json"}, content=b"secret"), 502),
        (httpx.Response(200, headers={"content-type": "audio/mpeg"}, content=b"not-mpeg"), 502),
        (
            httpx.Response(200, headers={"content-type": "audio/mpeg"}, content=AUDIO_BYTES * 10),
            502,
        ),
    ],
)
async def test_provider_status_content_type_and_audio_validation_are_safe(
    provider_response, expected_status, caplog
):
    async def handler(request):
        if str(request.url).startswith("https://api.alquran.cloud/"):
            return httpx.Response(200, json=valid_source_response())
        return provider_response

    service = service_for(
        provider_handler=handler,
        settings=enabled_settings(TTS_MAX_AUDIO_BYTES=len(AUDIO_BYTES)),
    )
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == expected_status
    assert "provider-secret-detail" not in str(error.value)
    assert "provider-secret-detail" not in caplog.text
    await service.aclose()


@pytest.mark.anyio
async def test_provider_timeout_returns_safe_gateway_timeout():
    async def handler(request):
        if str(request.url).startswith("https://api.alquran.cloud/"):
            return httpx.Response(200, json=valid_source_response())
        raise httpx.ReadTimeout("secret provider detail", request=request)

    service = service_for(provider_handler=handler)
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 504
    assert "secret provider detail" not in str(error.value)
    await service.aclose()


@pytest.mark.anyio
async def test_slow_drip_quran_cloud_source_has_total_deadline_and_skips_provider():
    source_body = json.dumps(valid_source_response()).encode()
    provider = AsyncMock(return_value=provider_success(None))

    class SlowSourceStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for chunk in (source_body[:20], source_body[20:40], source_body[40:]):
                await asyncio.sleep(0.04)
                yield chunk

        async def aclose(self):
            pass

    async def source_handler(request):
        return httpx.Response(200, stream=SlowSourceStream())

    service = service_for(
        source_handler=source_handler,
        provider_handler=provider,
        settings=enabled_settings(TTS_TIMEOUT_SECONDS=0.08),
    )
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 504
    assert getattr(error.value, "detail", None) == "Translation source timed out"
    provider.assert_not_awaited()
    await service.aclose()


@pytest.mark.anyio
async def test_slow_drip_provider_stream_has_total_deadline():
    class SlowProviderStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for chunk in (AUDIO_BYTES[:2], AUDIO_BYTES[2:4], AUDIO_BYTES[4:]):
                await asyncio.sleep(0.04)
                yield chunk

        async def aclose(self):
            pass

    async def provider_handler(request):
        if str(request.url).startswith("https://api.alquran.cloud/"):
            return httpx.Response(200, json=valid_source_response())
        return httpx.Response(
            200,
            headers={"content-type": "audio/mpeg"},
            stream=SlowProviderStream(),
        )

    service = service_for(
        provider_handler=provider_handler,
        settings=enabled_settings(TTS_TIMEOUT_SECONDS=0.08),
    )
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 504
    assert getattr(error.value, "detail", None) == "Audio generation timed out"
    await service.aclose()


@pytest.mark.anyio
async def test_quran_cloud_source_failures_return_safe_errors():
    async def handler(request):
        return httpx.Response(503, text="source-secret-detail")

    service = service_for(source_handler=handler)
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) in {502, 503}
    assert "source-secret-detail" not in str(error.value)
    await service.aclose()


@pytest.mark.anyio
async def test_rejects_source_text_over_configured_limit_before_calling_provider():
    provider = AsyncMock()

    async def handler(request):
        if str(request.url).startswith("https://api.alquran.cloud/"):
            return httpx.Response(200, json=valid_source_response(text="too long"))
        return await provider(request)

    service = service_for(
        provider_handler=handler,
        settings=enabled_settings(TTS_MAX_TEXT_CHARS=5),
    )
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 502
    provider.assert_not_awaited()
    await service.aclose()


@pytest.mark.anyio
async def test_rejects_oversized_streamed_source_before_json_parsing_or_provider_call(monkeypatch):
    source_body = json.dumps(valid_source_response()).encode() + b" " * 256
    provider = AsyncMock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "audio/mpeg"},
            content=AUDIO_BYTES,
        )
    )
    parsed_responses = []
    original_json = httpx.Response.json

    def tracked_json(response, **kwargs):
        parsed_responses.append(response)
        return original_json(response, **kwargs)

    monkeypatch.setattr(httpx.Response, "json", tracked_json)

    class SourceStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield source_body

        async def aclose(self):
            pass

    async def handler(request):
        if str(request.url).startswith("https://api.alquran.cloud/"):
            return httpx.Response(200, stream=SourceStream())
        return await provider(request)

    service = service_for(
        source_handler=handler,
        provider_handler=provider,
        settings=enabled_settings(TTS_MAX_SOURCE_BYTES=64),
    )
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 502
    assert parsed_responses == []
    provider.assert_not_awaited()
    await service.aclose()


@pytest.mark.anyio
async def test_rejects_source_content_length_over_limit_before_reading_or_calling_provider():
    provider = AsyncMock()
    stream_started = False
    source_body = json.dumps(valid_source_response(), ensure_ascii=False).encode()
    assert len(source_body) < 256

    class SourceStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            nonlocal stream_started
            stream_started = True
            yield source_body

        async def aclose(self):
            pass

    async def handler(request):
        if str(request.url).startswith("https://api.alquran.cloud/"):
            return httpx.Response(
                200,
                headers={"content-length": "257"},
                stream=SourceStream(),
            )
        return await provider(request)

    service = service_for(
        source_handler=handler,
        provider_handler=provider,
        settings=enabled_settings(TTS_MAX_SOURCE_BYTES=256),
    )
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 502
    assert getattr(error.value, "detail", None) == "Translation source response is too large"
    assert stream_started is False
    provider.assert_not_awaited()
    await service.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "headers",
    [
        {"content-length": "not-a-number"},
        {"content-length": "-1"},
    ],
)
async def test_invalid_source_content_length_returns_safe_upstream_error(headers):
    async def handler(request):
        return httpx.Response(200, headers=headers, content=b"{}")

    service = service_for(
        source_handler=handler,
        settings=enabled_settings(TTS_MAX_SOURCE_BYTES=64),
    )
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 502
    await service.aclose()


@pytest.mark.anyio
async def test_redis_unavailable_fails_closed_before_provider_and_does_not_log_raw_ip(caplog):
    redis = FakeRedis()
    redis.error = RedisError("redis-secret-detail")
    provider = AsyncMock()
    service = service_for(redis=redis, provider_handler=provider)
    with pytest.raises(Exception) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert getattr(error.value, "status_code", None) == 503
    assert "redis-secret-detail" not in str(error.value)
    assert "redis-secret-detail" not in caplog.text
    assert "192.0.2.3" not in caplog.text
    provider.assert_not_awaited()
    assert all("192.0.2.3" not in key for key in redis.values)
    await service.aclose()


@pytest.mark.anyio
async def test_unexpected_rate_limiter_errors_are_not_hidden_as_redis_unavailability():
    redis = FakeRedis()
    redis.error = RuntimeError("programming error")
    service = service_for(redis=redis)
    with pytest.raises(RuntimeError, match="programming error"):
        await service._allow_request("192.0.2.3")
    await service.aclose()


@pytest.mark.anyio
async def test_rate_limit_key_expiry_starts_a_new_window():
    now = [100.0]
    redis = FakeRedis(clock=lambda: now[0])
    service = service_for(redis=redis, settings=enabled_settings(TTS_RATE_LIMIT_PER_MINUTE=1))

    await service._allow_request("192.0.2.3")
    with pytest.raises(Exception) as error:
        await service._allow_request("192.0.2.3")
    assert getattr(error.value, "status_code", None) == 429

    now[0] += 60
    await service._allow_request("192.0.2.3")

    key = next(iter(redis.values))
    assert redis.values[key] == 1
    assert redis.expiries[key] == now[0] + 60
    assert len(redis.calls) == 3
    await service.aclose()


@pytest.mark.anyio
async def test_rate_limit_uses_atomic_expiring_hashed_client_key():
    redis = FakeRedis()
    service = service_for(redis=redis, settings=enabled_settings(TTS_RATE_LIMIT_PER_MINUTE=3))
    outcomes = await asyncio.gather(
        *(
            service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
            for _ in range(8)
        ),
        return_exceptions=True,
    )
    assert sum(not isinstance(item, Exception) for item in outcomes) == 3
    assert len(redis.values) == 1
    key = next(iter(redis.values))
    assert "192.0.2.3" not in key
    assert redis.expiries[key] == 60
    assert redis.values[key] == 8
    assert len(redis.calls) == 8
    script, numkeys, _, window, limit = redis.calls[0]
    assert "INCR" in script and "EXPIRE" in script
    assert numkeys == 1 and window == 60 and limit == 3
    await service.aclose()


def test_audio_cache_keys_every_output_input_and_expires_and_evicts_lru():
    now = [100.0]
    cache = AudioCache(max_entries=2, ttl_seconds=10, clock=lambda: now[0])
    base = ("th.thai", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)
    cache.set(*base, AUDIO_BYTES)
    assert cache.get(*base) == AUDIO_BYTES
    for changed in (
        ("en.sahih", 1, 1, SOURCE_TEXT, "model", "voice", 1.0),
        ("th.thai", 1, 1, SOURCE_TEXT + "!", "model", "voice", 1.0),
        ("th.thai", 1, 1, SOURCE_TEXT, "model-2", "voice", 1.0),
        ("th.thai", 1, 1, SOURCE_TEXT, "model", "voice-2", 1.0),
        ("th.thai", 1, 1, SOURCE_TEXT, "model", "voice", 1.1),
        ("th.thai", 2, 1, SOURCE_TEXT, "model", "voice", 1.0),
        ("th.thai", 1, 2, SOURCE_TEXT, "model", "voice", 1.0),
    ):
        assert cache.get(*changed) is None
    second = ("en.sahih", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)
    third = ("id.indonesian", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)
    cache.set(*second, AUDIO_BYTES + b"2")
    cache.get(*base)
    cache.set(*third, AUDIO_BYTES + b"3")
    assert cache.get(*second) is None
    assert cache.get(*base) == AUDIO_BYTES
    now[0] += 11
    assert cache.get(*base) is None


def test_audio_cache_evicts_least_recently_used_entries_to_stay_within_byte_budget():
    cache = AudioCache(max_entries=10, max_bytes=10, ttl_seconds=60)
    first = ("th.thai", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)
    second = ("en.sahih", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)
    third = ("id.indonesian", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)

    cache.set(*first, b"aaaa")
    cache.set(*second, b"bbbb")
    assert cache.get(*second) == b"bbbb"
    cache.set(*third, b"cccc")

    assert cache.get(*first) is None
    assert cache.get(*second) == b"bbbb"
    assert cache.get(*third) == b"cccc"


def test_audio_cache_skips_entries_larger_than_byte_budget():
    cache = AudioCache(max_entries=2, max_bytes=4, ttl_seconds=60)
    oversized = ("th.thai", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)
    normal = ("en.sahih", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)

    cache.set(*oversized, b"12345")
    assert cache.get(*oversized) is None
    cache.set(*normal, b"1234")
    assert cache.get(*normal) == b"1234"


def test_audio_cache_expired_entries_are_removed_during_get_and_set_maintenance():
    now = [0.0]
    cache = AudioCache(max_entries=10, max_bytes=10, ttl_seconds=5, clock=lambda: now[0])
    expired = ("th.thai", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)
    live = ("en.sahih", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)
    newer = ("id.indonesian", 1, 1, SOURCE_TEXT, "model", "voice", 1.0)

    cache.set(*expired, b"123456")
    now[0] = 4.0
    cache.set(*live, b"1234")
    now[0] = 6.0
    assert cache.get(*live) == b"1234"
    cache.set(*newer, b"abcdef")

    assert cache.get(*live) == b"1234"
    assert cache.get(*newer) == b"abcdef"


@pytest.mark.anyio
async def test_service_caches_only_validated_successful_audio():
    provider_calls = []

    async def handler(request):
        if str(request.url).startswith("https://api.alquran.cloud/"):
            return httpx.Response(200, json=valid_source_response())
        provider_calls.append(request)
        if len(provider_calls) == 1:
            return httpx.Response(200, headers={"content-type": "audio/mpeg"}, content=b"invalid")
        return provider_success(request)

    cache = AudioCache(max_entries=4, ttl_seconds=60)
    service = service_for(
        provider_handler=handler,
        cache=cache,
        settings=enabled_settings(TTS_MAX_AUDIO_BYTES=1024),
    )
    with pytest.raises(Exception):
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    result = await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    hit = await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert result.cached is False
    assert hit.cached is True
    assert len(provider_calls) == 2
    await service.aclose()


def test_service_configures_audio_cache_byte_budget_from_settings():
    configured = enabled_settings(TTS_CACHE_MAX_BYTES=1234)
    service = service_for(settings=configured)
    assert service.cache.max_bytes == 1234


def test_capabilities_only_expose_availability_languages_and_enabled_editions():
    service = service_for(
        settings=enabled_settings(
            TTS_ALLOWED_EDITIONS=["th.thai", "id.indonesian"],
            TTS_API_KEY="capability-secret",
            TTS_MODEL="private-model",
            TTS_VOICE_MAP={"th": "private-thai-voice", "id": "private-id-voice"},
        )
    )
    capabilities = service.capabilities()
    serialized = json.dumps(capabilities)
    assert capabilities == {
        "available": True,
        "supported_languages": ["th", "id"],
        "enabled_editions": ["th.thai", "id.indonesian"],
    }
    for secret in ("capability-secret", "private-model", "private-thai-voice", "tts.example.test"):
        assert secret not in serialized


def test_routes_mount_capabilities_and_audio_with_mpeg_cache_and_cors_headers():
    service = service_for()
    app.dependency_overrides[get_translation_audio_service] = lambda: service
    try:
        with TestClient(app) as client:
            capabilities = client.get("/api/v1/quran/translation-audio/capabilities")
            audio = client.get(
                "/api/v1/quran/translation-audio/1/1",
                params={"edition": "th.thai", "speed": 1.0},
                headers={
                    "Origin": "http://localhost:3000",
                    "X-Forwarded-For": "203.0.113.99",
                },
            )
    finally:
        app.dependency_overrides.pop(get_translation_audio_service, None)
    assert capabilities.status_code == 200
    assert capabilities.json()["available"] is True
    assert audio.status_code == 200
    assert audio.content == AUDIO_BYTES
    assert audio.headers["content-type"] == "audio/mpeg"
    assert audio.headers["x-audio-cache"] == "miss"
    assert audio.headers["access-control-allow-origin"] == "http://localhost:3000"
    exposed_headers = {
        header.strip().lower()
        for header in audio.headers["access-control-expose-headers"].split(",")
    }
    assert "x-audio-cache" in exposed_headers
    key = next(iter(service.redis_client.values))
    assert key.endswith(hashlib.sha256(b"testclient").hexdigest())
    assert "203.0.113.99" not in key


@pytest.mark.anyio
async def test_translation_audio_service_lifecycle_is_managed_once(monkeypatch):
    http_clients = []
    redis_clients = []
    services = []
    capability_instances = []

    class ManagedClient:
        def __init__(self):
            self.aclose = AsyncMock()

    def create_http_client(*args, **kwargs):
        client = ManagedClient()
        http_clients.append(client)
        return client

    def create_redis_client(*args, **kwargs):
        client = ManagedClient()
        redis_clients.append(client)
        return client

    original_service_class = TranslationAudioService

    def create_service(*args, **kwargs):
        service = original_service_class(*args, **kwargs)
        service.aclose = AsyncMock(wraps=service.aclose)
        services.append(service)
        return service

    def capabilities(service):
        capability_instances.append(service)
        return {"instance": str(id(service))}

    monkeypatch.setattr(translation_audio_router.httpx, "AsyncClient", create_http_client)
    monkeypatch.setattr(translation_audio_router.redis.Redis, "from_url", create_redis_client)
    monkeypatch.setattr(translation_audio_router, "TranslationAudioService", create_service)
    monkeypatch.setattr(original_service_class, "capabilities", capabilities)

    async with app.router.lifespan_context(app):
        service = getattr(app.state, "translation_audio_service", None)
        assert service is not None
        assert services == [service]
        assert len(http_clients) == 1
        assert len(redis_clients) == 1
        assert service.http_client is http_clients[0]
        assert service.redis_client is redis_clients[0]

        async with HTTPX_ASYNC_CLIENT(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            responses = await asyncio.gather(
                *(
                    client.get("/api/v1/quran/translation-audio/capabilities")
                    for _ in range(8)
                )
            )

        assert all(response.status_code == 200 for response in responses)
        assert {response.json()["instance"] for response in responses} == {str(id(service))}
        assert capability_instances == [service] * 8
        assert services == [service]

    service.aclose.assert_awaited_once()
    http_clients[0].aclose.assert_awaited_once()
    redis_clients[0].aclose.assert_awaited_once()


@pytest.mark.anyio
async def test_aclose_attempts_redis_when_http_close_fails():
    http_error = RuntimeError("HTTP close failed")
    http_client = AsyncMock()
    http_client.aclose.side_effect = http_error
    redis_client = AsyncMock()
    service = TranslationAudioService(
        settings=enabled_settings(),
        redis_client=redis_client,
        http_client=http_client,
    )

    with pytest.raises(RuntimeError) as error:
        await service.aclose()

    assert error.value is http_error
    http_client.aclose.assert_awaited_once()
    redis_client.aclose.assert_awaited_once()


@pytest.mark.anyio
async def test_aclose_preserves_cancellation_when_redis_close_also_fails():
    cancellation = asyncio.CancelledError()
    redis_error = RuntimeError("redis-secret-detail")
    http_client = AsyncMock()
    http_client.aclose.side_effect = cancellation
    redis_client = AsyncMock()
    redis_client.aclose.side_effect = redis_error
    service = TranslationAudioService(
        settings=enabled_settings(),
        redis_client=redis_client,
        http_client=http_client,
    )

    with pytest.raises(asyncio.CancelledError) as error:
        await service.aclose()

    assert error.value is cancellation
    http_client.aclose.assert_awaited_once()
    redis_client.aclose.assert_awaited_once()
    assert error.value.__notes__ == ["Redis client cleanup also failed"]
    assert error.value.__suppress_context__
    assert "redis-secret-detail" not in "\n".join(error.value.__notes__)


@pytest.mark.anyio
async def test_aclose_aggregates_http_and_redis_close_failures():
    http_error = RuntimeError("HTTP close failed")
    redis_error = RuntimeError("Redis close failed")
    http_client = AsyncMock()
    http_client.aclose.side_effect = http_error
    redis_client = AsyncMock()
    redis_client.aclose.side_effect = redis_error
    service = TranslationAudioService(
        settings=enabled_settings(),
        redis_client=redis_client,
        http_client=http_client,
    )

    with pytest.raises(ExceptionGroup) as error:
        await service.aclose()

    assert [str(exception) for exception in error.value.exceptions] == [
        "HTTP close failed",
        "Redis close failed",
    ]
    http_client.aclose.assert_awaited_once()
    redis_client.aclose.assert_awaited_once()


@pytest.mark.anyio
async def test_aclose_propagates_redis_error_after_http_close_completes():
    redis_error = RuntimeError("Redis close failed")
    http_client = AsyncMock()
    redis_client = AsyncMock()
    redis_client.aclose.side_effect = redis_error
    service = TranslationAudioService(
        settings=enabled_settings(),
        redis_client=redis_client,
        http_client=http_client,
    )

    with pytest.raises(RuntimeError) as error:
        await service.aclose()

    assert error.value is redis_error
    http_client.aclose.assert_awaited_once()
    redis_client.aclose.assert_awaited_once()


@pytest.mark.anyio
async def test_translation_audio_dependency_is_unavailable_outside_lifespan():
    isolated_app = FastAPI()
    request = Request({"type": "http", "app": isolated_app})

    try:
        with pytest.raises(HTTPException) as error:
            get_translation_audio_service(request)
        assert error.value.status_code == 503
    finally:
        service = getattr(isolated_app.state, "translation_audio_service", None)
        if service is not None:
            await service.aclose()


@pytest.mark.anyio
async def test_surah_source_is_fetched_once_for_consecutive_ayahs():
    source_calls = []

    async def source(request):
        source_calls.append(str(request.url))
        return httpx.Response(
            200,
            json={
                "data": {
                    "number": 1,
                    "edition": {"identifier": "th.thai"},
                    "ayahs": [
                        {"numberInSurah": 1, "text": "หนึ่ง"},
                        {"numberInSurah": 2, "text": "สอง"},
                    ],
                }
            },
        )

    service = service_for(source_handler=source)
    await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    await service.synthesize(1, 2, "th.thai", 1.0, "192.0.2.3")
    assert len(source_calls) == 1
    with pytest.raises(HTTPException) as missing:
        await service.synthesize(1, 3, "th.thai", 1.0, "192.0.2.3")
    assert missing.value.status_code == 502
    await service.aclose()


WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVE" + b"\x00" * 24


@pytest.mark.anyio
async def test_native_gemini_tts_returns_wav_without_openai_speech_endpoint():
    import base64

    seen = []

    async def provider(request):
        seen.append(request)
        body = json.loads(request.content)
        assert body["contents"][0]["parts"][0]["text"] == SOURCE_TEXT
        assert body["generationConfig"]["responseModalities"] == ["AUDIO"]
        voice = body["generationConfig"]["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]
        assert voice["voiceName"] == "Kore"
        assert request.headers["x-goog-api-key"] == "tts-secret"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "inlineData": {
                                        "mimeType": "audio/wav",
                                        "data": base64.b64encode(WAV_BYTES).decode(),
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    async def source(request):
        return httpx.Response(200, json=valid_source_response())

    service = service_for(
        source_handler=source,
        provider_handler=provider,
        settings=enabled_settings(
            TTS_API_BASE_URL="https://generativelanguage.googleapis.com/v1beta",
            TTS_MODEL="gemini-3.8-flash-lite-tts",
            TTS_VOICE_MAP={"th": "Kore", "en": "Kore", "id": "Kore"},
        ),
    )
    result = await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert result.audio == WAV_BYTES
    assert str(seen[0].url).endswith("/models/gemini-3.8-flash-lite-tts:generateContent")
    await service.aclose()


@pytest.mark.anyio
async def test_native_gemini_tts_rejects_non_audio_reply():
    async def provider(request):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "hi"}]}}]})

    async def source(request):
        return httpx.Response(200, json=valid_source_response())

    service = service_for(
        source_handler=source,
        provider_handler=provider,
        settings=enabled_settings(
            TTS_API_BASE_URL="https://generativelanguage.googleapis.com/v1beta",
        ),
    )
    with pytest.raises(HTTPException) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert error.value.status_code == 502
    await service.aclose()


@pytest.mark.anyio
async def test_native_gemini_tts_rate_limit_is_reported_as_429():
    async def provider(request):
        return httpx.Response(429, json={"error": {"status": "RESOURCE_EXHAUSTED"}})

    async def source(request):
        return httpx.Response(200, json=valid_source_response())

    service = service_for(
        source_handler=source,
        provider_handler=provider,
        settings=enabled_settings(
            TTS_API_BASE_URL="https://generativelanguage.googleapis.com/v1beta",
        ),
    )
    with pytest.raises(HTTPException) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert error.value.status_code == 429
    assert "quota" in error.value.detail.lower()
    await service.aclose()


GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


def gemini_audio_reply():
    import base64

    return httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"inlineData": {
            "mimeType": "audio/wav", "data": base64.b64encode(WAV_BYTES).decode()}}]}}]},
    )


def fallback_service(provider, clock=None):
    async def source(request):
        return httpx.Response(200, json=valid_source_response())

    service = service_for(
        source_handler=source,
        provider_handler=provider,
        settings=enabled_settings(
            TTS_API_BASE_URL=GEMINI_BASE,
            TTS_MODEL="primary-tts",
            TTS_FALLBACK_MODELS="backup-tts,last-tts",
            TTS_MODEL_COOLDOWN_SECONDS=300,
        ),
    )
    if clock:
        service._clock = clock
    return service


@pytest.mark.anyio
async def test_quota_error_falls_back_to_next_model_and_returns_audio():
    seen = []

    async def provider(request):
        seen.append(str(request.url))
        if "primary-tts" in str(request.url):
            return httpx.Response(429, json={})
        return gemini_audio_reply()

    service = fallback_service(provider)
    result = await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert result.audio == WAV_BYTES
    assert [u.split("/models/")[1].split(":")[0] for u in seen] == ["primary-tts", "backup-tts"]
    await service.aclose()


@pytest.mark.anyio
async def test_rate_limited_model_is_skipped_during_cooldown_then_retried():
    seen = []
    now = [1000.0]

    async def provider(request):
        seen.append(str(request.url).split("/models/")[1].split(":")[0])
        if "primary-tts" in str(request.url) and now[0] < 1400:
            return httpx.Response(429, json={})
        return gemini_audio_reply()

    service = fallback_service(provider, clock=lambda: now[0])
    await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    await service.synthesize(1, 1, "th.thai", 1.1, "192.0.2.3")
    assert seen == ["primary-tts", "backup-tts", "backup-tts"]
    now[0] = 1401.0
    await service.synthesize(1, 1, "th.thai", 1.2, "192.0.2.3")
    assert seen[-1] == "primary-tts"
    await service.aclose()


@pytest.mark.anyio
async def test_all_models_exhausted_reports_429():
    async def provider(request):
        return httpx.Response(429, json={})

    service = fallback_service(provider)
    with pytest.raises(HTTPException) as error:
        await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert error.value.status_code == 429
    await service.aclose()


@pytest.mark.anyio
async def test_provider_server_error_also_falls_back():
    async def provider(request):
        if "primary-tts" in str(request.url):
            return httpx.Response(503, json={})
        return gemini_audio_reply()

    service = fallback_service(provider)
    result = await service.synthesize(1, 1, "th.thai", 1.0, "192.0.2.3")
    assert result.audio == WAV_BYTES
    await service.aclose()
