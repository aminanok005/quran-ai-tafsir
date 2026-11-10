from services.api.services.gemini_http import http_status_for
from services.api.services.gemini_provider import GeminiError, GeminiErrorKind


def test_mapping():
    assert http_status_for(GeminiError(GeminiErrorKind.CONFIGURATION)) == 503
    assert http_status_for(GeminiError(GeminiErrorKind.RATE_LIMIT)) == 429
    assert http_status_for(GeminiError(GeminiErrorKind.TIMEOUT)) == 504
    assert http_status_for(GeminiError(GeminiErrorKind.AUTHENTICATION)) == 503
    assert http_status_for(GeminiError(GeminiErrorKind.MALFORMED)) == 502
