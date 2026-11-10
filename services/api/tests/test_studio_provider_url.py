import pytest

from services.api.routers.workspace import _is_loopback_provider_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:20128/v1",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
    ],
)
def test_allows_loopback_and_google_gemini(url):
    assert _is_loopback_provider_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://generativelanguage.googleapis.com/v1beta/openai/",
        "https://generativelanguage.googleapis.com.evil.com/v1",
        "https://evil.com/v1",
        "https://user:pw@generativelanguage.googleapis.com/v1",
        "https://generativelanguage.googleapis.com/v1?x=1",
    ],
)
def test_rejects_other_hosts(url):
    assert not _is_loopback_provider_url(url)
