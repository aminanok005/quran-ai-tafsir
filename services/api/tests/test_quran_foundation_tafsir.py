import base64
import unittest

import httpx

from services.api.services.quran_foundation_tafsir import (
    QuranFoundationTafsirClient,
    QuranFoundationTafsirError,
    resolve_auth_base_url,
)


class QuranFoundationTafsirClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetches_and_normalizes_a_tafsir_with_cached_oauth_token(self):
        requests = []

        async def handler(request):
            requests.append(request)
            if request.url.path == "/oauth2/token":
                return httpx.Response(200, json={"access_token": "test-token", "expires_in": 3600})
            return httpx.Response(
                200,
                json={
                    "tafsir": {
                        "verses": {"1:1": {"id": 7}},
                        "resource_id": 169,
                        "resource_name": "Tafsir Ibn Kathir",
                        "language_name": "english",
                        "slug": "en-tafisr-ibn-kathir",
                        "text": "<p>Text <b>with detail</b>.</p>",
                    },
                },
            )

        client = QuranFoundationTafsirClient(
            api_base_url="https://apis-prelive.quran.foundation",
            client_id="test-client",
            client_secret="test-secret",
            transport=httpx.MockTransport(handler),
        )

        first = await client.fetch_ayah(169, 1, 1)
        second = await client.fetch_ayah(169, 1, 1)

        self.assertEqual(first, second)
        self.assertEqual(first.text, "Text with detail.")
        self.assertEqual(first.verse_key, "1:1")
        self.assertEqual(
            sum(request.url.path == "/oauth2/token" for request in requests),
            1,
        )
        content_request = next(request for request in requests if "/tafsirs/" in request.url.path)
        self.assertEqual(
            str(content_request.url),
            "https://apis-prelive.quran.foundation/content/api/v4/tafsirs/169/by_ayah/1:1",
        )
        self.assertEqual(content_request.headers["x-auth-token"], "test-token")
        self.assertEqual(content_request.headers["x-client-id"], "test-client")
        expected_basic = base64.b64encode(b"test-client:test-secret").decode()
        token_request = next(request for request in requests if request.url.path == "/oauth2/token")
        self.assertEqual(token_request.headers["authorization"], f"Basic {expected_basic}")
        self.assertNotIn("test-secret", token_request.url.query.decode())

    async def test_rejects_a_mismatched_response_without_returning_remote_text(self):
        async def handler(request):
            if request.url.path == "/oauth2/token":
                return httpx.Response(200, json={"access_token": "test-token"})
            return httpx.Response(
                200,
                json={
                    "tafsir": {
                        "verses": {"2:1": {"id": 1}},
                        "resource_id": 169,
                        "resource_name": "Tafsir Ibn Kathir",
                        "language_name": "english",
                        "slug": "test",
                        "text": "private passage text",
                    },
                },
            )

        client = QuranFoundationTafsirClient(
            api_base_url="https://apis-prelive.quran.foundation",
            client_id="test-client",
            client_secret="test-secret",
            transport=httpx.MockTransport(handler),
        )

        with self.assertRaisesRegex(QuranFoundationTafsirError, "mismatched") as caught:
            await client.fetch_ayah(169, 1, 1)
        self.assertNotIn("private passage text", str(caught.exception))

    async def test_http_errors_are_sanitized_and_preserve_status(self):
        async def handler(request):
            if request.url.path == "/oauth2/token":
                return httpx.Response(200, json={"access_token": "test-token"})
            return httpx.Response(403, json={"message": "sensitive authorization detail"})

        client = QuranFoundationTafsirClient(
            api_base_url="https://apis-prelive.quran.foundation",
            client_id="test-client",
            client_secret="test-secret",
            transport=httpx.MockTransport(handler),
        )

        with self.assertRaises(QuranFoundationTafsirError) as caught:
            await client.fetch_ayah(169, 1, 1)
        self.assertEqual(caught.exception.status_code, 403)
        self.assertNotIn("sensitive authorization detail", str(caught.exception))

    def test_auth_base_url_matches_api_environment(self):
        self.assertEqual(
            resolve_auth_base_url("https://apis.quran.foundation"),
            "https://oauth2.quran.foundation",
        )
        self.assertEqual(
            resolve_auth_base_url("https://apis-prelive.quran.foundation"),
            "https://prelive-oauth2.quran.foundation",
        )
        self.assertEqual(
            resolve_auth_base_url("https://custom.example.test", "https://auth.example.test/"),
            "https://auth.example.test",
        )


if __name__ == "__main__":
    unittest.main()
