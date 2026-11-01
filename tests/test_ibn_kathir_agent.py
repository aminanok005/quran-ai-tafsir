"""
Test for Ibn Kathir Agent

Tests for the Ibn Kathir agent implementation including:
- Source retrieval
- Citation validation
- Response formatting
- Quality gate validation
- Edge case handling
"""

import asyncio
import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from ...agents.ibn-kathir.agent import IbnKathirAgent
from ...agents.ibn-kathir.source_retrieval import IbnKathirSourceRetrieval
from ...agents.ibn-kathir.citation_validator import CitationValidator, ValidationResult
from ...agents.ibn-kathir.response_formatter import IbnKathirResponseFormatter

@pytest.fixture
def agent_config():
    """Test configuration for Ibn Kathir agent."""
    return {
        "agent_id": "ibn-kathir",
        "scholar": "Ibn Kathir",
        "scholar_ar": "ابن كثير",
        "methodology": "ma'thur",
        "max_context_length": 4000,
        "temperature": 0.1,
        "quality_gates": [
            {"type": "citation_accuracy", "threshold": 0.95, "action": "reject"},
            {"type": "content_authenticity", "threshold": 0.98, "action": "reject"}
        ]
    }

@pytest.fixture
def test_context():
    """Test context for ayah execution."""
    return {
        "ayah_id": "1:1",
        "surah": 1,
        "ayah": 1,
        "arabic_text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
        "methodology": "ma'thur"
    }

class TestIbnKathirSourceRetrieval:
    """Tests for source retrieval."""

    async def test_retrieve_valid_ayah(self):
        """Test retrieval of valid ayah sources."""
        retrieval = IbnKathirSourceRetrieval()
        # Initialize with mock data
        await retrieval.load_sources()

        results = await retrieval.retrieve("1:1", {}, "ma'thur", max_results=5)
        assert len(results) > 0
        assert results[0]["relevance_score"] > 0.3

    async def test_retrieve_no_sources(self):
        """Test retrieval returns empty list for unknown ayah."""
        retrieval = IbnKathirSourceRetrieval()
        await retrieval.load_sources()

        results = await retrieval.retrieve("999:999", {}, "ma'thur")
        assert results == [] or len(results) == 0

    async def test_cache_hits(self):
        """Test that cache works correctly."""
        retrieval = IbnKathirSourceRetrieval()
        await retrieval.load_sources()

        # First retrieval should hit cache after second call
        result1 = await retrieval.retrieve("1:1", {}, "ma'thur", max_results=5)
        result2 = await retrieval.retrieve("1:1", {}, "ma'thur", max_results=5)

        assert len(result1) == len(result2)

class TestCitationValidator:
    """Tests for citation validator."""

    async def test_validate_valid_source(self):
        """Test validation of a valid source."""
        validator = CitationValidator()

        is_valid, result = await validator.validate(
            source_id="test_1",
            author="Ibn Kathir",
            title="Tafsir Ibn Kathir",
            excerpt="plain text excerpt here that is reasonably long",
            source_type="tafsir"
        )

        assert is_valid is True
        assert len(result.issues) == 0 or all(issue.severity != "CRITICAL" for issue in result.issues)

    async def test_validate_unverified_source(self):
        """Test validation flags unverified sources."""
        validator = CitationValidator()
        validator.source_database = {
            "test_unverified": {
                "id": "test_unverified",
                "source_id": "tafsir_ibn_kathir",
                "verified": False,
                "grading": "hasan",
                "original_text": "test text"
            }
        }

        is_valid, result = await validator.validate(
            source_id="test_unverified",
            author="Ibn Kathir",
            title="Tafsir Ibn Kathir",
            excerpt="text here",
            source_type="tafsir"
        )

        assert is_valid is False

    async def test_validate_unknown_source(self):
        """Test validation flags unknown sources."""
        validator = CitationValidator()

        is_valid, result = await validator.validate(
            source_id="nonexistent",
            author="Unknown Author",
            title="Unknown Book",
            excerpt="some text",
            source_type="tafsir"
        )

        assert is_valid is False

