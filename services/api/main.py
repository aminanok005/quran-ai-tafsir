"""QURAN AI API service bootstrap."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.quran import router as quran_router
from .routers.tafsir import router as tafsir_router

app = FastAPI(
    title="QURAN AI API",
    version="0.1.0",
    description="Thai-first Quran study and evidence-based Tafsir API.",
)
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(quran_router)
app.include_router(tafsir_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
