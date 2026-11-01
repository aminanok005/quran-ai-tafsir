"""
Response Formatter for Ibn Kathir Agent

Formats agent responses according to QURAN AI requirements:
- Source-grounded explanations
- Proper citation attribution
- Thai language responses
- Scholarly disagreement identification
- Evidence level labeling
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ....shared_types import (
    TafsirExplanation, EvidenceLevel, EvidenceGrade,
    RetrievedSource, AgentOutput, CitationReference
)

logger = logging.getLogger(__name__)

class IbnKathirResponseFormatter:
    """
    Formats responses for the Ibn Kathir agent according to QURAN AI standards.

    Ensures:
    - Source-grounded explanations only
    - Clear citation attribution
    - Thai language responses
    - Evidence level labeling
    - Scholarly disagreement identification
    - No fabricated references
    """

    def __init__(self):
        self.response_templates = self._load_templates()
        self.citation_formats = self._load_citation_formats()
        self.evidence_level_markers = self._load_evidence_level_markers()

    def _load_templates(self) -> Dict[str, str]:
        """Load response templates for different scenarios."""
        return {
            "standard_explanation": """
[[SOURCED_EXPLANATION]]

المراجع:
[[CITATIONS]]

مستوى الأدلة: [[EVIDENCE_LEVEL]]
""",
            "multiple_sources": """
[[SOURCED_EXPLANATIONS]]

ความเห็นต่างของนักวิชาการ:
[[DISAGREEMENT_ANALYSIS]]

المراجع:
[[CITATIONS]]

مستوى الأدلة: [[EVIDENCE_LEVEL]]
""",
            "error_response": """
ขออภัย ฉันไม่สามารถให้คำอธิบายเกี่ยวกับอายะฮ์นี้ได้เนื่องจากปัญหาต่อไปนี้:

[[ERROR_DETAILS]]

โปรด:
- ลองอีกครั้งในภายหลัง
- เลือกอายะฮ์อื่น
- ติดต่อทีมผู้ดูแลเพื่อรายงานปัญหานี้

หมายเหตุ: هذا النظام هو مساعد بحثي ไม่ใช่แทนที่นักวิชาการ
""",
            "no_sources": """
ไม่พบตำ�รที่ตัฟซีร Ibn Kathir สำหรับอายะฮ์นี้ในฐานข้อมูล.

คำแนะนำ:
- ลองอายะฮ์บริเวณใกล้เคียง
- ลองใช้ Tafsir อื่น (Al-Tabari, Al-Qurtubi)
- ตรวจสอบระบบแหล่งอ้างอิง

