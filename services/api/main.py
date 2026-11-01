"""QURAN AI API entry point for Quran Reader data."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
QURAN_API_BASE_URL = os.getenv(
    "QURAN_COM_API_BASE_URL", "https://api.quran.com/api/v4"
).rstrip("/")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(
        base_url=QURAN_API_BASE_URL,
        timeout=httpx.Timeout(15.0),
    ) as client:
        app.state.quran_client = client
        yield


app = FastAPI(
    title="QURAN AI API",
    version="0.1.0",
    description="Thai-first Quran study and evidence-based Tafsir API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


async def get_quran_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.quran_client


async def fetch_quran_data(
    client: httpx.AsyncClient, path: str, *, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    try:
        response = await client.get(path, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as error:
        logger.warning("Quran API request failed for %s: %s", path, error)
        raise HTTPException(
            status_code=502, detail="The Quran data service is currently unavailable."
        ) from error
    except ValueError as error:
        logger.warning("Quran API returned invalid JSON for %s", path)
        raise HTTPException(
            status_code=502, detail="The Quran data service returned an invalid response."
        ) from error

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=502, detail="The Quran data service returned an invalid response."
        )
    return payload


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/surahs", tags=["Quran"])
async def get_surahs(
    client: httpx.AsyncClient = Depends(get_quran_client),
) -> dict[str, Any]:
    payload = await fetch_quran_data(
        client, "/chapters", params={"language": "en"}
    )
    if not isinstance(payload.get("chapters"), list):
        raise HTTPException(
            status_code=502, detail="The Quran data service returned invalid chapter data."
        )
    return payload


@app.get("/api/v1/surahs/{surah_id}/ayahs", tags=["Quran"])
async def get_surah_ayahs(
    surah_id: int = Path(ge=1, le=114),
    client: httpx.AsyncClient = Depends(get_quran_client),
) -> dict[str, Any]:
    payload = await fetch_quran_data(
        client,
        f"/verses/by_chapter/{surah_id}",
        params={"fields": "text_uthmani,verse_key", "per_page": 300},
    )
    if not isinstance(payload.get("verses"), list):
        raise HTTPException(
            status_code=502, detail="The Quran data service returned invalid Ayah data."
        )
    return payload
