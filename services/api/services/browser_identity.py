"""Signed anonymous browser identity stored in an HttpOnly cookie."""

from __future__ import annotations

import hashlib
import hmac
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, Response

from ..config import settings

COOKIE_NAME = "quran_browser"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365


def _signature(browser_id: UUID) -> str:
    secret = settings.secret_key.strip()
    if settings.environment.lower() != "development" and (
        len(secret) < 32 or secret.startswith("GENERATE_")
    ):
        raise HTTPException(status_code=503, detail="Browser-scoped notes require a configured SECRET_KEY")
    return hmac.new(
        secret.encode("utf-8"),
        browser_id.bytes,
        hashlib.sha256,
    ).hexdigest()


def _decode_cookie(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        browser_id_text, signature = value.split(".", 1)
        browser_id = UUID(browser_id_text)
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(_signature(browser_id), signature):
        return None
    return browser_id


def get_or_create_browser_id(request: Request, response: Response) -> UUID:
    browser_id = _decode_cookie(request.cookies.get(COOKIE_NAME))
    if browser_id is not None:
        return browser_id

    browser_id = uuid4()
    secure_cookie = settings.environment.lower() != "development"
    response.set_cookie(
        key=COOKIE_NAME,
        value=f"{browser_id}.{_signature(browser_id)}",
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )
    return browser_id
