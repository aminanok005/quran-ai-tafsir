import asyncio
import json
import os
import unittest
from unittest.mock import patch

import httpx

from services.api.config import Settings
from services.api.services.gemini_provider import GeminiError, GeminiErrorKind, GeminiProvider
from services.api.services.model_router import ModelRouter, Task


def make_settings(**extra):
    env = {"DATABASE_URL": "postgresql://localhost/q", "GEMINI_API_KEY": "test-key-not-real",
           "PRIMARY_MODEL": "m-primary", "REASONING_MODEL": "m-reason", "FAST_MODEL": "m-fast",
           "GEMINI_MAX_RETRIES": "1", **extra}
    with patch.dict(os.environ, env, clear=True):
        return Settings(_env_file=None)


async def _no_sleep(_seconds):
    return None


def ok(content, usage=None):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}],
                                     "usage": usage or {"prompt_tokens": 10, "completion_tokens": 5}})


def provider(cfg, handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GeminiProvider(cfg, client)


class GeminiTests(unittest.IsolatedAsyncioTestCase):
    async def test_routing_by_task_and_fallback_chain(self):
        r = ModelRouter(provider(make_settings(FALLBACK_MODEL="m-fb"), lambda r: ok("x")), make_settings(FALLBACK_MODEL="m-fb"))
        self.assertEqual(r.models_for(Task.TRANSLATION), ["m-primary", "m-fb"])
        self.assertEqual(r.models_for(Task.IKHTILAF)[0], "m-reason")
        self.assertEqual(r.models_for(Task.CLASSIFICATION)[0], "m-fast")

    async def test_json_usage_cost_and_auth_header(self):
        cfg = make_settings(GEMINI_MODEL_PRICES=json.dumps({"m-primary": {"input_per_million": 1.0, "output_per_million": 2.0}}))
        seen = {}

        def handler(request):
            seen["auth"] = request.headers["authorization"]
            seen["path"] = request.url.path
            return ok('```json\n{"a": 1}\n```')
        router = ModelRouter(provider(cfg, handler), cfg)
        result = await router.run(Task.TRANSLATION, [{"role": "user", "content": "hi"}], json_output=True)
        self.assertEqual(result.data, {"a": 1})
        self.assertTrue(seen["path"].endswith("/chat/completions"))
        self.assertAlmostEqual(router.usage["m-primary"]["cost"], 20 / 1_000_000)
        self.assertEqual(router.usage["m-primary"]["calls"], 1)

    async def test_retry_on_rate_limit_then_succeed(self):
        calls = []

        def handler(request):
            calls.append(1)
            return httpx.Response(429) if len(calls) == 1 else ok("done")
        cfg = make_settings()
        with patch("services.api.services.gemini_provider.asyncio.sleep", new=_no_sleep):
            result = await ModelRouter(provider(cfg, handler), cfg).run(Task.CONTENT, [])
        self.assertEqual(result.text, "done")
        self.assertEqual(len(calls), 2)

    async def test_fallback_model_used_after_failure_and_retries_bounded(self):
        models = []

        def handler(request):
            model = json.loads(request.content)["model"]
            models.append(model)
            return httpx.Response(500) if model == "m-primary" else ok("fb")
        cfg = make_settings(FALLBACK_MODEL="m-fb")
        with patch("services.api.services.gemini_provider.asyncio.sleep", new=_no_sleep):
            result = await ModelRouter(provider(cfg, handler), cfg).run(Task.CONTENT, [])
        self.assertEqual(result.usage.model, "m-fb")
        self.assertEqual(models, ["m-primary", "m-primary", "m-fb"])

    async def test_auth_error_not_retried_and_error_has_no_secret(self):
        calls = []

        def handler(request):
            calls.append(1)
            return httpx.Response(401, text="bad key test-key-not-real")
        cfg = make_settings(FALLBACK_MODEL="m-fb")
        with self.assertRaises(GeminiError) as ctx:
            await ModelRouter(provider(cfg, handler), cfg).run(Task.CONTENT, [])
        self.assertEqual(ctx.exception.kind, GeminiErrorKind.AUTHENTICATION)
        self.assertNotIn("test-key-not-real", str(ctx.exception))
        self.assertEqual(len(calls), 1)

    async def test_malformed_and_invalid_json(self):
        cfg = make_settings(GEMINI_MAX_RETRIES="0")
        with self.assertRaises(GeminiError) as ctx:
            await provider(cfg, lambda r: ok("not json")).generate("m", [], json_output=True)
        self.assertEqual(ctx.exception.kind, GeminiErrorKind.MALFORMED)

    async def test_missing_key_makes_no_request(self):
        cfg = make_settings()
        cfg.gemini_api_key = None
        called = []
        with self.assertRaises(GeminiError):
            await provider(cfg, lambda r: called.append(1) or ok("x")).generate("m", [])
        self.assertEqual(called, [])

    async def test_concurrency_limit(self):
        cfg = make_settings(GEMINI_MAX_CONCURRENCY="2")
        running = peak = 0

        class T(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                nonlocal running, peak
                running += 1
                peak = max(peak, running)
                await asyncio.sleep(0.01)
                running -= 1
                return ok("x")
        p = GeminiProvider(cfg, httpx.AsyncClient(transport=T()))
        await asyncio.gather(*(p.generate("m", []) for _ in range(6)))
        self.assertEqual(peak, 2)

    def test_key_not_in_frontend_env_example(self):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[3] / "apps/web/.env.example").read_text()
        self.assertNotIn("GEMINI", text.upper())
