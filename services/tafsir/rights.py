"""Rights decisions required before exposing or training on source text."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .agents import DEFAULT_DATABASES, REPOSITORY_ROOT

REQUIRED_SOURCE_IDS = {
    f"qul:{Path(filename).stem}"
    for filename in [*DEFAULT_DATABASES.values(), "id-tafsir-as-saadi.db"]
}
ALLOWED_USES = {
    "display",
    "quotation",
    "storage",
    "indexing",
    "ai_processing",
    "model_training",
}
RUNTIME_USES = {"display", "quotation", "ai_processing"}


def _approved_record_issues(permission: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    if not isinstance(permission.get("license"), str) or not permission["license"].strip():
        issues.append("missing license")
    reviewer = permission.get("reviewed_by")
    if not isinstance(reviewer, str) or not reviewer.strip():
        issues.append("missing reviewer")
    reviewed_at = permission.get("reviewed_at")
    if not isinstance(reviewed_at, str) or not reviewed_at.strip():
        issues.append("missing review timestamp")
    else:
        try:
            timestamp = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                issues.append("review timestamp must include a timezone")
        except ValueError:
            issues.append("invalid review timestamp")

    evidence_refs = permission.get("evidence_refs")
    if (
        not isinstance(evidence_refs, list)
        or not evidence_refs
        or any(
            not isinstance(reference, str) or not reference.strip()
            for reference in evidence_refs
        )
    ):
        issues.append("missing evidence references")

    decision_note = permission.get("decision_note")
    if not isinstance(decision_note, str) or not decision_note.strip():
        issues.append("missing decision note")

    allowed_uses = permission.get("allowed_uses")
    if (
        not isinstance(allowed_uses, list)
        or not allowed_uses
        or any(not isinstance(use, str) or use not in ALLOWED_USES for use in allowed_uses)
    ):
        issues.append("allowed_uses contains an invalid value")
    return issues


def permission_allows(permission: Dict[str, Any], uses: Iterable[str]) -> bool:
    if permission.get("status") != "approved" or _approved_record_issues(permission):
        return False
    requested_uses = set(uses)
    return (
        requested_uses <= ALLOWED_USES
        and requested_uses <= set(permission["allowed_uses"])
    )


def validate_rights_manifest_structure(manifest: Dict[str, Any]) -> List[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sources"), dict):
        return ["manifest must contain a sources object"]
    sources = manifest["sources"]
    issues: List[str] = []
    if "schema_version" in manifest and manifest["schema_version"] != 1:
        issues.append("unsupported schema_version")
    for source_id in sources:
        if source_id not in REQUIRED_SOURCE_IDS:
            issues.append(f"{source_id}: unknown source ID")
    for source_id, permission in sources.items():
        if not isinstance(permission, dict):
            issues.append(f"{source_id}: source record must be an object")
        elif permission.get("status") not in {"approved", "pending", "rejected", "unknown"}:
            issues.append(f"{source_id}: invalid status {permission.get('status')!r}")
    return issues


def validate_rights_manifest(
    manifest: Dict[str, Any], require_all_sources: bool = True
) -> List[str]:
    structure_issues = validate_rights_manifest_structure(manifest)
    if structure_issues:
        return structure_issues
    sources = manifest["sources"]
    issues: List[str] = []
    for source_id in sorted(REQUIRED_SOURCE_IDS):
        permission = sources.get(source_id)
        if permission is None:
            if require_all_sources:
                issues.append(f"{source_id}: missing source record")
            continue
        status = permission.get("status")
        if status != "approved":
            issues.append(f"{source_id}: status is {status}")
            continue
        issues.extend(
            f"{source_id}: {issue}" for issue in _approved_record_issues(permission)
        )
    return issues


def load_rights_manifest() -> Dict[str, Any]:
    path = Path(
        os.environ.get(
            "TAFSIR_RIGHTS_MANIFEST",
            REPOSITORY_ROOT / "data-tafsir" / "rights-manifest.json",
        )
    ).expanduser()
    if not path.is_file():
        return {"sources": {}}
    with path.open(encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)
    issues = validate_rights_manifest_structure(manifest)
    if issues:
        raise ValueError(f"Invalid tafsir rights manifest {path}: {'; '.join(issues)}")
    return manifest


def source_permission(source_id: str) -> Dict[str, Any]:
    permission = load_rights_manifest()["sources"].get(source_id, {})
    if not isinstance(permission, dict):
        raise ValueError(f"Invalid source record in tafsir rights manifest: {source_id}")
    return permission


def source_allows(source_id: str, uses: Iterable[str]) -> bool:
    return permission_allows(source_permission(source_id), uses)
