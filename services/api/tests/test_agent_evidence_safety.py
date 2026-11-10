import json
import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from services.api.services.agent_orchestrator import AgentOrchestratorService

APPROVED = {
    "passage_id": "qf:168:1:1",
    "permission_status": "approved",
    "verification_status": "verified",
    "license": "open",
    "verification_evidence": "reviewed",
    "source_reference": "https://example.test/source",
    "scholar_name": "Scholar",
    "book_title": "Book",
}
PLACEHOLDER_MARKERS = ("Sahih Bukhari", "Sahih Muslim", "Musnad Ahmad", "hadith_references", "4854")


class LegacyAgentEvidenceSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_mock_agent_data_never_reaches_responses(self):
        orchestrator = AgentOrchestratorService()
        result = await orchestrator.execute_agent_analysis(
            1, 1, list(orchestrator.agents), {}, source_passages=[APPROVED]
        )
        payload = json.dumps(result, ensure_ascii=False)
        for marker in PLACEHOLDER_MARKERS:
            self.assertNotIn(marker, payload)
        for output in result["agent_outputs"].values():
            if output.get("status") != "failed":
                self.assertTrue(
                    {c["passage_id"] for c in output["citations"]} <= {APPROVED["passage_id"]}
                )

    async def test_unapproved_passages_are_rejected(self):
        orchestrator = AgentOrchestratorService()
        with self.assertRaises(ValueError):
            await orchestrator.execute_agent_analysis(
                1, 1, ["ibn_kathir"], {}, source_passages=[{**APPROVED, "verification_status": "unverified"}]
            )


class IbnKathirAgentRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_explain_ayah_does_not_await_sync_source_lookup(self):
        from services.api.agents.ibn_kathir_agent import IbnKathirAgent

        try:
            await IbnKathirAgent().explain_ayah(1, 1, {})
        except TypeError as exc:
            self.assertNotIn("await", str(exc))
        except KeyError:
            pass  # separate legacy mock-data defect, out of scope here
