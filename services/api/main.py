"""QURAN AI API service bootstrap."""

from fastapi import FastAPI

app = FastAPI(
    title="QURAN AI API",
    version="0.1.0",
    description="Thai-first Quran study and evidence-based Tafsir API.",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
