"""Map Gemini provider errors to generic HTTP statuses."""

from .gemini_provider import GeminiError, GeminiErrorKind

_STATUS = {
    GeminiErrorKind.CONFIGURATION: 503,
    GeminiErrorKind.AUTHENTICATION: 503,
    GeminiErrorKind.RATE_LIMIT: 429,
    GeminiErrorKind.TIMEOUT: 504,
}


def http_status_for(error: GeminiError) -> int:
    return _STATUS.get(error.kind, 502)
