"""
Citation Validator for Ibn Kathir Agent

Validates authenticity and reliability of sources from Ibn Kathir's tafsir.
Implements the evidence validation required for source-grounded AI.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from enum import Enum

from ....shared_types import EvidenceGrade, ValidationIssue, SourceQualityReport

logger = logging.getLogger(__name__)

class ValidationResult:
    """Result of citation validation."""

    def __init__(self, is_valid: bool, issues: List[ValidationIssue],
                 confidence: float, recommendations: List[str] = None):
        self.is_valid = is_valid
        self.issues = issues
        self.confidence = confidence
        self.recommendations = recommendations or []

        # Calculate overall validation score
        self.overall_score = self._calculate_score()

    def _calculate_score(self) -> float:
        """Calculate overall validation score."""
        if not self.is_valid:
            return 0.0

        # Base score on confidence and issue count
        score = self.confidence

        # Deduct for issues
        critical_issues = len([i for i in self.issues if i.severity == "CRITICAL"])
        high_issues = len([i for i in self.issues if i.severity == "HIGH"])
        medium_issues = len([i for i in self.issues if i.severity == "MEDIUM"])

        score -= critical_issues * 0.3
        score -= high_issues * 0.2
        score -= medium_issues * 0.1

        # Clamp to 0-1 range
        return max(0.0, min(1.0, score))
class CitationValidator:
    """
    Validates citations for authenticity and reliability.

    This class implements validation for the Ibn Kathir agent, checking:
    - Source authenticity and verification status
    - Evidence grading (Sahih, Hasan, Daif, Maud)
    - Source licensing and permissions
    - Citation completeness and accuracy
    - Scholarly attribution
    """

    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.source_database = {}
        self.license_checker = LicenseChecker()
        self.quality_assessor = QualityAssessor()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for different source types."""
        return {
            "tafsir_sources": {
                "required_fields": ["source_id", "author", "title", "text"],
                "mandatory_verification": True,
                "grade_requirement": "sahih",  # Minimum acceptable grade
                "max_unverified_quotes": 2,
                "isra'iliyyat_warning_required": True
            },
            "hadith_sources": {
                "required_fields": ["source_id", "book", "hadith_id", "text"],
                "mandatory_verification": True,
                "grade_requirement": "sahih",
                "max_unverified_reports": 1,
                "chain_verification_required": True
            },
            "scholarly_reports": {
                "required_fields": ["scholar", "book", "chapter", "text"],
                "mandatory_verification": False,
                "grade_requirement": "none",
                "max_unverified_sources": 5
            },
            "multiple_authors": {
                "disagreement_alert": True,
                "source_disclosure_required": True,
                "attribution_standard": "standard"
            }
        }

    async def validate(self, source_id: str, author: str, title: str,
                      excerpt: str, source_type: str = "tafsir") -> tuple[bool, ValidationResult]:
        """
        Validate a source citation.

        Args:
            source_id: Unique identifier for the source
            author: Author of the source
            title: Title of the source
            excerpt: Text excerpt from the source
            source_type: Type of source (tafsir, hadith, scholarly)

        Returns:
            Tuple of (is_valid, validation_result)
        """
        try:
            # Initialize validation result
            issues = []
            confidence = 1.0
            recommendations = []

            # Apply validation rules based on source type
            rule_set = self.validation_rules.get(source_type, self.validation_rules["scholarly_sources"])

            # Check required fields
            validation_issues = await self._check_required_fields(
                source_id, author, title, excerpt, rule_set
            )
            issues.extend(validation_issues)

            # Validate source authenticity
            auth_issues = await self._validate_source_authenticity(
                source_id, author, title, rule_set
            )
            issues.extend(auth_issues)

            # Check excerpt authenticity
            excerpt_issues = await self._validate_excerpt(
                excerpt, source_id, rule_set
            )
            issues.extend(excerpt_issues)

            # Check licensing and permissions
            license_issues = await self.license_checker.check_source(source_id)
            issues.extend(license_issues)

            # Assess source quality
            quality_report = await self.quality_assessor.assess(source_id, author, title)
            if quality_report.issues:
                issues.extend(quality_report.issues)
                confidence *= (1.0 - quality_report.overall_score)

            # Determine overall validity
            is_valid = self._determine_validity(issues, rule_set, confidence)

            # Add recommendations based on issues
            if issues:
                recommendations.extend(self._generate_recommendations(issues))

            # Create validation result
            result = ValidationResult(
                is_valid=is_valid,
                issues=issues,
                confidence=confidence,
                recommendations=recommendations
            )

            logger.debug(
                f"Citation validation for {source_id}: valid={is_valid}, "
                f"confidence={confidence:.2f}, issues={len(issues)}"
            )

            return is_valid, result

        except Exception as e:
            logger.error(f"Citation validation error: {str(e)}")
            return False, ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    type="VALIDATION_ERROR",
                    severity="CRITICAL",
                    description=f"Validation system error: {str(e)}",
                    location=source_id
                )],
                confidence=0.0,
                recommendations=["Contact system administrator"]
            )

    async def _check_required_fields(self, source_id: str, author: str, title: str,
                                   excerpt: str, rule_set: Dict[str, Any]) -> List[ValidationIssue]:
        """Check if source has required fields."""
        issues = []

        required_fields = rule_set.get("required_fields", [])
        field_values = {
            "source_id": source_id,
            "author": author,
            "title": title,
            "excerpt": excerpt
        }

        for field in required_fields:
            if field in field_values:
                value = field_values[field]
                if not value or (isinstance(value, str) and not value.strip()):
                    issues.append(ValidationIssue(
                        type="MISSING_REQUIRED_FIELD",
                        severity="MEDIUM",
                        description=f"Missing or empty required field: {field}",
                        location=source_id,
                        suggested_fix=f"Add {field} to source metadata"
                    ))

        return issues

    async def _validate_source_authenticity(self, source_id: str, author: str, title: str,
                                           rule_set: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate source authenticity and verification."""
        issues = []

        # Check if source exists in database
        if source_id not in self.source_database:
            issues.append(ValidationIssue(
                type="UNKNOWN_SOURCE",
                severity="HIGH",
                description=f"Source ID {source_id} not found in database",
                location=source_id,
                suggested_fix="Verify source ID or add to source registry"
            ))
            return issues

        source = self.source_database[source_id]

        # Check verification status
        if rule_set.get("mandatory_verification", False):
            if not source.get("verified", False):
                issues.append(ValidationIssue(
                    type="UNVERIFIED_SOURCE",
                    severity="HIGH",
                    description=f"Source {source_id} is not verified",
                    location=source_id,
                    suggested_fix="Obtain verification from qualified scholar or source registry"
                ))

        # Check minimum quality grade
        min_grade = rule_set.get("grade_requirement", "none")
        if min_grade != "none":
            source_grade = source.get("grade", "unknown")
            grade_hierarchy = {"sahih": 4, "hasan": 3, "daif": 2, "maudu": 1}

            if source_grade in grade_hierarchy:
                if grade_hierarchy[source_grade] < grade_hierarchy.get(min_grade, 0):
                    issues.append(ValidationIssue(
                        type="INSUFFICIENT_GRADE",
                        severity="MEDIUM",
                        description=f"Source grade {source_grade} does not meet minimum requirement {min_grade}",
                        location=source_id,
                        suggested_fix=f"Replace with source of grade {min_grade} or higher"
                    ))

        return issues

    async def _validate_excerpt(self, excerpt: str, source_id: str,
                               rule_set: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate excerpt authenticity and format."""
        issues = []

        if not excerpt:
            issues.append(ValidationIssue(
                type="EMPTY_EXCERPT",
                severity="MEDIUM",
                description="Excerpt text is empty",
                location=source_id,
                suggested_fix="Provide meaningful excerpt from source"
            ))
            return issues

        # Check excerpt length
        if len(excerpt.strip()) < 10:
            issues.append(ValidationIssue(
                type="EXCERPT_TOO_SHORT",
                severity="LOW",
                description="Excerpt is too short to be meaningful",
                location=source_id,
                suggested_fix="Provide longer excerpt (at least 10 characters)"
            ))

        # Check for obvious fabrication indicators
        fabrication_indicators = [
            "fabricated", "fake", "made up", "invented", "fictional",
            "not in the book", "never written", "does not exist"
        ]

        excerpt_lower = excerpt.lower()
        for indicator in fabrication_indicators:
            if indicator in excerpt_lower:
                issues.append(ValidationIssue(
                    type="FABRICATION_INDICATOR",
                    severity="CRITICAL",
                    description="Excerpt contains indicators of fabrication",
                    location=source_id,
                    suggested_fix="Remove fabricated content and use authentic source"
                ))
                break

        # Check for source attribution
        if rule_set.get("isra'iliyyat_warning_required", False):
            isra_iliyyat_indicators = [
                "isra'iliyyat", "israiliyyat", "jewish story", "persian story",
                "greek myth", "hindu story", "buddhist teaching"
            ]

            for indicator in isra_iliyyat_indicators:
                if indicator in excerpt_lower:
                    issues.append(ValidationIssue(
                        type="ISRAILIYAT_REPORT",
                        severity="MEDIUM",
                        description="Excerpt appears to contain Isra'iliyyat reports",
                        location=source_id,
                        suggested_fix="Mark as Isra'iliyyat with appropriate warning"
                    ))
                    break

        return issues

    def _determine_validity(self, issues: List[ValidationIssue],
                          rule_set: Dict[str, Any], confidence: float) -> bool:
        """Determine if source is valid based on issues and confidence."""
        if not issues:
            return True

        # Check for critical issues
        critical_issues = [i for i in issues if i.severity == "CRITICAL"]
        if critical_issues:
            return False

        # Check high severity issues against limits
        high_issues = [i for i in issues if i.severity == "HIGH"]
        max_high_issues = rule_set.get("max_unverified_quotes", 2) + rule_set.get("max_unverified_sources", 5)

        if len(high_issues) > max_high_issues:
            return False

        # Check if confidence is below minimum threshold
        min_confidence = 0.3  # 30% minimum confidence
        if confidence < min_confidence:
            return False

        # Overall validity check
        return True

    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate recommendations based on validation issues."""
        recommendations = []

        issue_types = set(issue.type for issue in issues)

        if "UNKNOWN_SOURCE" in issue_types:
            recommendations.append("Add source to registry or verify source ID")

        if "UNVERIFIED_SOURCE" in issue_types:
            recommendations.append("Obtain source verification from qualified scholar")

        if "INSUFFICIENT_GRADE" in issue_types:
            recommendations.append("Replace with source of higher quality grade")

        if "FABRICATION_INDICATOR" in issue_types:
            recommendations.append("Remove fabricated content and consult authentic sources")

        if "EMPTY_EXCERPT" in issue_types:
            recommendations.append("Provide meaningful excerpt from source")

        return recommendations
class LicenseChecker:
    """Checks source licensing and permissions."""

    def __init__(self):
        self.license_database = {}

    async def check_source(self, source_id: str) -> List[ValidationIssue]:
        """Check if source has proper licensing for use."""
        issues = []

        if source_id not in self.license_database:
            issues.append(ValidationIssue(
                type="MISSING_LICENSE_INFO",
                severity="HIGH",
                description="Source license information not available",
                location=source_id,
                suggested_fix="Add license information to source registry"
            ))
            return issues

        license_info = self.license_database[source_id]

        # Check if source is licensed for AI processing
        allowed_uses = license_info.get("allowed_uses", [])
        required_uses = ["display", "quotation", "indexing", "AI processing"]

        for use in required_uses:
            if use not in allowed_uses:
                issues.append(ValidationIssue(
                    type="LICENSE_RESTRICTION",
                    severity="MEDIUM",
                    description=f"Source not licensed for {use}",
                    location=source_id,
                    suggested_fix=f"Obtain license for {use} or use different source"
                ))

        # Check if license has expired
        expires_at = license_info.get("expires_at")
        if expires_at:
            from datetime import datetime
            if datetime.now() > datetime.fromisoformat(expires_at):
                issues.append(ValidationIssue(
                    type="EXPIRED_LICENSE",
                    severity="HIGH",
                    description="Source license has expired",
                    location=source_id,
                    suggested_fix="Renew source license or find alternative source"
                ))

        return issues
class QualityAssessor:
    """Assesses source quality and reliability."""

    def __init__(self):
        self.quality_metrics = {}

    async def assess(self, source_id: str, author: str, title: str) -> SourceQualityReport:
        """Assess source quality and return report."""
        # Mock implementation - would use actual quality assessment metrics
        # In reality, this would analyze source completeness, accuracy, etc.

        return SourceQualityReport(
            source_id=source_id,
            integrity_score=0.95,
            completeness_score=0.90,
            accuracy_score=0.98,
            issues=[],
            last_verified="2024-01-15",
            reviewer="System",
            overall_score=0.94
        )