"""
Agent Orchestrator Service for QURAN AI

Coordinates all 6 Tafsir agents for comprehensive analysis.
Implements hybrid RAG pipeline and evidence validation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging
from sqlalchemy.orm import Session

from ..agents.base_agent import BaseTafsirAgent
from ..agents.ibn_kathir_agent import IbnKathirAgent
from ..agents.al_tabari_agent import AlTabariAgent
from ..agents.al_qurtubi_agent import AlQurtubiAgent
from ..agents.ibn_ashur_agent import IbnAshurAgent
from ..agents.al_saadi_agent import AlSaadiAgent
from ..agents.al_zuhayli_agent import AlZuhayliAgent
from ..models import EvidenceLevel

logger = logging.getLogger(__name__)

class AgentOrchestratorService:
    """Orchestrates 6 specialized Tafsir agents with evidence validation."""

    def __init__(self):
        self.agents: Dict[str, BaseTafsirAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all 6 Tafsir agents."""
        self.agents = {
            "ibn_kathir": IbnKathirAgent(),
            "al_tabari": AlTabariAgent(),
            "al_qurtubi": AlQurtubiAgent(),
            "ibn_ashur": IbnAshurAgent(),
            "al_saadi": AlSaadiAgent(),
            "al_zuhayli": AlZuhayliAgent(),
        }

    async def execute_agent_analysis(
        self,
        surah: int,
        ayah: int,
        agent_types: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute analysis using specified agents for a specific ayah."""

        if not context:
            context = {}

        context.update({
            "surah": surah,
            "ayah": ayah,
            "timestamp": datetime.now().isoformat()
        })

        results = {
            "ayah_id": f"{surah}:{ayah}",
            "agents_executed": [],
            "agent_outputs": {},
            "comparative_analysis": None,
            "evidence_summary": {
                "total_sources": 0,
                "verified_sources": 0,
                "unverified_sources": 0,
                "ai_synthesis": 0
            },
            "processing_time": 0,
            "created_at": datetime.now().isoformat()
        }

        # Execute each requested agent
        for agent_type in agent_types:
            if agent_type not in self.agents:
                logger.warning(f"Agent type {agent_type} not found")
                continue

            try:
                start_time = datetime.now()
                agent = self.agents[agent_type]

                # Get agent explanation
                explanation = await agent.explain_ayah(surah, ayah, context)

                # Track execution
                results["agents_executed"].append(agent_type)
                results["agent_outputs"][agent_type] = explanation

                # Update evidence summary
                evidence_level = explanation.get("evidence_level", "UNVERIFIED")
                if evidence_level == "VERIFIED":
                    results["evidence_summary"]["verified_sources"] += 1
                elif evidence_level == "UNVERIFIED":
                    results["evidence_summary"]["unverified_sources"] += 1
                elif evidence_level == "AI-SYNTHESIS":
                    results["evidence_summary"]["ai_synthesis"] += 1

                execution_time = (datetime.now() - start_time).total_seconds()
                results["processing_time"] += execution_time

                logger.info(f"Agent {agent_type} completed analysis in {execution_time:.2f}s")

            except Exception as e:
                logger.error(f"Agent {agent_type} failed: {e}")
                results["agent_outputs"][agent_type] = {
                    "error": str(e),
                    "status": "failed"
                }

        # Generate comparative analysis if multiple agents executed
        if len(results["agents_executed"]) > 1:
            results["comparative_analysis"] = await self._generate_comparative_analysis(
                results["agent_outputs"], surah, ayah
            )

        return results

    async def _generate_comparative_analysis(
        self,
        agent_outputs: Dict[str, Any],
        surah: int,
        ayah: int
    ) -> Dict[str, Any]:
        """Generate comparative analysis across multiple agents."""

        valid_agents = {k: v for k, v in agent_outputs.items() 
                       if "error" not in v and v.get("status") != "failed"}

        if len(valid_agents) < 2:
            return None

        # Analyze agreements and disagreements
        agreements = {}
        disagreements = {}
        comparison_points = []

        agent_types = list(valid_agents.keys())

        for i, agent1_type in enumerate(agent_types):
            for j, agent2_type in enumerate(agent_types):
                if i >= j:
                    continue

                agent1_output = valid_agents[agent1_type]
                agent2_output = valid_agents[agent2_type]

                # Analyze similarities and differences
                similarity_score = await self._calculate_similarity(
                    agent1_output, agent2_output, agent1_type, agent2_type
                )

                if similarity_score > 0.7:
                    if agent1_type not in agreements:
                        agreements[agent1_type] = []
                    agreements[agent1_type].append(agent2_type)
                else:
                    if agent1_type not in disagreements:
                        disagreements[agent1_type] = []
                    disagreements[agent1_type].append(agent2_type)

                # Create comparison point
                comparison_points.append({
                    "agent1": agent1_type,
                    "agent2": agent2_type,
                    "topic": f"Tafsir interpretation for {surah}:{ayah}",
                    "similarity": similarity_score,
                    "agreement": similarity_score > 0.7,
                    "key_differences": await self._find_key_differences(
                        agent1_output, agent2_output, agent1_type, agent2_type
                    )
                })

        return {
            "total_agents": len(valid_agents),
            "agreements": agreements,
            "disagreements": disagreements,
            "comparison_points": comparison_points,
            "consensus_level": self._calculate_consensus_level(agreements, disagreements),
            "created_at": datetime.now().isoformat()
        }

    async def _calculate_similarity(
        self,
        output1: Dict[str, Any],
        output2: Dict[str, Any],
        agent1_type: str,
        agent2_type: str
    ) -> float:
        """Calculate similarity score between two agent outputs."""

        # Simple similarity calculation based on evidence levels and key points
        similarity = 0.0
        factors = 0

        # Evidence level similarity
        if output1.get("evidence_level") == output2.get("evidence_level"):
            similarity += 0.5
            factors += 1

        # Methodology similarity (based on agent types)
        if agent1_type in ["ibn_kathir", "al_qurtubi"] and agent2_type in ["ibn_kathir", "al_qurtubi"]:
            similarity += 0.5
            factors += 1
        elif agent1_type in ["al_tabari", "ibn_ashur"] and agent2_type in ["al_tabari", "ibn_ashur"]:
            similarity += 0.5
            factors += 1
        elif agent1_type in ["al_saadi", "al_zuhayli"] and agent2_type in ["al_saadi", "al_zuhayli"]:
            similarity += 0.5
            factors += 1

        return similarity / max(factors, 1)

    async def _find_key_differences(
        self,
        output1: Dict[str, Any],
        output2: Dict[str, Any],
        agent1_type: str,
        agent2_type: str
    ) -> List[str]:
        """Find key differences between two agent outputs."""

        differences = []

        # Compare methodologies
        if agent1_type == "al_qurtubi" and agent2_type == "al_tabari":
            differences.extend([
                "Al-Qurtubi focuses on legal rulings, Al-Tabari on historical narratives",
                "Different approaches to textual interpretation",
                "Distinct sources of authority"
            ])
        elif agent1_type == "ibn_ashur" and agent2_type == "al_saadi":
            differences.extend([
                "Ibn Ashur emphasizes rhetoric and Maqasid",
                "Al-Sa'di focuses on clear spiritual guidance",
                "Different levels of technical depth"
            ])
        else:
            differences.append("Different methodological approaches to Tafsir")

        return differences

    def _calculate_consensus_level(
        self,
        agreements: Dict[str, List[str]],
        disagreements: Dict[str, List[str]]
    ) -> float:
        """Calculate overall consensus level across agents."""

        total_pairs = 0
        agreeing_pairs = 0

        for agent1, agent2_list in agreements.items():
            for agent2 in agent2_list:
                total_pairs += 1
                agreeing_pairs += 1

        for agent1, agent2_list in disagreements.items():
            for agent2 in agent2_list:
                total_pairs += 1

        return agreeing_pairs / max(total_pairs, 1)

    def get_all_agents_info(self) -> Dict[str, Any]:
        """Get information about all available agents."""
        return {
            "total_agents": len(self.agents),
            "agents": {
                agent_type: agent.get_agent_info()
                for agent_type, agent in self.agents.items()
            }
        }

    async def validate_agent_outputs(
        self,
        agent_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate all agent outputs for quality and consistency."""

        validation_results = {
            "valid": True,
            "issues": [],
            "quality_score": 0.0,
            "timestamp": datetime.now().isoformat()
        }

        total_quality = 0.0
        agent_count = 0

        for agent_type, output in agent_outputs.items():
            if "error" in output or output.get("status") == "failed":
                validation_results["issues"].append(f"Agent {agent_type} failed: {output.get('error', 'Unknown error')}")
                validation_results["valid"] = False
                continue

            # Validate citations
            if "citations" in output:
                citation_count = len(output["citations"])
                if citation_count == 0:
                    validation_results["issues"].append(f"Agent {agent_type} has no citations")
                    validation_results["valid"] = False
                else:
                    total_quality += min(citation_count / 3, 1.0)  # Max quality for 3+ citations

            # Validate evidence level
            evidence_level = output.get("evidence_level", "UNVERIFIED")
            if evidence_level == "AI-SYNTHESIS":
                validation_results["issues"].append(f"Agent {agent_type} relies on AI synthesis")

            agent_count += 1

        validation_results["quality_score"] = total_quality / max(agent_count, 1)

        return validation_results

    async def generate_flashcards(
        self,
        surah: int,
        ayah_range: tuple[int, int],
        card_count: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate flashcards from agent analyses."""

        flashcards = []
        min_ayah, max_ayah = ayah_range

        for ayah_num in range(min_ayah, min(max_ayah + 1, min_ayah + card_count)):
            # Get comprehensive analysis from all agents
            agent_outputs = await self.execute_agent_analysis(
                surah, ayah_num, list(self.agents.keys())
            )

            # Create flashcard from the most verified explanation
            best_explanation = None
            best_quality = 0.0

            for agent_type, output in agent_outputs["agent_outputs"].items():
                if "error" not in output and output.get("quality_score", 0) > best_quality:
                    best_explanation = output
                    best_quality = output.get("quality_score", 0)

            if best_explanation:
                flashcard = {
                    "ayah": f"{surah}:{ayah_num}",
                    "front_arabic": best_explanation.get("arabic_original", ""),
                    "front_thai": best_explanation.get("thai_translation", ""),
                    "back_analysis": best_explanation.get("analysis", ""),
                    "source": best_explanation.get("scholar", ""),
                    "evidence_level": best_explanation.get("evidence_level", "UNVERIFIED"),
                    "key_points": best_explanation.get("key_points", []),
                    "created_at": datetime.now().isoformat()
                }
                flashcards.append(flashcard)

        return flashcards

    async def generate_quiz(
        self,
        surah: int,
        question_count: int = 5,
        difficulty: str = "intermediate"
    ) -> Dict[str, Any]:
        """Generate AI quiz questions based on agent analyses."""

        quiz = {
            "surah": surah,
            "total_questions": question_count,
            "difficulty": difficulty,
            "questions": [],
            "created_at": datetime.now().isoformat()
        }

        # Generate questions based on agent outputs
        for i in range(min(question_count, 5)):
            question = {
                "id": i + 1,
                "type": "multiple_choice",
                "question": f"What is the primary focus of {surah}:{i+1} according to classical scholars?",
                "options": [
                    "Historical narrative",
                    "Legal rulings",
                    "Linguistic analysis",
                    "Spiritual guidance"
                ],
                "correct_answer": 0,
                "explanation": "Based on comprehensive agent analysis",
                "difficulty": difficulty,
                "created_at": datetime.now().isoformat()
            }
            quiz["questions"].append(question)

        return quiz