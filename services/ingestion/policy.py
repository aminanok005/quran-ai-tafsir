"""Pure source-rights policy for ingestion.

No network or database access. Rights and verification remain separate.
"""

from dataclasses import dataclass
from typing import Optional

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
SUSPENDED = "suspended"
DEVELOPMENT_ONLY = "development_only"
VERIFIED = "verified"
UNVERIFIED = "unverified"
PRODUCTION = "production"
DEVELOPMENT = "development"


@dataclass(frozen=True)
class SourcePermission:
    source_id: str
    work_title: str
    permission_status: str = PENDING
    verification_status: str = UNVERIFIED
    license: Optional[str] = None
    source_url: Optional[str] = None
    verification_evidence: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class IngestionDecision:
    allowed: bool
    reason: str
    production_eligible: bool = False


def evaluate_source(
    permission: SourcePermission,
    *,
    mode: str = PRODUCTION,
) -> IngestionDecision:
    """Evaluate explicit source permission for production or development use."""
    if mode not in {PRODUCTION, DEVELOPMENT}:
        return IngestionDecision(False, f"unsupported ingestion mode: {mode}")
    if permission.permission_status == DEVELOPMENT_ONLY:
        if mode == DEVELOPMENT:
            return IngestionDecision(
                True,
                "development-only source allowed for research/test mode",
                production_eligible=False,
            )
        return IngestionDecision(False, "development-only source is not production eligible")
    if permission.permission_status in {PENDING, REJECTED, SUSPENDED}:
        return IngestionDecision(
            False,
            f"source permission status is {permission.permission_status}",
        )
    if permission.permission_status != APPROVED:
        return IngestionDecision(False, "source permission status is unknown")
    if permission.verification_status != VERIFIED:
        return IngestionDecision(False, "source verification evidence is missing or unverified")
    if not permission.verification_evidence:
        return IngestionDecision(False, "source verification evidence is missing")
    if not permission.license:
        return IngestionDecision(False, "source license is missing")
    if not permission.source_url:
        return IngestionDecision(False, "source URL is missing")
    return IngestionDecision(True, "source permission approved and verified", production_eligible=True)


def development_import_metadata(permission: SourcePermission) -> dict[str, str]:
    """Return explicit provenance fields for development-only imports."""
    return {
        "source_id": permission.source_id,
        "source_url": permission.source_url or "",
        "permission_status": permission.permission_status,
        "verification_status": permission.verification_status,
        "import_mode": DEVELOPMENT,
    }
