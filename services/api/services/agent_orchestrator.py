"""
Agent Orchestrator Service for QURAN AI

Coordinates all 6 Tafsir agents for comprehensive analysis.
Implements hybrid RAG pipeline and evidence validation.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..agents.al_qurtubi_agent import AlQurtubiAgent
from ..agents.al_saadi_agent import AlSaadiAgent
from ..agents.al_tabari_agent import AlTabariAgent
from ..agents.al_zuhayli_agent import AlZuhayliAgent
from ..agents.base_agent import BaseTafsirAgent
from ..agents.ibn_ashur_agent import IbnAshurAgent
from ..agents.ibn_kathir_agent import IbnKathirAgent

logger = logging.getLogger(__name__)

class AgentOrchestratorService:
    """Orchestrates 6 specialized Tafsir agents with evidence validation."""

    def __init__(
        self,
        agents: Optional[Dict[str, BaseTafsirAgent]] = None,
        *,
        max_concurrency: int = 3,
        timeout_seconds: float = 30,
    ):
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least one")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.agents = agents if agents is not None else self._create_agents()
        self.max_concurrency = max_concurrency
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _create_agents() -> Dict[str, BaseTafsirAgent]:
        """Create the six supported Tafsir agents."""
        return {
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
        context: Optional[Dict[str, Any]] = None,
        *,
        source_passages: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Execute bounded, source-grounded analysis for a specific ayah."""
        if not 1 <= surah <= 114 or not 1 <= ayah <= 200:
            raise ValueError("Surah must be 1-114 and ayah must be 1-200")
        if not agent_types:
            raise ValueError("At least one agent must be selected")
        if len(set(agent_types)) != len(agent_types):
            raise ValueError("Agent types must be unique")
        unknown_agents = sorted(set(agent_types) - self.agents.keys())
        if unknown_agents:
            raise ValueError(f"Unknown agent types: {', '.join(unknown_agents)}")

        trusted_passages = self._trusted_passages(source_passages or [])
        if not trusted_passages:
            raise ValueError("No approved, verified source passages are available")

        agent_context = dict(context or {})
        agent_context.update({
            "surah": surah,
            "ayah": ayah,
            "source_passages": trusted_passages,
            "timestamp": datetime.now().isoformat()
        })

        started = time.perf_counter()
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def run_agent(agent_type: str) -> tuple[str, Dict[str, Any], float]:
            agent = self.agents[agent_type]
            started_agent = time.perf_counter()
            try:
                async with semaphore:
                    output = await asyncio.wait_for(
                        agent.explain_ayah(surah, ayah, dict(agent_context)),
                        timeout=self.timeout_seconds,
                    )
                if (
                    not isinstance(output, dict)
                    or output.get("ayah_id") != f"{surah}:{ayah}"
                    or not output.get("explanation")
                ):
                    raise ValueError("Agent returned an invalid response")
                citations = self._canonical_citations(output, trusted_passages)
                if citations is None:
                    return agent_type, {
                        "status": "failed",
                        "error": "Agent citations did not match approved source passages",
                    }, time.perf_counter() - started_agent
                return agent_type, {
                    **output,
                    "citations": citations,
                    "evidence_level": "SOURCE-ATTRIBUTED",
                }, time.perf_counter() - started_agent
            except asyncio.TimeoutError:
                logger.warning("Agent %s timed out", agent_type)
                return agent_type, {
                    "status": "failed",
                    "error": "Agent timed out",
                }, time.perf_counter() - started_agent
            except Exception as error:
                logger.warning(
                    "Agent %s failed (%s)",
                    agent_type,
                    type(error).__name__,
                )
                return agent_type, {
                    "status": "failed",
                    "error": "Agent execution failed",
                }, time.perf_counter() - started_agent

        settled = await asyncio.gather(*(run_agent(agent_type) for agent_type in agent_types))
        outputs = {agent_type: output for agent_type, output, _ in settled}
        succeeded = [
            agent_type
            for agent_type, output, _ in settled
            if output.get("status") != "failed" and "error" not in output
        ]
        cited_ids = {
            citation["passage_id"]
            for agent_type in succeeded
            for citation in outputs[agent_type]["citations"]
        }
        source_ids = {source["passage_id"] for source in trusted_passages}
        source_count = len(cited_ids & source_ids)
        evidence_summary = {
            "total_sources": source_count,
            "verified_sources": source_count,
            "unverified_sources": 0,
            "ai_synthesis": 0,
        }

        return {
            "ayah_id": f"{surah}:{ayah}",
            "agents_executed": succeeded,
            "agent_outputs": outputs,
            "comparative_analysis": None,
            "evidence_summary": evidence_summary,
            "processing_time": time.perf_counter() - started,
            "created_at": datetime.now().isoformat()
        }

    @staticmethod
    def _trusted_passages(passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            passage
            for passage in passages
            if isinstance(passage, dict)
            and isinstance(passage.get("passage_id"), str)
            and passage.get("permission_status") == "approved"
            and passage.get("verification_status") == "verified"
            and passage.get("license")
            and passage.get("verification_evidence")
            and passage.get("source_reference")
        ]

    @staticmethod
    def _canonical_citations(
        output: Dict[str, Any],
        source_passages: List[Dict[str, Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        citations = output.get("citations")
        if not isinstance(citations, list) or not citations:
            return None
        allowed_sources = {
            passage["passage_id"]: passage for passage in source_passages
        }
        canonical_citations = []
        for citation in citations:
            if not isinstance(citation, dict):
                return None
            passage_id = citation.get("passage_id")
            source = allowed_sources.get(passage_id) if isinstance(passage_id, str) else None
            if source is None:
                return None
            canonical_citations.append({
                "passage_id": passage_id,
                "reference": {
                    "book": source.get("book_title"),
                    "scholar": source.get("scholar_name"),
                    "volume": source.get("volume"),
                    "page": source.get("page"),
                    "edition": source.get("edition"),
                    "url": source["source_reference"],
                },
                "evidence_status": "VERIFIED",
            })
        return canonical_citations

    async def _generate_comparative_analysis(
        self,
        agent_outputs: Dict[str, Any],
        surah: int,
        ayah: int,
    ) -> Optional[Dict[str, Any]]:
        """Do not infer scholarly agreement from metadata or agent names."""
        return None

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
        """Flashcard generation is unavailable until it can use approved sources."""
        raise NotImplementedError(
            "Source-grounded flashcard generation is not available yet"
        )

    async def generate_quiz(
        self,
        surah: int,
        question_count: int = 5,
        difficulty: str = "intermediate"
    ) -> Dict[str, Any]:
        """Quiz generation is unavailable until every answer can be cited."""
        raise NotImplementedError(
            "Source-grounded quiz generation is not available yet"
        )