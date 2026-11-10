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


class PlaceholderRetrieversReturnNothingTests(unittest.TestCase):
    def test_legacy_retrievers_never_return_placeholder_sources(self):
        from services.api.agents.al_qurtubi_agent import AlQurtubiAgent
        from services.api.agents.al_saadi_agent import AlSaadiAgent
        from services.api.agents.al_tabari_agent import AlTabariAgent
        from services.api.agents.al_zuhayli_agent import AlZuhayliAgent
        from services.api.agents.ibn_ashur_agent import IbnAshurAgent
        from services.api.agents.ibn_kathir_agent import IbnKathirAgent

        for agent, name in [
            (AlQurtubiAgent(), "al_qurtubi"),
            (AlSaadiAgent(), "al_saadi"),
            (AlTabariAgent(), "al_tabari"),
            (AlZuhayliAgent(), "al_zuhayli"),
            (IbnAshurAgent(), "ibn_ashur"),
            (IbnKathirAgent(), "ibn_kathir"),
        ]:
            self.assertEqual(getattr(agent, f"_retrieve_{name}_sources")(1, 1), [], name)


class GroundedAgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_each_agent_returns_only_its_own_approved_passage_verbatim(self):
        orchestrator = AgentOrchestratorService()
        passages = [
            {**APPROVED, "passage_id": f"qf:{i}:1:1", "scholar_id": agent, "arabic_text": f"نص {agent}"}
            for i, agent in enumerate(orchestrator.agents)
        ]
        result = await orchestrator.execute_agent_analysis(
            1, 1, list(orchestrator.agents), {}, source_passages=passages
        )
        self.assertEqual(sorted(result["agents_executed"]), sorted(orchestrator.agents))
        for agent, output in result["agent_outputs"].items():
            self.assertEqual(output["explanation"], f"نص {agent}")
            self.assertEqual(len(output["citations"]), 1)
            self.assertEqual(output["citations"][0]["evidence_status"], "VERIFIED")

    async def test_agent_without_its_own_passage_fails_closed(self):
        orchestrator = AgentOrchestratorService()
        result = await orchestrator.execute_agent_analysis(
            1, 1, ["al_tabari"], {}, source_passages=[{**APPROVED, "scholar_id": "ibn_kathir", "arabic_text": "x"}]
        )
        self.assertEqual(result["agents_executed"], [])


def _passage(agent, i):
    return {**APPROVED, "passage_id": f"qf:{i}:1:1", "scholar_id": agent, "arabic_text": f"نص {agent}",
            "scholar_name": agent, "book_title": f"كتاب {agent}"}


class IkhtilafMatrixTests(unittest.IsolatedAsyncioTestCase):
    async def test_single_scholar_gives_no_comparison(self):
        o = AgentOrchestratorService()
        r = await o.execute_agent_analysis(1, 1, ["ibn_kathir"], {}, source_passages=[_passage("ibn_kathir", 1)])
        self.assertIsNone(r["comparative_analysis"])

    async def test_two_scholars_give_verbatim_matrix_without_inferred_judgements(self):
        o = AgentOrchestratorService()
        r = await o.execute_agent_analysis(
            1, 1, ["ibn_kathir", "al_tabari"], {},
            source_passages=[_passage("ibn_kathir", 1), _passage("al_tabari", 2)],
        )
        m = r["comparative_analysis"]
        self.assertEqual([row["scholar_id"] for row in m["scholars"]], ["ibn_kathir", "al_tabari"])
        for row in m["scholars"]:
            self.assertEqual(row["text"], f"نص {row['scholar_id']}")
            self.assertEqual(row["evidence_status"], "VERIFIED")
            self.assertTrue(row["passage_id"].startswith("qf:"))
        for field in ("agreement", "disagreement", "hadith_evidence", "fiqh_implications"):
            self.assertEqual(m[field]["status"], "UNVERIFIED")
        self.assertEqual(m["evidence_status"], "SOURCE-ATTRIBUTED")
