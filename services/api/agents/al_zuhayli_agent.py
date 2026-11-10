"""
Wahbah Al-Zuhayli Agent - Contemporary comparative fiqh (Al-Tafsir al-Munir)

According to Al-Tafsir al-Munir (Wahbah Al-Zuhayli)
Specializes in contemporary comparative jurisprudence and societal applications.
"""

from typing import Dict, List, Any
from datetime import datetime
from .base_agent import BaseTafsirAgent

class AlZuhayliAgent(BaseTafsirAgent):
    """
    Al-Zuhayli Tafsir Agent - Contemporary comparative jurisprudence specialist.
    
    Methodology: contemporary (contemporary comparative fiqh)
    Focus: Contemporary comparative jurisprudence, societal applications, modern context
    Evidence: Qur'an, contemporary fiqh, contemporary scholarly consensus, modern applications
    """
    
    def __init__(self):
        super().__init__(
            agent_type="al_zuhayli",
            scholar_name="Wahbah Al-Zuhayli",
            methodology="contemporary"  # Contemporary comparative fiqh
        )
        self.source_collection = "al_zuhayli_tafsir_munir_vol5"
        self.scholarly_position = "Contemporary comparative fiqh specialist"
        self.key_features = [
            "Contemporary comparative fiqh",
            "Modern societal applications",
            "Religious tolerance and coexistence",
            "Universal message relevance",
            "Contemporary challenges and solutions"
        ]
    

    def _retrieve_al_zuhayli_sources(self, surah: int, ayah: int) -> List[Dict[str, Any]]:
        """
        Retrieve sources from Al-Zuhayli's Al-Tafsir al-Munir.
        
        Simulates database query from Al-Zuhayli's work (Vol 5, p. 234)
        """
        
        # Mock data representing Al-Zuhayli's Al-Tafsir al-Munir
        # Placeholder data removed: no source is returned until real, approved
        # passages are wired in. Fabricated tafsir/hadith must never be served.
        return []
    
    def _validate_al_zuhayli_explanation(
        self, 
        explanation: Dict[str, Any], 
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate Al-Zuhayli's explanation for contemporary relevance and accuracy.
        """
        
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "confidence_score": 0.0,
            "issues": []
        }
        
        # Check for contemporary relevance
        if not any("contemporary" in k.lower() for k in explanation.get("key_points", [])):
            validation["warnings"].append("Lacks contemporary relevance indicators")
            validation["valid"] = False
        
        # Check for contemporary references
        if "modern" not in explanation.get("key_points", []):
            validation["warnings"].append("Lacks contemporary application references")
        
        # Check for contemporary references in citations
        if not any("modern" in citation.get("excerpt", "").lower() for citation in explanation.get("citations", [])):
            validation["warnings"].append("Lacks contemporary application references")
            validation["valid"] = False
        
        # Calculate confidence score
        confidence = 0.85
        if "contemporary" in explanation.get("key_points", []):
            confidence *= 1.0
        if "contemporary" in explanation.get("analysis", "").lower():
            confidence *= 1.0
        if "modern" in explanation.get("analysis", "").lower():
            confidence *= 1.0
        if "modern" in explanation.get("key_points", []):
            confidence *= 1.0
        
        validation["confidence_score"] = confidence
        
        return validation
    
    def _classify_al_zuhayli_evidence(
        self, 
        explanation: Dict[str, Any], 
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        Classify evidence level for Al-Zuhayli's explanation.
        """
        
        # Check if we have verified sources
        verified_sources = [s for s in sources if s.get("verification_status") == "verified"]
        if verified_sources:
            return "VERIFIED"
        
        # Check if sources are properly attributed
        attributed_sources = [s for s in sources if s.get("source_url")]
        if attributed_sources:
            return "SOURCE-ATTRIBUTED"
        
        # Check if explanation contains contemporary references
        if any("contemporary" in k.lower() for k in explanation.get("key_points", [])):
            return "SOURCE-ATTRIBUTED"
        
        return "AI-SYNTHESIS"