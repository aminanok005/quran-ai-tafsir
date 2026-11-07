"""
Evidence Validation Service for QURAN AI

Validates Tafsir explanations for citation accuracy and evidence requirements.
Implements comprehensive validation according to master-prompts-vibecoding.md guidelines.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class CitationValidationError(Exception):
    """Exception raised for citation validation errors."""
    pass


def _explanation_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(item for item in value.values() if isinstance(item, str))
    return ""


class EvidenceValidationService:
    """Validates Tafsir explanations for religious accuracy and evidence requirements."""

    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.evidence_badges = {
            "VERIFIED": "Direct source match",
            "SOURCE-ATTRIBUTED": "Historical scholarly attribution",
            "SCHOLARLY-DIFFERENCE": "Recognized scholarly differences",
            "UNVERIFIED": "Contextual background without verification",
            "AI-SYNTHESIS": "Pedagogical explanation derived by AI"
        }

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from configuration."""
        return {
            "citation": {
                "min_citations": 1,
                "max_citations": 10,
                "required_sources": ["book", "volume", "page"],
                "forbidden_content": [
                    "I, Imam",
                    "I, Ibn Kathir",
                    "roleplay",
                    "fabricated",
                    "invented",
                    "unverified claim"
                ]
            },
            "content": {
                "min_confidence_score": 0.7,
                "max_ai_synthesis_ratio": 0.3,
                "required_elements": [
                    "tafsir_reference",
                    "scholarly_attribution",
                    "arabic_text_reference"
                ]
            },
            "scholarly": {
                "respect_ikhtilaf": True,
                "allow_methodological_differences": True,
                "require_source_attribution": True
            }
        }

    def validate_explanation(
        self,
        explanation: str,
        sources: List[Dict[str, Any]],
        scholar_name: str,
        agent_type: str
    ) -> Dict[str, Any]:
        """Validate a Tafsir explanation against all requirements."""

        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "scores": {},
            "evidence_level": "UNVERIFIED",
            "recommendations": [],
            "validated_at": datetime.now().isoformat()
        }

        # Rule 1: Citation validation
        citation_validation = self._validate_citations(explanation, sources)
        validation_result["scores"]["citation"] = citation_validation["score"]
        validation_result["errors"].extend(citation_validation["errors"])
        validation_result["warnings"].extend(citation_validation["warnings"])

        # Rule 2: Content validation
        content_validation = self._validate_content(explanation, scholar_name, agent_type)
        validation_result["scores"]["content"] = content_validation["score"]
        validation_result["errors"].extend(content_validation["errors"])
        validation_result["warnings"].extend(content_validation["warnings"])

        # Rule 3: Scholarly validation
        scholarly_validation = self._validate_scholarship(explanation, sources)
        validation_result["scores"]["scholarly"] = scholarly_validation["score"]
        validation_result["errors"].extend(scholarly_validation["errors"])
        validation_result["warnings"].extend(scholarly_validation["warnings"])

        # Determine overall validity
        validation_result["valid"] = len(validation_result["errors"]) == 0

        # Assign evidence level
        validation_result["evidence_level"] = self._determine_evidence_level(validation_result)

        # Generate recommendations
        validation_result["recommendations"] = self._generate_recommendations(validation_result)

        return validation_result

    def _validate_citations(
        self,
        explanation: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate citations and references."""

        validation = {
            "score": 1.0,
            "errors": [],
            "warnings": []
        }

        # Check for required citation elements
        if not any(
            source.get("book")
            or source.get("reference")
            or (
                isinstance(source.get("reference"), dict)
                and (
                    source["reference"].get("book")
                    or source["reference"].get("url")
                )
            )
            for source in sources
        ):
            validation["errors"].append("No source citations found")
            validation["score"] *= 0.5

        # Check for volume and page references
        source_with_volume_page = sum(
            1 for source in sources
            if source.get("volume")
            or source.get("page")
            or (
                isinstance(source.get("reference"), dict)
                and (
                    source["reference"].get("volume")
                    or source["reference"].get("page")
                )
            )
        )
        if source_with_volume_page < len(sources) * 0.7:  # At least 70% have volume/page
            validation["warnings"].append("Some sources lack volume/page references")
            validation["score"] *= 0.9

        # Check for forbidden content
        forbidden_patterns = self.validation_rules["citation"]["forbidden_content"]
        for pattern in forbidden_patterns:
            if re.search(pattern, explanation, re.IGNORECASE):
                validation["errors"].append(f"Content contains potentially fabricated claims: {pattern}")
                validation["score"] *= 0.0
                break

        return validation

    def _validate_content(
        self,
        explanation: str,
        scholar_name: str,
        agent_type: str
    ) -> Dict[str, Any]:
        """Validate content quality and scholarly standards."""

        validation = {
            "score": 1.0,
            "errors": [],
            "warnings": []
        }

        # Check for confidence indicators
        confidence_indicators = ["according to", "references", "source", "chapter", "verse"]
        has_confidence = any(indicator in explanation.lower() for indicator in confidence_indicators)

        if not has_confidence:
            validation["warnings"].append("Content lacks confidence indicators")
            validation["score"] *= 0.9

        # Check for required elements
        required_elements = self.validation_rules["content"]["required_elements"]
        missing_elements = []

        for element in required_elements:
            if element == "tafsir_reference":
                if "tafsir" not in explanation.lower():
                    missing_elements.append("tafsir reference")
            elif element == "scholarly_attribution":
                if not scholar_name or scholar_name.lower() in ["ibn kathir", "al-tabari", "al-qurtubi"]:
                    pass  # OK
                else:
                    missing_elements.append("scholarly attribution")
            elif element == "arabic_text_reference":
                if "arabic" not in explanation.lower() and "text" not in explanation.lower():
                    missing_elements.append("arabic text reference")

        if missing_elements:
            validation["warnings"].append(f"Missing content elements: {', '.join(missing_elements)}")
            validation["score"] *= 0.8

        return validation

    def _validate_scholarship(
        self,
        explanation: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate scholarly standards and academic integrity."""

        validation = {
            "score": 1.0,
            "errors": [],
            "warnings": []
        }

        # Check for scholarly differences (ikhtilaf)
        scholarly_differences = [
            "according to",
            "scholars differ",
            "interpretations vary",
            "disagreement",
            "differences of opinion"
        ]

        has_scholarly_differences = any(
            diff.lower() in explanation.lower() for diff in scholarly_differences
        )

        if has_scholarly_differences:
            validation["warnings"].append("Content contains recognized scholarly differences (ikhtilaf)")
            validation["score"] *= 0.95

        # Check for source attribution quality
        verified_sources = sum(1 for source in sources if source.get("verified"))
        if verified_sources > 0:
            validation["score"] *= 1.0  # Good
        else:
            validation["warnings"].append("No verified sources found")
            validation["score"] *= 0.9

        return validation

    def _determine_evidence_level(self, validation_result: Dict[str, Any]) -> str:
        """Do not infer source verification or scholarly disagreement from text heuristics."""
        return "AI-SYNTHESIS" if validation_result["valid"] else "UNVERIFIED"

    def _generate_recommendations(
        self,
        validation_result: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on validation results."""

        recommendations = []

        if not validation_result["valid"]:
            recommendations.append("Fix citation errors before publishing")
            recommendations.append("Add more specific source references")

        if validation_result["scores"]["citation"] < 0.8:
            recommendations.append("Increase citation density and specificity")

        if "scholarly differences" in str(validation_result["warnings"]):
            recommendations.append("Maintain balanced presentation of scholarly differences")

        if validation_result["evidence_level"] == "AI-SYNTHESIS":
            recommendations.append("Add classical source citations")
            recommendations.append("Increase reliance on primary sources")

        return recommendations

    def validate_agent_output(
        self,
        agent_output: Dict[str, Any],
        agent_type: str
    ) -> Dict[str, Any]:
        """Validate a complete agent output including explanations and citations."""

        explanation = _explanation_text(agent_output.get("explanation", ""))
        citations = agent_output.get("citations", [])
        scholar_name = agent_output.get("scholar", agent_type)

        # Validate the explanation
        validation_result = self.validate_explanation(explanation, citations, scholar_name, agent_type)

        has_canonical_citations = bool(citations) and all(
            isinstance(citation, dict)
            and citation.get("evidence_status") == "VERIFIED"
            and isinstance(citation.get("passage_id"), str)
            and bool(citation["passage_id"])
            and isinstance(citation.get("reference"), dict)
            and str(citation["reference"].get("url", "")).startswith(("https://", "http://"))
            for citation in citations
        )
        if not has_canonical_citations:
            validation_result["errors"].append(
                "No server-verified source citations found"
            )
            validation_result["valid"] = False
            validation_result["evidence_level"] = "UNVERIFIED"
        elif validation_result["valid"]:
            validation_result["evidence_level"] = "SOURCE-ATTRIBUTED"
        else:
            validation_result["evidence_level"] = "UNVERIFIED"

        # Add agent-specific validation
        if agent_type == "ibn_kathir":
            # Ibn Kathir should not roleplay
            if "I, Imam" in explanation or "I, Ibn Kathir" in explanation:
                validation_result["errors"].append("Ibn Kathir agent should not roleplay")
                validation_result["valid"] = False
                validation_result["evidence_level"] = "UNVERIFIED"

        return validation_result

    def bulk_validate_agent_outputs(
        self,
        agent_outputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate multiple agent outputs in batch."""

        results = {
            "overall_valid": True,
            "agent_validations": {},
            "summary": {
                "total_agents": len(agent_outputs),
                "valid_agents": 0,
                "invalid_agents": 0,
                "evidence_levels": {}
            },
            "recommendations": [],
            "validated_at": datetime.now().isoformat()
        }

        for agent_type, output in agent_outputs.items():
            if "error" in output or output.get("status") == "failed":
                validation_result = {
                    "valid": False,
                    "errors": ["Agent execution failed"],
                    "warnings": [],
                    "evidence_level": "UNVERIFIED",
                    "validated_at": datetime.now().isoformat(),
                }
            else:
                validation_result = self.validate_agent_output(output, agent_type)
            results["agent_validations"][agent_type] = validation_result

            if validation_result["valid"]:
                results["summary"]["valid_agents"] += 1
            else:
                results["summary"]["invalid_agents"] += 1
                results["overall_valid"] = False

            # Count evidence levels
            evidence_level = validation_result["evidence_level"]
            results["summary"]["evidence_levels"][evidence_level] = (
                results["summary"]["evidence_levels"].get(evidence_level, 0) + 1
            )

        # Generate overall recommendations
        if not results["overall_valid"]:
            results["recommendations"].append(
                "Fix validation errors in agent outputs before publication"
            )

        return results

    def get_evidence_badge_info(self) -> Dict[str, str]:
        """Get information about evidence classification badges."""
        return self.evidence_badges.copy()
