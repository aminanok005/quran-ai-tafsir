import unittest

import httpx

from services.api.services.gemini_http import http_status_for
from services.api.services.gemini_provider import GeminiError, GeminiErrorKind
from services.api.tests.test_gemini_router import make_settings, provider


def truncated(_request):
    return httpx.Response(
        200,
        json={
            "choices": [{"finish_reason": "length", "message": {"role": "assistant"}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 0},
        },
    )


class TruncationTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_length_stop_is_reported_as_truncated_not_retried(self):
        calls = []

        def handler(request):
            calls.append(1)
            return truncated(request)

        p = provider(make_settings(), handler)
        with self.assertRaises(GeminiError) as ctx:
            await p.generate("m", [{"role": "user", "content": "x"}], max_tokens=20)
        self.assertEqual(ctx.exception.kind, GeminiErrorKind.TRUNCATED)
        self.assertEqual(len(calls), 1)
        self.assertEqual(http_status_for(ctx.exception), 502)
