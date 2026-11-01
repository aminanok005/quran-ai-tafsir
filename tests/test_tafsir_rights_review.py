import json

import pytest

from services.tafsir.rights import permission_allows, source_allows
from services.tafsir.rights_review import record_decision

SOURCE_ID = "qul:ar-tafsir-ibn-kathir"


def test_recording_approval_requires_evidence_and_decision_details(tmp_path):
    with pytest.raises(ValueError, match="evidence reference"):
        record_decision(
            path=tmp_path / "rights.json",
            source_id=SOURCE_ID,
            status="approved",
            reviewer="reviewer",
            decision_note="Reviewed the source license",
            evidence_refs=[],
            license_name="Example license",
            allowed_uses=["display", "quotation", "ai_processing"],
        )


def test_approval_is_source_specific_scoped_and_auditable(tmp_path, monkeypatch):
    manifest_path = tmp_path / "rights.json"
    approval = record_decision(
        path=manifest_path,
        source_id=SOURCE_ID,
        status="approved",
        reviewer="reviewer-1",
        decision_note="Approved local corpus storage and indexing only",
        evidence_refs=["docs/license-review.pdf#page=2"],
        license_name="Example license",
        allowed_uses=["storage", "indexing"],
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(manifest_path))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    permission = manifest["sources"][SOURCE_ID]
    assert approval["status"] == "approved"
    assert len(permission["review_history"]) == 1
    assert permission["reviewed_by"] == "reviewer-1"
    assert permission["evidence_refs"] == ["docs/license-review.pdf#page=2"]
    assert permission_allows(permission, ["storage", "indexing"])
    assert not permission_allows(permission, ["display", "ai_processing"])
    assert not source_allows(SOURCE_ID, ["display", "quotation", "ai_processing"])

    record_decision(
        path=manifest_path,
        source_id=SOURCE_ID,
        status="rejected",
        reviewer="reviewer-2",
        decision_note="Evidence does not authorize public display",
        evidence_refs=["docs/license-review.pdf#page=3"],
    )
    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(updated["sources"][SOURCE_ID]["review_history"]) == 2
    assert not source_allows(SOURCE_ID, ["storage"])


def test_runtime_rights_require_timestamp_evidence_and_full_use_scope(tmp_path, monkeypatch):
    manifest_path = tmp_path / "rights.json"
    manifest_path.write_text(
        json.dumps(
            {
                "sources": {
                    SOURCE_ID: {
                        "status": "approved",
                        "license": "Example license",
                        "allowed_uses": ["display", "quotation", "ai_processing"],
                        "reviewed_by": "reviewer",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TAFSIR_RIGHTS_MANIFEST", str(manifest_path))

    assert not source_allows(SOURCE_ID, ["display", "quotation", "ai_processing"])


def test_optional_surah_background_source_can_be_display_only(tmp_path):
    source_id = "qul:surah-info-id"
    manifest_path = tmp_path / "rights.json"
    approval = record_decision(
        path=manifest_path,
        source_id=source_id,
        status="approved",
        reviewer="reviewer-1",
        decision_note="Approved reader display only",
        evidence_refs=["docs/surah-info-permission.pdf"],
        license_name="Example license",
        allowed_uses=["display"],
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    permission = manifest["sources"][source_id]

    assert approval["allowed_uses"] == ["display"]
    assert permission_allows(permission, ["display"])
    assert not permission_allows(permission, ["quotation", "ai_processing"])
