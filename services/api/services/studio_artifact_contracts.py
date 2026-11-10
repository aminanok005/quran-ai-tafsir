"""Strict contracts for the structured Studio artifact kinds."""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    ValidationError,
    model_validator,
)


class StudioGenerationError(RuntimeError):
    """Raised when a provider returns malformed structured content."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _AudioSegment(_StrictModel):
    host: Literal["Host A", "Host B"]
    text: Annotated[StrictStr, Field(min_length=1, max_length=1200)]

    @model_validator(mode="after")
    def require_thai_script(self):
        if re.search(r"[\u0E00-\u0E7F]", self.text) is None:
            raise ValueError("audio text must contain Thai script")
        return self


class _AudioContent(_StrictModel):
    segments: list[_AudioSegment] = Field(min_length=4, max_length=8)

    @model_validator(mode="after")
    def require_alternating_hosts(self):
        for index, segment in enumerate(self.segments):
            expected_host = "Host A" if index % 2 == 0 else "Host B"
            if segment.host != expected_host:
                raise ValueError("audio hosts must alternate starting with Host A")
        return self


class _QuizQuestion(_StrictModel):
    question: Annotated[StrictStr, Field(min_length=1, max_length=500)]
    options: list[Annotated[StrictStr, Field(min_length=1, max_length=200)]] = Field(
        min_length=3,
        max_length=3,
    )
    answer_index: Annotated[StrictInt, Field(ge=0, le=2)]
    explanation: Annotated[StrictStr, Field(min_length=1, max_length=1000)]
    source_passage_id: Annotated[StrictStr, Field(min_length=1, max_length=200)] | None = None


class _QuizContent(_StrictModel):
    questions: list[_QuizQuestion] = Field(min_length=5, max_length=5)


class _Flashcard(_StrictModel):
    front: Annotated[StrictStr, Field(min_length=1, max_length=300)]
    back: Annotated[StrictStr, Field(min_length=1, max_length=600)]
    source_passage_id: Annotated[StrictStr, Field(min_length=1, max_length=200)]


class _FlashcardsContent(_StrictModel):
    cards: list[_Flashcard] = Field(min_length=3, max_length=12)


class _InfographicCard(_StrictModel):
    heading: Annotated[StrictStr, Field(min_length=1, max_length=100)]
    points: list[Annotated[StrictStr, Field(min_length=1, max_length=280)]] = Field(
        min_length=2,
        max_length=5,
    )


class _InfographicContent(_StrictModel):
    takeaway: Annotated[StrictStr, Field(min_length=1, max_length=500)]
    cards: list[_InfographicCard] = Field(min_length=3, max_length=6)
    layout_hint: Literal["stacked", "two-column", "sequence"] = "stacked"


class _ArtifactEnvelope(_StrictModel):
    title: Annotated[StrictStr, Field(min_length=1, max_length=160)]
    summary: Annotated[StrictStr, Field(max_length=500)]


def validate_studio_artifact(
    kind: Literal["audio", "quiz", "infographic", "flashcards"],
    title: object,
    summary: object,
    content: object,
) -> dict[str, object]:
    content_models = {
        "audio": _AudioContent,
        "quiz": _QuizContent,
        "flashcards": _FlashcardsContent,
        "infographic": _InfographicContent,
    }
    try:
        envelope = _ArtifactEnvelope.model_validate({"title": title, "summary": summary})
        validated_content = content_models[kind].model_validate(content)
    except (ValidationError, TypeError):
        raise StudioGenerationError(
            "Artifact response does not match the required contract"
        ) from None

    return {
        "title": envelope.title,
        "summary": envelope.summary,
        "content": validated_content.model_dump(exclude_unset=True),
    }


def validate_studio_artifact_envelope(
    kind: str,
    artifact: object,
) -> dict[str, object]:
    if not isinstance(artifact, dict) or set(artifact) != {"title", "summary", "content"}:
        raise StudioGenerationError("Artifact response does not match the required contract")
    if kind == "audio":
        structured_kind: Literal["audio", "quiz", "infographic"] = "audio"
    elif kind == "quiz":
        structured_kind = "quiz"
    elif kind == "infographic":
        structured_kind = "infographic"
    else:
        raise StudioGenerationError("Artifact response does not match the required contract")
    return validate_studio_artifact(
        structured_kind,
        artifact["title"],
        artifact["summary"],
        artifact["content"],
    )