class TestIbnKathirAgent:
    """Tests for Ibn Kathir agent."""

    async def test_execute_with_valid_context(self, agent_config, test_context):
        """Test agent execution with valid context."""
        agent = IbnKathirAgent(agent_config)

        output = await agent.execute(test_context["ayah_id"], test_context)

        assert "explanation" in output
        assert "citations" in output
        assert output["confidence"] > 0.5

    async def test_execute_no_sources(self, agent_config, test_context):
        """Test agent behavior when no sources are found."""
        agent = IbnKathirAgent(agent_config)

        # Mock empty results
        with patch.object(agent.source_retrieval, 'retrieve', return_value=[]):
            output = await agent.execute(test_context["ayah_id"], test_context)

            assert "citations" in output
            assert output["confidence"] < 0.5

    async def test_quality_gates_reject(self, agent_config, test_context):
        """Test quality gates fail rejection."""
        agent_config["quality_gates"].append({
            "type": "scholarly_attribution",
            "threshold": 0.99,  # Very high threshold
            "action": "reject"
        })

        agent = IbnKathirAgent(agent_config)
        output = await agent.execute(test_context["ayah_id"], test_context)

        assert "citations" in output
        assert output["confidence"] <= 0.5

    async def test_get_stats(self, agent_config, test_context):
        """Test agent statistics."""
        agent = IbnKathirAgent(agent_config)

        await agent.execute(test_context["ayah_id"], test_context)

        stats = agent.get_stats()
        assert stats["statistics"]["total_executions"] >= 1

class TestResponseFormatter:
    """Tests for response formatter."""

    def test_format_standard_explanation(self):
        """Test formatting standard explanation."""
        formatter = IbnKathirResponseFormatter()

        sources = [
            {
                "source_id": "test1",
                "excerpt": "test excerpt text",
                "original_text": "test original",
                "author": "Ibn Kathir",
                "title": "Tafsir Ibn Kathir",
                "grade": "sahih",
                "verified": True,
                "relevance_score": 0.9
            }
        ]

        output = formatter.format(
            ayah_id="1:1",
            explanation="sample explanation text",
            sources=sources,
            context={"ayah_id": "1:1", "surah": 1, "ayah": 1}
        )

        assert "explanation" in output
        assert "citations" in output
        assert len(output["citations"]) > 0
        assert output["evidence_level"] in ["VERIFIED", "SOURCE-ATTRIBUTED", "UNVERIFIED"]

    def test_format_multiple_sources(self):
        """Test formatting multiple sources response."""
        formatter = IbnKathirResponseFormatter()

        sources = [
            {
                "source_id": "test1",
                "excerpt": "excerpt one",
                "author": "Ibn Kathir",
                "title": "Tafsir Ibn Kathir",
                "grade": "sahih",
                "verified": True
            },
            {
                "source_id": "test2",
                "excerpt": "excerpt two",
                "author": "Another Scholar",
                "title": "Another Tafsir",
                "grade": "hasan",
                "verified": True
            }
        ]

        output = formatter.format(
            ayah_id="1:1",
            explanation="multi-source explanation",
            sources=sources,
            context={"ayah_id": "1:1", "surah": 1, "ayah": 1}
        )

        assert len(output["citations"]) >= 2

    def test_evidence_level_mapping(self):
        """Test evidence level mapping."""
        formatter = IbnKathirResponseFormatter()

        # Test verified sahih source
        sources = [
            {"source_id": "t1", "graded": "sahih", "verified": True, "relevance_score": 0.9}
        ]

        output = formatter.format(
            ayah_id="1:1",
            explanation="test",
            sources=sources,
            context={"ayah_id": "1:1", "surah": 1, "ayah": 1}
        )

        assert output["evidence_level"] in ["VERIFIED", "SOURCE-ATTRIBUTED"]

    def test_scholarly_position(self):
        """Test scholarly position determination."""
        formatter = IbnKathirResponseFormatter()

        sources = [
            {"source_id": "t1", "author": "Ibn Kathir", "excerpt": "text"},
            {"source_id": "t2", "author": "Ibn Kathir", "excerpt": "text"}
        ]

        output = formatter.format(
            ayah_id="1:1",
            explanation="test",
            sources=sources,
            context={"ayah_id": "1:1", "surah": 1, "ayah": 1}
        )

        assert "Ibn Kathir" in output["scholarly_position"]