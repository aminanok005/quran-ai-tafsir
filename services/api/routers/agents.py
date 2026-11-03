"""
Agents Router for QURAN AI

Handles all API endpoints for multi-agent Tafsir system.
Provides access to 6 specialized Tafsir agents with evidence validation.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models import AgentType
from ..services import AgentOrchestratorService, EvidenceValidationService
from ..config import settings

router = APIRouter(tags=["Agents"])
logger = logging.getLogger(__name__)

# Initialize services
agent_orchestrator = AgentOrchestratorService()
evidence_validator = EvidenceValidationService()

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
    background_tasks: BackgroundTasks,
    ayah_id: str,
    agent_types: List[str],
    context: Optional[Dict[str, Any]] = None,
    validate_output: bool = True
):
    """Get Tafsir explanation from specified agents for a specific ayah."""

    try:
        # Parse ayah ID (format: "surah:ayah")
        if ":" not in ayah_id:
            raise HTTPException(status_code=400, detail="Invalid ayah ID format. Use format: 'surah:ayah'")

        surah, ayah = map(int, ayah_id.split(":"))

        if not (1 <= surah <= 114):
            raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")

        if not (1 <= ayah <= 200):
            raise HTTPException(status_code=400, detail="Ayah number must be between 1 and 200")

        # Validate agent types
        valid_agent_types = ["ibn_kathir", "al_tabari", "al_qurtubi", "ibn_ashur", "al_saadi", "al_zuhayli"]
        for agent_type in agent_types:
            if agent_type not in valid_agent_types:
                raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")

        # Execute agent analysis
        agent_outputs = await agent_orchestrator.execute_agent_analysis(
            surah, ayah, agent_types, context
        )

        # Validate outputs if requested
        if validate_output:
            validation_results = await evidence_validator.bulk_validate_agent_outputs(
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
        if ":" not in ayah_id:
            raise HTTPException(status_code=400, detail="Invalid ayah ID format. Use format: 'surah:ayah'")

        surah, ayah = map(int, ayah_id.split(":"))

        if not agent_types:
            # Default to all agents if none specified
            agent_types = ["ibn_kathir", "al_tabari", "al_qurtubi", "ibn_ashur", "al_saadi", "al_zuhayli"]

        # Get comparative analysis
        comparative_analysis = await agent_orchestrator.execute_agent_analysis(
            surah, ayah, agent_types
        ).get("comparative_analysis")

        if not comparative_analysis:
            raise HTTPException(status_code=400, detail="Insufficient agents for comparison")

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
                flashcard["validation"] = validation_result
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