"""Grounded Arabic->Thai translation workflow. Arabic text and citations come from
server-side sources only; the model output is validated and never replaces them."""

from __future__ import annotations

import json
from typing import Any, Literal, Optional, Sequence

from pydantic import BaseModel, Field, ValidationError

from .gemini_provider import GeminiError, GeminiErrorKind
from .model_router import ModelRouter, Task

EvidenceStatus = Literal["VERIFIED", "SOURCE_ATTRIBUTED", "SCHOLARLY_DIFFERENCE", "UNVERIFIED", "AI_SYNTHESIS"]


class Ambiguity(BaseModel):
    expression: str = Field(max_length=200)
    note: str = Field(max_length=500)


class TranslationDraft(BaseModel):
    literal_th: str = Field(min_length=1, max_length=4000)
    contextual_th: str = Field(min_length=1, max_length=4000)
    ambiguities: list[Ambiguity] = Field(default_factory=list, max_length=20)
    source_ids_used: list[str] = Field(default_factory=list)


class QualityReview(BaseModel):
    terminology_preserved: bool
    meaning_preserved: bool
    issues: list[str] = Field(default_factory=list, max_length=20)


_SYSTEM = (
    "You translate Quran text into Thai. Use only the supplied Arabic and source passages. "
    "Never invent verses, hadith, quotations, scholars or page numbers. Keep Quranic terms "
    "transliterated or glossed. Reply with JSON only."
)


async def translate_ayah(
    router: ModelRouter,
    *,
    verse_key: str,
    arabic_text: str,
    sources: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Return a translation record. `arabic_text` is passed through unchanged."""
    if not arabic_text.strip():
        raise ValueError("arabic_text must not be empty")
    allowed = {str(s["source_id"]): s for s in sources if s.get("source_id")}
    context = [{"source_id": sid, "scholar": s.get("scholar_name"), "text": s.get("text", "")} for sid, s in allowed.items()]
    prompt = json.dumps({
        "verse_key": verse_key, "arabic": arabic_text, "sources": context,
        "schema": {"literal_th": "str", "contextual_th": "str", "ambiguities": [{"expression": "str", "note": "str"}], "source_ids_used": ["source_id"]},
    }, ensure_ascii=False)
    result = await router.run(Task.TRANSLATION, [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": prompt}], json_output=True)
    try:
        draft = TranslationDraft.model_validate(result.data)
    except ValidationError as error:
        raise GeminiError(GeminiErrorKind.MALFORMED) from error

    # Citation integrity: drop any id the model cites that we did not supply.
    cited = [sid for sid in dict.fromkeys(draft.source_ids_used) if sid in allowed]
    references = [
        {"source_id": sid, "scholar_name": allowed[sid].get("scholar_name"), "volume": allowed[sid].get("volume"), "page": allowed[sid].get("page")}
        for sid in cited
    ]
    status: EvidenceStatus = "SOURCE_ATTRIBUTED" if references else "UNVERIFIED"

    review: Optional[QualityReview] = None
    try:
        rr = await router.run(Task.CLASSIFICATION, [
            {"role": "system", "content": "Review the Thai translation for Quranic terminology and meaning. Reply JSON: terminology_preserved, meaning_preserved, issues."},
            {"role": "user", "content": json.dumps({"arabic": arabic_text, "thai": draft.contextual_th}, ensure_ascii=False)},
        ], json_output=True)
        review = QualityReview.model_validate(rr.data)
    except (GeminiError, ValidationError):
        review = None

    return {
        "verse_key": verse_key,
        "arabic_text": arabic_text,
        "literal_th": draft.literal_th,
        "contextual_th": draft.contextual_th,
        "ambiguities": [a.model_dump() for a in draft.ambiguities],
        "references": references,
        "evidence_status": status,
        "ai_generated": True,
        "quality_review": review.model_dump() if review else None,
    }
