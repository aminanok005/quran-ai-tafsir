import unittest

from policy import (
    APPROVED,
    DEVELOPMENT,
    DEVELOPMENT_ONLY,
    PRODUCTION,
    REJECTED,
    SUSPENDED,
    VERIFIED,
    SourcePermission,
    development_import_metadata,
    evaluate_source,
)


class IngestionPolicyTests(unittest.TestCase):
    def test_pending_rejected_and_suspended_sources_are_blocked(self):
        for status in ("pending", REJECTED, SUSPENDED):
            with self.subTest(status=status):
                decision = evaluate_source(SourcePermission("s1", "Example work", permission_status=status))
                self.assertFalse(decision.allowed)

    def test_development_only_allowed_only_in_development_mode(self):
        permission = SourcePermission("s1", "Example work", permission_status=DEVELOPMENT_ONLY)
        self.assertTrue(evaluate_source(permission, mode=DEVELOPMENT).allowed)
        production = evaluate_source(permission, mode=PRODUCTION)
        self.assertFalse(production.allowed)
        self.assertFalse(production.production_eligible)

    def test_approved_source_requires_all_explicit_metadata(self):
        base = dict(permission_status=APPROVED, verification_status=VERIFIED)
        for field in ("license", "source_url", "verification_evidence"):
            values = dict(base, license="MIT", source_url="https://example.invalid/source", verification_evidence="review-1")
            values[field] = None
            with self.subTest(field=field):
                self.assertFalse(evaluate_source(SourcePermission("s1", "Example work", **values)).allowed)

    def test_approved_verified_source_is_production_eligible(self):
        permission = SourcePermission(
            "s1", "Example work", permission_status=APPROVED,
            verification_status=VERIFIED, license="MIT",
            source_url="https://example.invalid/source", verification_evidence="review-1",
        )
        decision = evaluate_source(permission)
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.production_eligible)

    def test_policy_never_infers_mit(self):
        permission = SourcePermission(
            "s1", "Example work", permission_status=APPROVED,
            verification_status=VERIFIED, source_url="https://example.invalid/source",
            verification_evidence="review-1",
        )
        self.assertFalse(evaluate_source(permission).allowed)

    def test_development_metadata_preserves_status_and_provenance(self):
        permission = SourcePermission("s1", "Example work", permission_status=DEVELOPMENT_ONLY, source_url="https://example.invalid/source")
        metadata = development_import_metadata(permission)
        self.assertEqual(metadata["permission_status"], DEVELOPMENT_ONLY)
        self.assertEqual(metadata["verification_status"], "unverified")
        self.assertEqual(metadata["import_mode"], DEVELOPMENT)


if __name__ == "__main__":
    unittest.main()
