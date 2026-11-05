"""
Base Tafsir Agent class for QURAN AI

Provides common functionality for all 6 specialized Tafsir agents.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging
import json

logger = logging.getLogger(__name__)

class BaseTafsirAgent(ABC):
    """Base class for all Tafsir agents."""

    def __init__(self, agent_type: str, scholar_name: str, methodology: str):
        self.agent_type = agent_type
        self.scholar_name = scholar_name
        self.methodology = methodology
        self.source_collection = f"{agent_type}_collection"
        self.retrieval_config = {
            "min_confidence": 0.72,
            "max_results": 5,
            "filter_by_verified": True
        }
        self.quality_gates = [
            {
                "type": "citation_accuracy",
                "threshold": 0.8,
                "action": "request_revision"
            },
            {
                "type": "content_authenticity",
                "threshold": 0.9,
                "action": "reject"
            }
        ]

    @abstractmethod
    async def explain_ayah(self, surah: int, ayah: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Tafsir explanation for a specific ayah."""
        pass

    async def compare_views(self, surah: int, ayah: int, other_agents: List[str]) -> Dict[str, Any]:
        """Compare scholarly views when a concrete agent implements comparison."""
        raise NotImplementedError(
            f"{self.agent_type} does not implement direct view comparison"
        )

    async def retrieve_sources(self, surah: int, ayah: int, session=None) -> List[Dict[str, Any]]:
        """Retrieve relevant Tafsir sources from database."""
        try:
            # In a real implementation, this would query the database
            # For now, return mock data structure
            return []
        except Exception as e:
            logger.error(f"Error retrieving sources: {e}")
            return []

    async def validate_citations(self, explanation: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that all citations are properly attributed."""
        try:
            # Simple validation - check if explanation contains source references
            validation_result = {
                "valid": True,
                "issues": [],
                "confidence": 0.8
            }

            # Check for required citations
            if "Tafsir" not in explanation:
                validation_result["issues"].append("Missing Tafsir reference")
                validation_result["valid"] = False

            return validation_result
        except Exception as e:
            logger.error(f"Error validating citations: {e}")
            return {"valid": False, "issues": [str(e)], "confidence": 0.0}

    async def classify_evidence(self, explanation: str, sources: List[Dict[str, Any]]) -> str:
        """Classify evidence level based on available sources."""
        if not sources:
            return "UNVERIFIED"

        # Check if we have verified sources
        verified_sources = [s for s in sources if s.get("verification_status") == "verified"]
        if verified_sources:
            return "VERIFIED"

        # Check if sources are attributed
        attributed_sources = [s for s in sources if s.get("source_url")]
        if attributed_sources:
            return "SOURCE-ATTRIBUTED"

        return "AI-SYNTHESIS"

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent configuration information."""
        return {
            "agent_type": self.agent_type,
            "scholar_name": self.scholar_name,
            "methodology": self.methodology,
            "source_collection": self.source_collection,
            "retrieval_config": self.retrieval_config,
            "quality_gates": self.quality_gates
        }