หากคุณมีแหล่งข้อมูลที่เป็นทางการมากกว่า โปรดแจ้งทีมงานของเรา
"""
        }

    def _load_citation_formats(self) -> Dict[str, str]:
        """Load citation format templates."""
        return {
            "quran_reference": "{surah}:{ayah}",
            "tafsir_reference": "{scholar} - {title}",
            "hadith_reference": "{book} {hadith_id}: {grading}",
            "generic_reference": "{source_type}: {id}"
        }

    def _load_evidence_level_markers(self) -> Dict[str, str]:
        """Load evidence level markers for different levels."""
        return {
            "VERIFIED": "✓ ก็อพอใจงั้นเถอะ",
            "SOURCE-ATTRIBUTED": "⚠ อ้างอิงจากแหล่งที่ได้รับการยืนยัน",
            "SCHOLARLY DIFFERENCE": "📚 มีนักวิชาการมีความเห็นแตกต่างกัน",
            "UNVERIFIED": "⚠ ยังไม่สามารถยืนยันหลักฐานได้",
            "AI SYNTHESIS": "🤖 นี่คือการสังเคราะห์ของ AI"
        }

    def format(self, ayah_id: str, explanation: str, sources: List[Dict[str, Any]],
              context: Dict[str, Any]) -> AgentOutput:
        """
        Format agent response according to QURAN AI standards.

        Args:
            ayah_id: The ayah identifier
            explanation: Generated explanation text
            sources: Validated sources used
            context: Context information

        Returns:
            Formatted agent output
        """
        try:
            # Determine response template based on scenario
            template = self._select_template(explanation, sources)

            # Process citations
            citations = self._format_citations(sources, context)

            # Analyze scholarly disagreement
            disagreement_analysis = self._analyze_disagreement(sources)

            # Determine evidence level
            evidence_level = self._determine_evidence_level(sources)

            # Format the final response
            formatted_response = self._apply_template(
                template, explanation, citations, disagreement_analysis, evidence_level
            )

            # Create agent output
            output = {
                "explanation": formatted_response,
                "citations": citations,
                "confidence": self._calculate_confidence(sources),
                "scholarly_position": self._determine_scholarly_position(sources),
                "methodology_notes": self._generate_methodology_notes(context),
                "limitations": self._identify_limitations(sources)
            }

            # Log formatting for audit purposes
            logger.info(
                f"Response formatted for ayah {ayah_id}: "
                f"confidence={output['confidence']:.2f}, "
                f"sources={len(sources)}, "
                f"evidence_level={evidence_level}"
            )

            return output

        except Exception as e:
            logger.error(f"Response formatting failed for ayah {ayah_id}: {str(e)}")

            # Return fallback error response
            return self._create_fallback_response(ayah_id, str(e))

    def _select_template(self, explanation: str, sources: List[Dict[str, Any]]) -> str:
        """
        Select appropriate response template based on scenario.

        Args:
            explanation: Generated explanation
            sources: Available sources

        Returns:
            Selected template
        """
        if not explanation and not sources:
            return self.response_templates["no_sources"]

        if not explanation:
            return self.response_templates["error_response"]

        if len(sources) > 1:
            return self.response_templates["multiple_sources"]

        return self.response_templates["standard_explanation"]

    def _format_citations(self, sources: List[Dict[str, Any]],
                         context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format citations from sources.

        Args:
            sources: Sources to cite
            context: Context information

        Returns:
            Formatted citations
        """
        citations = []

        for source in sources:
            citation = self._create_single_citation(source, context)
            if citation:
                citations.append(citation)

        return citations

    def _create_single_citation(self, source: Dict[str, Any],
                               context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a single citation from a source.

        Args:
            source: Source to create citation for
            context: Context information

        Returns:
            Formatted citation
        """
        try:
            ayah_id = context.get("ayah_id", "")
            surah = context.get("surah", 0)
            ayah = context.get("ayah", 0)

            # Determine citation type
            citation_type = self._determine_citation_type(source)

            # Format reference based on type
            reference = self._format_reference(source, citation_type, ayah_id)

            # Extract excerpt with proper attribution
            excerpt = self._extract_excerpt(source)

            # Preserve a grade only when the source provides one.
            grade = self._determine_source_grade(source)

            citation = {
                "source_id": source.get("source_id", ""),
                "passage_id": source.get("id", ""),
                "reference": reference,
                "excerpt": excerpt,
                "grade": grade,
                "verified": source.get("verified", False),
                "evidence_level": self._map_to_evidence_level(source.get("verified", False)),
                "metadata": {
                    "author": source.get("author", ""),
                    "title": source.get("title", ""),
                    "surah": source.get("surah", surah),
                    "ayah": source.get("ayah", ayah),
                    "ayah_range": source.get("ayah_range"),
                    "volume": source.get("volume"),
                    "page": source.get("page"),
                    "language": source.get("language", "ar"),
                    "dataset_file": source.get("dataset_file"),
                    "resource_url": source.get("resource_url"),
                    "rights_status": source.get("rights_status", "unknown"),
                    "relevance_score": source.get("relevance_score", 0)
                }
            }

            return citation

        except Exception as e:
            logger.error(f"Citation creation failed: {str(e)}")
            return None

    def _determine_citation_type(self, source: Dict[str, Any]) -> str:
        """Determine citation type based on source metadata."""
        source_type = source.get("type")
        author = source.get("author", "")
        title = source.get("title", "")

        if source.get("source_backend") == "qul_sqlite" or source_type == "tafsir":
            return "tafsir"

        # Check if it's a Quran reference
        if source.get("surah") and source.get("ayah"):
            return "quran"

        # Check if it's a Hadith reference
        if "hadith" in title.lower() or "sahih" in author.lower():
            return "hadith"

        # Default to tafsir
        return "tafsir"

    def _format_reference(self, source: Dict[str, Any], citation_type: str, ayah_id: str) -> str:
        """Format reference string based on citation type."""
        if citation_type == "quran":
            return f"Quran {source.get('surah', '')}:{source.get('ayah', '')}"

        elif citation_type == "hadith":
            return f"{source.get('book', '')} {source.get('hadith_id', '')}: {source.get('grading', '')}"

        else:
            # Tafsir reference
            author = source.get("author", "Ibn Kathir")
            title = source.get("title", "")
            ayah_range = source.get("ayah_range")

            if title:
                reference = f"{author} - {title}"
            else:
                reference = f"{author} - Tafsir"
            if ayah_range:
                reference += f" (Ayah {ayah_range})"
            return reference

    def _extract_excerpt(self, source: Dict[str, Any]) -> str:
        """Extract excerpt from source with proper attribution."""
        excerpt = source.get("excerpt", "")

        if not excerpt:
            # Use thai translation as excerpt if available
            excerpt = source.get("thai_translation", "")

        if not excerpt:
            # Use original text as excerpt
            excerpt = source.get("original_text", "")

        # Truncate long excerpts
        if len(excerpt) > 500:
            excerpt = excerpt[:497] + "..."

        return excerpt.strip()

    def _determine_source_grade(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Determine source grade (evidence grade)."""
        source_grade = source.get("grading", "unknown")

        # Map to standardized grade format
        grade_mapping = {
            "sahih": {"level": "sahih", "confidence": 0.95},
            "hasan": {"level": "hasan", "confidence": 0.85},
            "daif": {"level": "daif", "confidence": 0.60},
            "maudu": {"level": "maudu", "confidence": 0.30},
            "unknown": {"level": "unknown", "confidence": 0.0}
        }

        return grade_mapping.get(source_grade, grade_mapping["unknown"])

    def _map_to_evidence_level(self, verified: bool) -> str:
        """Map source-text verification to the citation evidence level."""
        if verified:
            return "VERIFIED"

        return "UNVERIFIED"

    def _analyze_disagreement(self, sources: List[Dict[str, Any]]) -> str:
        """
        Analyze and format scholarly disagreement.

        Args:
            sources: List of sources to analyze

        Returns:
            Formatted disagreement analysis
        """
        if len(sources) <= 1:
            return "ไม่มีนักวิชาการให้ความเห็นแตกต่าง"

        # Analyze differences between sources
        disagreements = []

        for i, source1 in enumerate(sources):
            for j, source2 in enumerate(sources[i+1:], i+1):
                diff = self._compare_sources(source1, source2)
                if diff:
                    disagreements.append(diff)

        if not disagreements:
            return "นักวิชาการมีความเห็นคล้ายกัน"

        # Format disagreement analysis
        analysis = "นักวิชาการมีความเห็นแตกต่างดังนี้:\n\n"

        for i, disagreement in enumerate(disagreements, 1):
            analysis += f"{i}. {disagreement}\n\n"

        return analysis.strip()

    def _compare_sources(self, source1: Dict[str, Any], source2: Dict[str, Any]) -> str:
        """
        Compare two sources to identify disagreements.

        Args:
            source1: First source
            source2: Second source

        Returns:
            Description of disagreement, or empty string if no disagreement
        """
        # Compare key attributes
        author1 = source1.get("author", "")
        author2 = source2.get("author", "")

        if author1 == author2:
            return ""

        # Compare excerpts for substantive differences
        excerpt1 = source1.get("excerpt", "")
        excerpt2 = source2.get("excerpt", "")

        if excerpt1 and excerpt2:
            # Simple comparison - check for different key terms
            key_terms1 = set(self._extract_key_terms(excerpt1))
            key_terms2 = set(self._extract_key_terms(excerpt2))

            if key_terms1 and key_terms2:
                common_terms = key_terms1 & key_terms2
                if len(common_terms) < min(len(key_terms1), len(key_terms2)) * 0.3:
                    # Different key terms suggest disagreement
                    return f"{author1} vs {author2}: ความแตกต่างด้านศัพท์และการนำเสนอ"

        return ""

    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from text for comparison.

        Args:
            text: Text to analyze

        Returns:
            List of key terms
        """
        # Simple key term extraction
        # In practice, this would use NLP techniques
        words = re.findall(r'\b\w{4,}\b', text.lower())

        # Remove stop words
        stop_words = {"the", "and", "for", "are", "with", "that", "this", "from", "have", "has", "had", "been", "being", "will", "would", "could", "should", "may", "might", "can", "must", "shall", "ought", "their", "they", "them", "there", "then", "than", "when", "where", "why", "how", "what", "which", "who", "whom", "whose", "is", "in", "on", "at", "by", "to", "of", "a", "an", "the"}

        return [word for word in words if word not in stop_words]

    def _determine_evidence_level(self, sources: List[Dict[str, Any]]) -> str:
        """
        Determine overall evidence level for the response.

        Args:
            sources: List of sources used

        Returns:
            Evidence level string
        """
        if not sources:
            return "UNVERIFIED"

        verified = sum(1 for source in sources if source.get("verified", False))
        unverified = sum(1 for source in sources if not source.get("verified", False))

        if verified == len(sources):
            return "VERIFIED"

        elif verified > 0 and unverified / len(sources) <= 0.5:
            return "SOURCE-ATTRIBUTED"

        elif unverified > 0:
            return "UNVERIFIED"

        else:
            return "AI SYNTHESIS"

    def _calculate_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence level for the response.

        Args:
            sources: List of sources used

        Returns:
            Confidence level between 0 and 1
        """
        if not sources:
            return 0.0

        # Calculate average source confidence
        confidences = [source.get("relevance_score", 0.5) for source in sources]
        avg_confidence = sum(confidences) / len(confidences)

        # Adjust based on verification status
        verified_sources = sum(1 for source in sources if source.get("verified", False))
        verification_ratio = verified_sources / len(sources)

        # Weighted confidence
        confidence = (avg_confidence * 0.6) + (verification_ratio * 0.4)

        return min(1.0, max(0.0, confidence))

    def _determine_scholarly_position(self, sources: List[Dict[str, Any]]) -> str:
        """
        Determine scholarly position based on sources.

        Args:
            sources: List of sources

        Returns:
            Scholarly position description
        """
        if not sources:
            return "No available sources"

        # Analyze source characteristics
        scholars = set(source.get("author", "") for source in sources)

        if len(scholars) == 1:
            return f"Position of {list(scholars)[0]}"

        elif len(scholars) > 1:
            return "Comparative analysis across scholars"

        else:
            return "General Quranic interpretation"

    def _generate_methodology_notes(self, context: Dict[str, Any]) -> str:
        """
        Generate notes about methodology used.

        Args:
            context: Context information

        Returns:
            Methodology notes
        """
        methodology = context.get("methodology", "")

        if methodology == "ma'thur":
            return "คำอธิบายอ้างอิงจาก Quran, Hadith ที่เศาะฮีห์ และรายงานจากสะละฟุศศอลิห์"

        elif methodology == "ra'y":
            return "คำอธิบายอ้างอิงจากการวิเคราะห์ด้วยเหตุผล"

        elif methodology == "linguistic":
            return "คำอธิบายอ้างอิงจากการวิเคราะห์ภาษาอาหรับ"

        elif methodology == "legal":
            return "คำอธิบายอ้างอิงจากการวิเคราะห์ฟิกฮ์"

        elif methodology == "contemporary":
            return "คำอธิบายอ้างอิงจากมุมมองร่วมสมัย"

        else:
            return "คำอธิบายอ้างอิงจากหลายวิธีการ"

    def _identify_limitations(self, sources: List[Dict[str, Any]]) -> List[str]:
        """
        Identify limitations of the response.

        Args:
            sources: List of sources

        Returns:
            List of limitations
        """
        limitations = []

        # Check for lack of sources
        if not sources:
            limitations.append("No authentic sources found for this ayah")

        # Check for unverified sources
        unverified = [s for s in sources if not s.get("verified", False)]
        if unverified:
            limitations.append(f"{len(unverified)} sources require additional verification")

        # Check for quality issues
        low_quality = [s for s in sources if s.get("relevance_score", 1.0) < 0.5]
        if low_quality:
            limitations.append(f"{len(low_quality)} sources have low relevance")

        # Check for Isra'iliyyat reports
        isra_iliyyat = [s for s in sources if "isra" in str(s.get("excerpt", "")).lower()]
        if isra_iliyyat:
            limitations.append("Some sources contain Isra'iliyyat reports marked for caution")

        return limitations

    def _apply_template(self, template: str, explanation: str, citations: List[Dict[str, Any]],
                       disagreement_analysis: str, evidence_level: str) -> str:
        """
        Apply template to create final response.

        Args:
            template: Response template
            explanation: Generated explanation
            citations: Formatted citations
            disagreement_analysis: Disagreement analysis
            evidence_level: Evidence level

        Returns:
            Formatted response
        """
        response = template

        # Replace template variables
        response = response.replace("[[SOURCED_EXPLANATION]]", explanation)
        response = response.replace("[[CITATIONS]]", self._format_citation_list(citations))
        response = response.replace("[[SOURCED_EXPLANATIONS]]", explanation)
        response = response.replace("[[DISAGREEMENT_ANALYSIS]]", disagreement_analysis)
        response = response.replace("[[EVIDENCE_LEVEL]]", self.evidence_level_markers.get(evidence_level, evidence_level))
        response = response.replace("[[ERROR_DETAILS]]", explanation)

        return response

    def _format_citation_list(self, citations: List[Dict[str, Any]]) -> str:
        """
        Format citation list.

        Args:
            citations: List of citations

        Returns:
            Formatted citation list
        """
        if not citations:
            return "ไม่มีแหล่งข้อมูล"

        formatted = []

        for i, citation in enumerate(citations, 1):
            reference = citation.get("reference", "")
            excerpt = citation.get("excerpt", "")
            verified = citation.get("verified", False)
            evidence_level = citation.get("evidence_level", "UNVERIFIED")

            citation_line = f"{i}. {reference}"
            if verified:
                citation_line += " ✓"

            citation_line += f"\n{excerpt}"
            citation_line += f"\n*ระดับ: {self.evidence_level_markers.get(evidence_level, evidence_level)}*"

            formatted.append(citation_line)

        return "\n\n".join(formatted)

    def _create_fallback_response(self, ayah_id: str, error_message: str) -> Dict[str, Any]:
        """
        Create fallback response when formatting fails.

        Args:
            ayah_id: The ayah identifier
            error_message: Error message

        Returns:
            Fallback response
        """
        return {
            "explanation": f"เกิดข้อผิดพลาดในการแปลงผลลัพธ์: {error_message}",
            "citations": [],
            "confidence": 0.0,
            "scholarly_position": "Error in response formatting",
            "methodology_notes": "Quality gates failed or formatting error occurred",
            "limitations": ["Response formatting error", "Agent error"]
        }