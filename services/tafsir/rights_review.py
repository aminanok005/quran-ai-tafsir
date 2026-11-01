"""Local, auditable operator workflow for source-specific tafsir rights reviews."""

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agents import DEFAULT_DATABASES, REPOSITORY_ROOT
from .rights import (
    ALLOWED_USES,
    KNOWN_SOURCE_IDS,
    OPTIONAL_SOURCE_IDS,
    REQUIRED_SOURCE_IDS,
    RUNTIME_USES,
    permission_allows,
    validate_rights_manifest,
    validate_rights_manifest_structure,
)

DEFAULT_MANIFEST = REPOSITORY_ROOT / "data-tafsir" / "rights-manifest.json"
DECISIONS = {"approved", "pending", "rejected"}


def _empty_manifest() -> Dict[str, Any]:
    dataset_files = [
        *DEFAULT_DATABASES.values(),
        "id-tafsir-as-saadi.db",
        "surah-info-id.json",
        "qpc-v4-tajweed-15-lines.db",
    ]
    return {
        "schema_version": 1,
        "sources": {
            f"qul:{Path(filename).stem}": {
                "status": "pending",
                "license": None,
                "allowed_uses": [],
                "reviewed_by": None,
                "reviewed_at": None,
                "evidence_refs": [],
                "decision_note": None,
                "review_history": [],
            }
            for filename in dataset_files
        },
    }


def _read_manifest(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return _empty_manifest()
    with path.open(encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)
    issues = validate_rights_manifest_structure(manifest)
    if issues:
        raise ValueError(f"Invalid rights manifest {path}: {'; '.join(issues)}")
    return manifest


def record_decision(
    path: Path,
    source_id: str,
    status: str,
    reviewer: str,
    decision_note: str,
    evidence_refs: List[str],
    license_name: Optional[str] = None,
    allowed_uses: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if source_id not in KNOWN_SOURCE_IDS:
        raise ValueError(f"Unknown tafsir source: {source_id}")
    if status not in DECISIONS:
        raise ValueError(f"status must be one of {sorted(DECISIONS)}")
    if not reviewer.strip():
        raise ValueError("reviewer must not be empty")
    if not decision_note.strip():
        raise ValueError("decision note must not be empty")
    if not evidence_refs or any(not reference.strip() for reference in evidence_refs):
        raise ValueError("at least one non-empty evidence reference is required")

    uses = allowed_uses or []
    if any(use not in ALLOWED_USES for use in uses):
        raise ValueError(f"allowed uses must be selected from {sorted(ALLOWED_USES)}")
    if status == "approved":
        if not license_name or not license_name.strip():
            raise ValueError("approved decisions require a license name or identifier")
        if not uses:
            raise ValueError("approved decisions must explicitly grant at least one use")
    elif uses:
        raise ValueError("only approved decisions may grant allowed uses")

    manifest = _read_manifest(path)
    sources = manifest["sources"]
    for required_source in KNOWN_SOURCE_IDS:
        sources.setdefault(required_source, _empty_manifest()["sources"][required_source])

    permission = sources.get(source_id)
    if not isinstance(permission, dict):
        raise ValueError(f"Invalid source record for {source_id}")
    history = permission.get("review_history", [])
    if not isinstance(history, list):
        raise ValueError(f"Invalid review history for {source_id}")

    reviewed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    decision = {
        "status": status,
        "license": license_name.strip() if license_name and license_name.strip() else None,
        "allowed_uses": sorted(set(uses)),
        "reviewed_by": reviewer.strip(),
        "reviewed_at": reviewed_at,
        "evidence_refs": [reference.strip() for reference in evidence_refs],
        "decision_note": decision_note.strip(),
    }
    permission.update(decision)
    permission["review_history"] = [*history, decision.copy()]
    manifest["schema_version"] = 1

    issues = validate_rights_manifest(manifest)
    if status == "approved":
        source_issues = [issue for issue in issues if issue.startswith(f"{source_id}:")]
        if source_issues:
            raise ValueError(f"Rights approval is incomplete: {'; '.join(source_issues)}")

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        json.dump(manifest, temporary_file, ensure_ascii=False, indent=2)
        temporary_file.write("\n")
    os.replace(temporary_path, path)
    return decision


def _status_report(path: Path, require_runtime: bool = False) -> int:
    manifest = _read_manifest(path)
    sources = manifest.get("sources", {})
    problems = validate_rights_manifest(manifest)
    for source_id in sorted(KNOWN_SOURCE_IDS):
        permission = sources.get(source_id, {})
        status = permission.get("status", "missing") if isinstance(permission, dict) else "invalid"
        print(f"{source_id}: {status}")
        if source_id in OPTIONAL_SOURCE_IDS:
            if isinstance(permission, dict) and permission_allows(permission, ["display"]):
                print("  Runtime: eligible for display")
            else:
                print("  Runtime: blocked until display permission is reviewed")
            continue
        if status != "approved":
            print("  Runtime: blocked until reviewed and approved")
        elif permission_allows(permission, RUNTIME_USES):
            print("  Runtime: eligible for display, quotation, and AI processing")
        else:
            allowed = permission.get("allowed_uses", [])
            print(f"  Runtime: blocked; approved uses are {allowed}")
            if require_runtime:
                problems.append(f"{source_id}: missing complete runtime permissions")

    for issue in problems:
        print(f"BLOCKED: {issue}")
    return 1 if problems else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Show approval state and missing requirements")
    subparsers.add_parser(
        "validate",
        help="Fail unless all required tafsir corpora pass the runtime approval gate",
    )
    record_parser = subparsers.add_parser("record", help="Record a human source-specific decision")
    record_parser.add_argument("source_id", choices=sorted(REQUIRED_SOURCE_IDS))
    record_parser.add_argument("--status", choices=sorted(DECISIONS), required=True)
    record_parser.add_argument("--reviewed-by", required=True)
    record_parser.add_argument("--decision-note", required=True)
    record_parser.add_argument("--evidence-ref", action="append", required=True)
    record_parser.add_argument("--license")
    record_parser.add_argument("--allow", action="append", choices=sorted(ALLOWED_USES), default=[])
    args = parser.parse_args(argv)

    if args.command in {"status", "validate"}:
        return _status_report(args.manifest, require_runtime=args.command == "validate")

    decision = record_decision(
        path=args.manifest,
        source_id=args.source_id,
        status=args.status,
        reviewer=args.reviewed_by,
        decision_note=args.decision_note,
        evidence_refs=args.evidence_ref,
        license_name=args.license,
        allowed_uses=args.allow,
    )
    print(
        f"Recorded {decision['status']} decision for {args.source_id} "
        f"by {decision['reviewed_by']} at {decision['reviewed_at']}."
    )
    print("This records a human attestation; it is not a legal determination.")
    if decision["status"] != "approved":
        print("Runtime access remains blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
