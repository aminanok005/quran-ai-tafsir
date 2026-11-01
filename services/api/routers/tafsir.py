"""Ayah-selected source-grounded tafsir chat endpoints."""

from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from services.tafsir.agents import DEFAULT_DATABASES, get_agent_config
from services.tafsir.chat_agent import (
    TafsirChatAgent,
    TafsirLLMError,
    TafsirPermissionError,
)
from services.tafsir.rights import source_allows, source_permission

router = APIRouter(prefix="/api/v1/tafsir", tags=["tafsir"])


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class TafsirChatRequest(BaseModel):
    surah: int = Field(ge=1, le=114)
    ayah: int = Field(ge=1, le=286)
    scholar_id: str
    message: str = Field(min_length=1, max_length=2000)
    history: List[ChatTurn] = Field(default_factory=list, max_length=10)
    source_language: Optional[Literal["ar", "id"]] = None

    @model_validator(mode="after")
    def validate_history_size(self):
        if sum(len(turn.content) for turn in self.history) > 12000:
            raise ValueError("Combined conversation history must not exceed 12000 characters")
        return self


@router.get("/agents")
async def list_tafsir_agents():
    agents = []
    for agent_id in DEFAULT_DATABASES:
        config = get_agent_config(agent_id)
        agents.append(
            {
                "id": config.agent_id,
                "label": f"AI study assistant — {config.title}",
                "author": config.author,
                "author_ar": config.author_ar,
                "source_language": config.language,
                "database_available": config.database_path.is_file(),
                "enabled": config.database_path.is_file()
                and source_allows(
                    f"qul:{config.dataset_id}",
                    ["display", "quotation", "ai_processing"],
                ),
                "rights_status": source_permission(f"qul:{config.dataset_id}").get(
                    "status", "unknown"
                ),
                "verification_status": "not_reviewed",
            }
        )
        if agent_id == "al-saadi":
            indonesian = get_agent_config(agent_id, source_language="id")
            agents.append(
                {
                    "id": config.agent_id,
                    "label": f"AI study assistant — {indonesian.title}",
                    "author": indonesian.author,
                    "author_ar": indonesian.author_ar,
                    "source_language": indonesian.language,
                    "database_available": indonesian.database_path.is_file(),
                    "enabled": indonesian.database_path.is_file()
                    and source_allows(
                        f"qul:{indonesian.dataset_id}",
                        ["display", "quotation", "ai_processing"],
                    ),
                    "rights_status": source_permission(
                        f"qul:{indonesian.dataset_id}"
                    ).get("status", "unknown"),
                    "verification_status": "not_reviewed",
                }
            )
    return {"agents": agents}


@router.post("/chat")
async def chat_about_ayah(request: TafsirChatRequest):
    try:
        config = get_agent_config(
            request.scholar_id,
            source_language=request.source_language,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    if not config.database_path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Tafsir source database is unavailable: {config.database_path.name}",
        )
    if not source_allows(
        f"qul:{config.dataset_id}",
        ["display", "quotation", "ai_processing"],
    ):
        raise HTTPException(
            status_code=403,
            detail="This tafsir source is not approved for display and AI processing",
        )

    try:
        result = await TafsirChatAgent(config).respond(
            f"{request.surah}:{request.ayah}",
            request.message,
            [turn.model_dump() for turn in request.history],
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="Tafsir source database is unavailable",
        ) from error
    except TafsirPermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except TafsirLLMError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    if result["status"] == "source_unavailable":
        raise HTTPException(
            status_code=404,
            detail=f"No tafsir passage found for {request.surah}:{request.ayah}",
        )
    return result
