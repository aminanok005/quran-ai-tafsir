"""Deprecated database-backed Tafsir search endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

router = APIRouter(prefix="/tafsir", tags=["Tafsir retrieval"])


class TafsirSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    surah_number: int | None = Field(default=None, ge=1, le=114)
    ayah_number: int | None = Field(default=None, ge=1, le=286)
    scholar_id: str | None = Field(default=None, min_length=1, max_length=80)
    top_k: int = Field(default=5, ge=1, le=20)
    include_development: bool = False

    @model_validator(mode="after")
    def require_ayah_filter_pair(self) -> "TafsirSearchRequest":
        if (self.surah_number is None) != (self.ayah_number is None):
            raise ValueError("surah_number and ayah_number must be provided together")
        return self


@router.post("/search", response_model=dict[str, Any])
async def semantic_tafsir_search(_payload: TafsirSearchRequest) -> dict[str, Any]:
    """Prevent local Tafsir rows from serving as current runtime sources."""
    raise HTTPException(
        status_code=410,
        detail="Database-backed Tafsir search is retired; use API-sourced Tafsir passages",
    )


__all__ = ["TafsirSearchRequest", "router", "semantic_tafsir_search"]
