import httpx
import pytest
from fastapi.testclient import TestClient

from services.api.main import app, get_quran_client


@pytest.fixture
def api_client():
    def handle_request(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/chapters"):
            return httpx.Response(
                200,
                json={
                    "chapters": [
                        {
                            "id": 1,
                            "name_simple": "Al-Fatihah",
                            "name_arabic": "الفاتحة",
                            "verses_count": 7,
                        }
                    ]
                },
            )
        if request.url.path.endswith("/verses/by_chapter/1"):
            return httpx.Response(
                200,
                json={
                    "verses": [
                        {
                            "id": 1,
                            "verse_key": "1:1",
                            "text_uthmani": "remote Arabic text",
                        }
                    ]
                },
            )
        return httpx.Response(503)

    upstream = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_request),
        base_url="https://quran.example.test/api/v4",
    )
    app.dependency_overrides[get_quran_client] = lambda: upstream
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(upstream.aclose())


def test_surahs_returns_upstream_chapter_data(api_client):
    response = api_client.get("/api/v1/surahs")

    assert response.status_code == 200
    assert response.json()["chapters"][0]["id"] == 1


def test_ayahs_returns_upstream_arabic_text(api_client):
    response = api_client.get("/api/v1/surahs/1/ayahs")

    assert response.status_code == 200
    assert response.json()["verses"][0]["text_uthmani"] == "remote Arabic text"


def test_invalid_surah_is_rejected(api_client):
    response = api_client.get("/api/v1/surahs/115/ayahs")

    assert response.status_code == 422
