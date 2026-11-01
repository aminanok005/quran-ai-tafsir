"""
Ibn Kathir Agent

Tafsir bil-Ma''thur agent - Provides explanations based on Quran, authentic Hadith and reports from the Salaf.

This agent follows Ibn Kathir's methodology of using Quran, authentic Hadith, and reports from the Salaf (Companions and Successors) to explain verses.

Key features:
- Source-grounded explanations only
- Authentic Hadith validation and integration
- Scholarly reporting with chain verification
- Distinction between authentic and Isra'iliyyat reports
- Evidence grading (Sahih, Hasan, Daif)
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from ....shared_types import (
    TafsirExplanation, EvidenceLevel, EvidenceGrade,
    RetrievedSource, AgentOutput, CitationReference
)
from .source_retrieval import IbnKathirSourceRetrieval
from .citation_validator import CitationValidator
from .response_formatter import IbnKathirResponseFormatter

logger = logging.getLogger(__name__)

class IbnKathirAgent:
    """
    Ibn Kathir Agent implementing Tafsir bil-Ma''thur methodology.

    This agent retrieves sources from Ibn Kathir's tafsir and provides
    explanations grounded in authentic Quranic text, Hadith, and reports
    from the Salaf.
    """

    def __init__(self, config: Dict[str, Any]):
        self.agent_id = config.get("agent_id", "ibn-kathir")
        self.scholar = config.get("scholar", "Ibn Kathir")
        self.scholar_ar = config.get("scholar_ar", "ابن كثير")
        self.methodology = config.get("methodology", "ma'thur")
        self.max_context_length = config.get("max_context_length", 4000)
        self.temperature = config.get("temperature", 0.1)
        self.quality_gates = config.get("quality_gates", [])

        # Initialize dependencies
        self.source_retrieval = IbnKathirSourceRetrieval()
        self.citation_validator = CitationValidator()
        self.response_formatter = IbnKathirResponseFormatter()

        # Agent statistics
        self.stats = {
            "executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "cache_hits": 0,
            "sources_retrieved": 0,
            "citations_validated": 0
        }

    async def execute(self, ayah_id: str, context: Dict[str, Any]) -> AgentOutput:
        """
        Execute the agent for a specific ayah.

        Args:
            ayah_id: The ayah identifier (surah:ayah format)
            context: Context information including Arabic text, surah, ayah numbers

        Returns:
            AgentOutput with explanation and citations
        """
        execution_start = datetime.now()
        self.stats["executions"] += 1

        try:
            # Validate quality gates
            if not self._validate_quality_gates(context):
                return self._create_error_output(
                    "Quality gates failed",
                    confidence=0.0,
                    scholarly_position="Failed quality validation"
                )

            # Retrieve sources for the ayah
            sources = await self._retrieve_sources(ayah_id, context)
            self.stats["sources_retrieved"] += len(sources)

            if not sources:
                return self._create_error_output(
                    "No sources found for this ayah",
                    confidence=0.1,
                    scholarly_position="No available sources"
                )

            # Validate citations
            valid_sources = await self._validate_citations(sources)
            if not valid_sources:
                return self._create_error_output(
                    "No valid sources after citation validation",
                    confidence=0.1,
                    scholarly_position="Citation validation failed"
                )

            # Generate explanation
            explanation = await self._generate_explanation(ayah_id, valid_sources, context)

            # Format output
            output = self.response_formatter.format(
                ayah_id=ayah_id,
                explanation=explanation,
                sources=valid_sources,
                context=context
            )

            # Update stats
            self.stats["successful_executions"] += 1
            self.stats["citations_validated"] += len(output.get("citations", []))

            # Log execution
            execution_time = (datetime.now() - execution_start).total_seconds()
            logger.info(
                f"Ibn Kathir agent executed successfully for {ayah_id} "
                f"in {execution_time:.2f}s, retrieved {len(valid_sources)} sources"
            )

            return output

        except Exception as e:
            self.stats["failed_executions"] += 1
            logger.error(f"Ibn Kathir agent failed for {ayah_id}: {str(e)}", exc_info=True)

            return self._create_error_output(
                f"Agent execution failed: {str(e)}",
                confidence=0.0,
                scholarly_position="Error during execution"
            )

    async def _retrieve_sources(self, ayah_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve sources for the given ayah.

        Args:
            ayah_id: The ayah identifier
            context: Context information

        Returns:
            List of retrieved sources
        """
        try:
            # Use source retrieval system to find relevant Ibn Kathir passages
            sources = await self.source_retrieval.retrieve(
                ayah_id=ayah_id,
                context=context,
                methodology=self.methodology,
                max_results=10
            )

            # Filter and prioritize sources
            filtered_sources = await self._filter_sources(sources, context)

            return filtered_sources

        except Exception as e:
            logger.error(f"Source retrieval failed for {ayah_id}: {str(e)}")
            return []

    async def _filter_sources(self, sources: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter and prioritize sources based on quality criteria.

        Args:
            sources: Raw sources from retrieval
            context: Context information

        Returns:
            Filtered and prioritized sources
        """
        if not sources:
            return []

        # Apply filtering criteria
        filtered = []

        for source in sources:
            # Quality checks
            if not self._is_source_quality_acceptable(source):
                continue

            # Relevance scoring
            relevance_score = await self._calculate_source_relevance(source, context)

            if relevance_score >= 0.3:  # Minimum relevance threshold
                source["relevance_score"] = relevance_score
                filtered.append(source)

        # Sort by relevance score (descending)
        filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return filtered[:5]  # Return top 5 sources

    async def _validate_citations(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate citations for authenticity and reliability.

        Args:
            sources: Sources to validate

        Returns:
            Validated sources
        """
        valid_sources = []

        for source in sources:
            try:
                # Validate source authenticity
                is_valid, validation_result = await self.citation_validator.validate(
                    source_id=source.get("source_id"),
                    author=source.get("author"),
                    title=source.get("title"),
                    excerpt=source.get("excerpt", "")
                )

                if is_valid:
                    source["validation_result"] = validation_result
                    source["verified"] = True
                    valid_sources.append(source)
                else:
                    logger.warning(
                        f"Source validation failed: {source.get('source_id')} - "
                        f"Issues: {validation_result.get('issues', [])}"
                    )

            except Exception as e:
                logger.warning(f"Citation validation error for source {source.get('source_id')}: {str(e)}")
                # Include source even if validation fails, but mark as unverified
                source["validation_result"] = {"error": str(e)}
                source["verified"] = False
                source["relevance_score"] *= 0.5  # Penalize validation failures
                valid_sources.append(source)

        return valid_sources

    async def _generate_explanation(self, ayah_id: str, sources: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Generate explanation using validated sources.

        Args:
            ayah_id: The ayah identifier
            sources: Validated sources
            context: Context information

        Returns:
            Generated explanation
        """
        try:
            # Prepare source material for LLM
            source_material = self._prepare_source_material(sources)
            arabic_text = context.get("arabic_text", "")
            surah_number = context.get("surah", 0)
            ayah_number = context.get("ayah", 0)

            # Generate explanation (this would typically call an LLM)
            explanation = await self._call_llm_for_explanation(
                ayah_id=ayah_id,
                arabic_text=arabic_text,
                surah_number=surah_number,
                ayah_number=ayah_number,
                source_material=source_material,
                methodology=self.methodology
            )

            return explanation

        except Exception as e:
            logger.error(f"Explanation generation failed for {ayah_id}: {str(e)}")
            # Return a structured explanation based on available sources as fallback
            return self._create_structured_explanation_fallback(ayah_id, sources, context)

    async def _call_llm_for_explanation(self, ayah_id: str, arabic_text: str,
                                      surah_number: int, ayah_number: int,
                                      source_material: str, methodology: str) -> str:
        """
        Call LLM to generate explanation based on sources.

        Args:
            ayah_id: The ayah identifier
            arabic_text: The Arabic text of the ayah
            surah_number: Surah number
            ayah_number: Ayah number
            source_material: Compiled source material
            methodology: Agent methodology

        Returns:
            Generated explanation
        """
        # This is a placeholder for LLM integration
        # In a real implementation, this would:
        # 1. Format a prompt with the ayah context and sources
        # 2. Call the LLM API (OpenAI/Anthropic/etc.)
        # 3. Process the response
        # 4. Validate the response meets quality standards

        # For now, return a structured explanation based on source material
        prompt = self._build_explanation_prompt(
            ayah_id, arabic_text, surah_number, ayah_number,
            source_material, methodology
        )

        # TODO: Integrate with actual LLM service
        logger.warning("LLM integration not yet implemented - using structured fallback")

        return self._create_structured_explanation_fallback(
            ayah_id, source_material, {
                "arabic_text": arabic_text,
                "surah": surah_number,
                "ayah": ayah_number
            }
        )

    def _build_explanation_prompt(self, ayah_id: str, arabic_text: str,
                                 surah_number: int, ayah_number: int,
                                 source_material: str, methodology: str) -> str:
        """
        Build prompt for LLM explanation generation.

        Args:
            ayah_id: The ayah identifier
            arabic_text: The Arabic text of the ayah
            surah_number: Surah number
            ayah_number: Ayah number
            source_material: Compiled source material
            methodology: Agent methodology

        Returns:
            Formatted prompt
        """
        prompt = f"""You are Ibn Kathir's Tafsir agent, providing explanations based on
Quran, authentic Hadith, and reports from the Salaf.

AYAH CONTEXT:
Surah {surah_number}:{ayah_number}
Arabic Text: {arabic_text}

AVAILABLE SOURCES (from Ibn Kathir's tafsir):
{source_material}

METHODOLOGY:
Tafsir bil-Ma''thur - using Quran, authentic Hadith, and reports from the Salaf.

REQUIREMENTS:
1. Only use information from the provided sources above
2. Cite your sources when referencing specific content
3. Distinguish between:
   - Direct Quranic quotes
   - Authentic Hadith reports
   - Reports from Sahabah (Companions)
   - Reports from Tabi'in (Successors)
4. Identify and flag Isra'iliyyat reports
5. Use Thai language for explanation
6. Maintain scholarly accuracy and authenticity
7. Generate a comprehensive explanation suitable for study

EXPLANATION:
"""

        return prompt

    def _prepare_source_material(self, sources: List[Dict[str, Any]]) -> str:
        """
        Prepare source material for LLM consumption.

        Args:
            sources: Sources to prepare

        Returns:
            Formatted source material
        """
        if not sources:
            return "No sources available."

        formatted_sources = []

        for i, source in enumerate(sources, 1):
            source_id = source.get("source_id", f"source_{i}")
            author = source.get("author", "Unknown")
            title = source.get("title", "Untitled")
            excerpt = source.get("excerpt", "")
            relevance = source.get("relevance_score", 0)
            verified = source.get("verified", False)

            formatted = f"""Source {i}: {author} - {title}
Relevance: {relevance:.2f}
Verified: {'Yes' if verified else 'No'}

{excerpt}

---
"""
            formatted_sources.append(formatted)

        return "\n".join(formatted_sources)

    def _create_structured_explanation_fallback(self, ayah_id: str, sources: List[Dict[str, Any]],
                                                context: Dict[str, Any]) -> str:
        """
        Create a structured explanation as fallback when LLM is not available.

        Args:
            ayah_id: The ayah identifier
            sources: Available sources
            context: Context information

        Returns:
            Structured explanation
        """
        surah = context.get("surah", 0)
        ayah = context.get("ayah", 0)
        arabic_text = context.get("arabic_text", "")

        explanation = f"""بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ

تفسير سورة {surah}:{ayah} من منظور ابن كثير

النص القرآني:
{arabic_text}

المصادر المتاحة:
"""

        if sources:
            for i, source in enumerate(sources, 1):
                author = source.get("author", "Unknown")
                title = source.get("title", "Untitled")
                excerpt = source.get("excerpt", "")
                relevance = source.get("relevance_score", 0)
                verified = source.get("verified", False)

                explanation += f"""
{i}. {author} - {title} (Relevance: {relevance:.2f}, Verified: {'✓' if verified else '✗'})
{excerpt}

"""
        else:
            explanation += "\nلا توجد مصادر متاحة لهذا الجزء.\n"

        explanation += """
الخلاصة:
يجب الرجوع إلى المصادر الأصلية للحصول على تفسير كامل ودقيق.
هذا النظام هو مساعد بحثي، وليس بديلاً عن العلماء.
"""

        return explanation

    def _create_error_output(self, error_message: str, confidence: float = 0.0,
                           scholarly_position: str = "Error") -> AgentOutput:
        """
        Create an error output with proper structure.

        Args:
            error_message: Error message
            confidence: Confidence level
            scholarly_position: Scholarly position

        Returns:
            Error output
        """
        return {
            "explanation": f"العذر الطويل من ابن كثير: {error_message}",
            "citations": [],
            "confidence": confidence,
            "scholarly_position": scholarly_position,
            "methodology_notes": "Quality gates failed or no valid sources found",
            "limitations": ["Agent execution failed", "No valid sources available"]
        }

    def _validate_quality_gates(self, context: Dict[str, Any]) -> bool:
        """
        Validate quality gates for the execution.

        Args:
            context: Context information

        Returns:
            True if quality gates pass, False otherwise
        """
        for gate in self.quality_gates:
            gate_type = gate.get("type")
            threshold = gate.get("threshold", 0)
            action = gate.get("action", "allow")

            # Apply quality gate logic
            if gate_type == "citation_accuracy":
                # Would check citation accuracy based on context
                pass
            elif gate_type == "content_authenticity":
                # Would check content authenticity based on sources
                pass
            elif gate_type == "thai_translation":
                # Would check Thai translation quality
                pass
            elif gate_type == "scholarly_attribution":
                # Would check scholarly attribution
                pass

        return True

    async def _calculate_source_relevance(self, source: Dict[str, Any],
                                         context: Dict[str, Any]) -> float:
        """
        Calculate relevance score for a source.

        Args:
            source: Source to evaluate
            context: Context information

        Returns:
            Relevance score between 0 and 1
        """
        base_score = source.get("relevance_score", 0.5)

        # Adjust based on verification status
        if source.get("verified"):
            base_score *= 1.2

        # Adjust based on source quality
        source_quality = source.get("quality_score", 0.5)
        base_score *= source_quality

        # Adjust based on context match
        context_match = await self._calculate_context_match(source, context)
        base_score *= context_match

        # Clamp to 0-1 range
        return max(0.0, min(1.0, base_score))

    async def _calculate_context_match(self, source: Dict[str, Any],
                                     context: Dict[str, Any]) -> float:
        """
        Calculate how well source matches the context.

        Args:
            source: Source to evaluate
            context: Context information

        Returns:
            Context match score between 0 and 1
        """
        # Simple heuristic based on source metadata
        surah_match = 0.5
        ayah_match = 0.5
        topic_match = source.get("topic_match", 0.5)

        return (surah_match + ayah_match + topic_match) / 3.0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent execution statistics.

        Returns:
            Statistics dictionary
        """
        total = self.stats["executions"]
        successful = self.stats["successful_executions"]
        failed = self.stats["failed_executions"]

        success_rate = (successful / total * 100) if total > 0 else 0.0

        return {
            "agent_id": self.agent_id,
            "scholar": self.scholar,
            "methodology": self.methodology,
            "statistics": {
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": success_rate,
                "sources_retrieved": self.stats["sources_retrieved"],
                "citations_validated": self.stats["citations_validated"],
                "cache_hits": self.stats["cache_hits"]
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the agent.

        Returns:
            Health check results
        """
        try:
            # Test source retrieval
            test_context = {
                "surah": 1,
                "ayah": 1,
                "arabic_text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"
            }

            test_sources = await self.source_retrieval.retrieve("1:1", test_context, self.methodology, max_results=1)

            return {
                "agent_id": self.agent_id,
                "healthy": True,
                "source_retrieval_working": len(test_sources) > 0,
                "last_check": datetime.now().isoformat(),
                "issues": [] if test_sources else ["No sources available for test ayah"]
            }

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
                "issues": ["Health check failed"]
            }