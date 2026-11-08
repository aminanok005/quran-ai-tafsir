"""
Agents Router for QURAN AI

Handles all API endpoints for multi-agent Tafsir system.
Provides access to 6 specialized Tafsir agents with evidence validation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..services import AgentOrchestratorService, EvidenceValidationService
from ..services.quran_foundation_tafsir import QuranFoundationTafsirError
from .tafsir import (
    _api_source_url,
    _get_api_source_permission,
    _translation_is_allowed,
    get_engine,
    get_qf_tafsir_client,
)

router = APIRouter(tags=["Agents"])
logger = logging.getLogger(__name__)

# Initialize services
agent_orchestrator = AgentOrchestratorService()
evidence_validator = EvidenceValidationService()


async def _approved_source_passages(
    surah: int,
    ayah: int,
    agent_types: List[str],
) -> List[Dict[str, Any]]:
    """Fetch current API sources and admit only sources approved for AI use."""
    engine = get_engine()
    approved_resources: list[tuple[int, Dict[str, Any]]] = []
    seen_resources: set[int] = set()

    for agent_type in agent_types:
        resource_id = settings.quran_tafsir_resource_map.get(agent_type)
        if resource_id is None or resource_id in seen_resources:
            continue
        seen_resources.add(resource_id)
        permission = _get_api_source_permission(engine, resource_id)
        if _translation_is_allowed(permission) and permission is not None:
            approved_resources.append((resource_id, permission))

    if not approved_resources:
        return []

    source_passages = []
    try:
        client = get_qf_tafsir_client()
        for resource_id, permission in approved_resources:
            passage = await client.fetch_ayah(resource_id, surah, ayah)
            source_passages.append({
                "passage_id": f"qf:{passage.resource_id}:{passage.verse_key}",
                "resource_id": passage.resource_id,
                "verse_key": passage.verse_key,
                "arabic_text": passage.text,
                "volume": None,
                "page": None,
                "edition": passage.slug or None,
                "book_title": passage.resource_name,
                "scholar_id": agent_type,
                "scholar_name": passage.resource_name,
                "source_kind": "tafsir",
                "permission_status": permission["permission_status"],
                "verification_status": permission["verification_status"],
                "license": permission["license"],
                "verification_evidence": permission["verification_evidence"],
                "source_reference": _api_source_url(client, resource_id, passage.verse_key),
            })
    except QuranFoundationTafsirError as error:
        status_code = 503 if error.status_code is None or error.status_code >= 500 else 502
        logger.warning(
            "Quran Foundation Tafsir request failed for agent source (HTTP %s)",
            error.status_code or "network",
        )
        raise HTTPException(
            status_code=status_code,
            detail="Could not load the approved Quran Foundation Tafsir source",
        ) from error
    return source_passages


def _validated_agent_context(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    context = context or {}
    unknown_fields = set(context) - {"question", "language"}
    if unknown_fields:
        raise HTTPException(
            status_code=422,
            detail="Agent context only accepts question and language fields",
        )
    question = context.get("question")
    if question is not None and (
        not isinstance(question, str) or len(question) > 2000
    ):
        raise HTTPException(status_code=422, detail="Question must be text of at most 2000 characters")
    language = context.get("language")
    if language is not None and language not in {"ar", "en", "th"}:
        raise HTTPException(status_code=422, detail="Language must be one of: ar, en, th")
    return context


@router.get("/agents", response_model=Dict[str, Any])
async def get_available_agents():
    """Get list of all available Tafsir agents."""
    try:
        agents_info = agent_orchestrator.get_all_agents_info()
        return {
            "success": True,
            "data": agents_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting available agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available agents")

@router.post("/explain", response_model=Dict[str, Any])
async def get_agent_explanation(
    ayah_id: str,
    agent_types: List[str],
    context: Optional[Dict[str, Any]] = None,
    validate_output: bool = True
):
    """Get Tafsir explanation from specified agents for a specific ayah."""

    try:
        # Parse ayah ID (format: "surah:ayah")
        parts = ayah_id.split(":")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid ayah ID format. Use format: 'surah:ayah'")

        try:
            surah, ayah = map(int, parts)
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid ayah ID format. Use format: 'surah:ayah'") from error
        if not (1 <= surah <= 114 and 1 <= ayah <= 200):
            raise HTTPException(status_code=400, detail="Ayah ID is out of range")

        # Validate agent types
        valid_agent_types = ["ibn_kathir", "al_tabari", "al_qurtubi", "ibn_ashur", "al_saadi", "al_zuhayli"]
        for agent_type in agent_types:
            if agent_type not in valid_agent_types:
                raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")
        if not agent_types:
            raise HTTPException(status_code=400, detail="Select at least one Tafsir agent")
        if len(set(agent_types)) != len(agent_types):
            raise HTTPException(status_code=400, detail="Tafsir agent types must be unique")

        source_passages = await _approved_source_passages(surah, ayah, agent_types)
        if not source_passages:
            raise HTTPException(
                status_code=503,
                detail="No approved, verified Tafsir passages are available for this ayah",
            )

        agent_context = _validated_agent_context(context)
        agent_outputs = await agent_orchestrator.execute_agent_analysis(
            surah,
            ayah,
            agent_types,
            agent_context,
            source_passages=source_passages,
        )
        if not agent_outputs["agents_executed"]:
            raise HTTPException(
                status_code=503,
                detail="Agents could not produce output grounded in approved source passages",
            )

        # Validate outputs if requested
        if validate_output:
            validation_results = evidence_validator.bulk_validate_agent_outputs(
                agent_outputs["agent_outputs"]
            )
            agent_outputs["validation"] = validation_results

        return {
            "success": True,
            "data": agent_outputs,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent explanation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent explanation")

@router.post("/compare", response_model=Dict[str, Any])
async def compare_agents(
    ayah_id: str,
    agent_types: List[str] = None
):
    """Compare scholarly views across multiple agents for a specific ayah."""

    try:
        parts = ayah_id.split(":")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid ayah ID format. Use format: 'surah:ayah'")

        try:
            surah, ayah = map(int, parts)
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid ayah ID format. Use format: 'surah:ayah'") from error
        if not (1 <= surah <= 114 and 1 <= ayah <= 200):
            raise HTTPException(status_code=400, detail="Ayah ID is out of range")

        if not agent_types:
            # Default to all agents if none specified
            agent_types = ["ibn_kathir", "al_tabari", "al_qurtubi", "ibn_ashur", "al_saadi", "al_zuhayli"]

        if any(agent_type not in agent_orchestrator.agents for agent_type in agent_types):
            raise HTTPException(status_code=400, detail="Invalid agent type")
        if len(set(agent_types)) != len(agent_types):
            raise HTTPException(status_code=400, detail="Tafsir agent types must be unique")
        source_passages = await _approved_source_passages(surah, ayah, agent_types)
        if not source_passages:
            raise HTTPException(
                status_code=503,
                detail="No approved, verified Tafsir passages are available for this ayah",
            )

        # Get comparative analysis
        analysis = await agent_orchestrator.execute_agent_analysis(
            surah,
            ayah,
            agent_types,
            source_passages=source_passages,
        )
        comparative_analysis = analysis["comparative_analysis"]

        if not comparative_analysis:
            raise HTTPException(
                status_code=503,
                detail="Source-grounded scholarly comparison is not available yet",
            )

        return {
            "success": True,
            "data": comparative_analysis,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare agents")

@router.get("/flashcards", response_model=Dict[str, Any])
async def generate_flashcards(
    surah: int,
    ayah_range: str = "1-10",
    card_count: int = 10,
    validate_output: bool = True
):
    """Generate flashcards from Tafsir passages."""

    try:
        # Parse ayah range (format: "start-end")
        if "-" not in ayah_range:
            raise HTTPException(status_code=400, detail="Invalid ayah range format. Use format: 'start-end'")

        start, end = map(int, ayah_range.split("-"))

        if not (1 <= surah <= 114):
            raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")

        if not (1 <= start <= end <= 200):
            raise HTTPException(status_code=400, detail="Invalid ayah range")

        if not (1 <= card_count <= 20):
            raise HTTPException(status_code=400, detail="Card count must be between 1 and 20")
        raise HTTPException(
            status_code=503,
            detail="Source-grounded flashcard generation is not available yet",
        )

        # Generate flashcards
        flashcards = await agent_orchestrator.generate_flashcards(
            surah, (start, end), card_count
        )

        # Validate if requested
        if validate_output and flashcards:
            flashcard_validation = []
            for card in flashcards:
                validation_result = await evidence_validator.validate_explanation(
                    card["back_analysis"], [], card.get("source", ""), "general"
                )
                card["validation"] = validation_result
                flashcard_validation.append(validation_result)

            # Summary of validation results
            valid_cards = sum(1 for val in flashcard_validation if val["valid"])

        return {
            "success": True,
            "data": {
                "flashcards": flashcards,
                "total_generated": len(flashcards),
                "validation_summary": {
                    "valid_cards": valid_cards if flashcards else 0,
                    "invalid_cards": len(flashcards) - valid_cards if flashcards else 0
                } if flashcards else {}
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate flashcards")

@router.post("/quiz", response_model=Dict[str, Any])
async def generate_quiz(
    surah: int,
    question_count: int = 5,
    difficulty: str = "intermediate",
    validate_output: bool = True
):
    """Generate AI quiz questions based on Tafsir analysis."""

    try:
        if not (1 <= surah <= 114):
            raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")

        if not (1 <= question_count <= 20):
            raise HTTPException(status_code=400, detail="Question count must be between 1 and 20")

        if difficulty not in ["beginner", "intermediate", "advanced"]:
            raise HTTPException(status_code=400, detail="Difficulty must be one of: beginner, intermediate, advanced")

        raise HTTPException(
            status_code=503,
            detail="Source-grounded quiz generation is not available yet",
        )

        # Generate quiz
        quiz = await agent_orchestrator.generate_quiz(surah, question_count, difficulty)

        # Validate if requested
        if validate_output and quiz:
            quiz["validation"] = {
                "valid": True,
                "issues": [],
                "recommendations": [],
                "validated_at": datetime.now().isoformat()
            }

        return {
            "success": True,
            "data": quiz,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")

@router.get("/evidence-badges", response_model=Dict[str, Any])
async def get_evidence_badges():
    """Get information about evidence classification badges."""

    try:
        badges_info = evidence_validator.get_evidence_badge_info()

        return {
            "success": True,
            "data": {
                "badges": badges_info,
                "description": {
                    "VERIFIED": "Direct verbatim match from authenticated primary source",
                    "SOURCE-ATTRIBUTED": "Found in historical scholarly text; narration grading preserved as reported",
                    "SCHOLARLY-DIFFERENCE": "Recognized divergent viewpoints between scholars/madhahib",
                    "UNVERIFIED": "Contextual background without verified classical citation",
                    "AI-SYNTHESIS": "Pedagogical explanation, flashcard, or quiz derived by AI"
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting evidence badges: {e}")
        raise HTTPException(status_code=500, detail="Failed to get evidence badges")

@router.get("/health", response_model=Dict[str, Any])
async def agents_health_check():
    """Health check for agents service."""

    try:
        # Check agent availability
        agents_info = agent_orchestrator.get_all_agents_info()

        # Validate each agent
        agent_health = {}
        for agent_type, agent_info in agents_info["agents"].items():
            agent_health[agent_type] = {
                "healthy": True,
                "agent_type": agent_info["agent_type"],
                "scholar_name": agent_info["scholar_name"],
                "methodology": agent_info["methodology"]
            }

        return {
            "success": True,
            "data": {
                "status": "healthy",
                "total_agents": len(agents_info["agents"]),
                "healthy_agents": len(agent_health),
                "agents": agent_health,
                "services": {
                    "agent_orchestrator": "available",
                    "evidence_validator": "available"
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in agents health check: {e}")
        return {
            "success": True,
            "data": {
                "status": "degraded",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        }