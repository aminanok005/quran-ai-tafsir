import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from services.api.app import app
from services.api.routers import agents as agents_router
from services.api.services.agent_orchestrator import AgentOrchestratorService
from services.api.services.evidence_validator import EvidenceValidationService
from services.api.services.quran_foundation_tafsir import QuranFoundationTafsir
from services.api.services.embedding import EmbeddingProviderError

TRUSTED_PASSAGE = {
    "passage_id": "passage-1",
    "permission_status": "approved",
    "verification_status": "verified",
    "license": "open",
    "verification_evidence": "reviewed",
    "source_reference": "https://example.test/source",
}


class AgentStub:
    def __init__(self, *, citation_id="passage-1", delay=0):
        self.citation_id = citation_id
        self.delay = delay
        self.calls = 0
        self.contexts = []

    async def explain_ayah(self, surah, ayah, context):
        self.calls += 1
        self.contexts.append(context)
        if self.delay:
            await asyncio.sleep(self.delay)
        return {
            "ayah_id": f"{surah}:{ayah}",
            "explanation": "Grounded explanation",
            "evidence_level": "VERIFIED",
            "citations": [{
                "passage_id": self.citation_id,
                "reference": {"url": "https://untrusted.example.test/"},
            }],
        }


class AgentOrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_agent_sources_keep_their_selected_scholar_identity(self):
        class FakeQfClient:
            content_api_url = "https://apis-prelive.quran.foundation/content/api/v4"

            def __init__(self):
                self.calls = []

            async def fetch_ayah(self, resource_id, surah, ayah):
                self.calls.append((resource_id, surah, ayah))
                return QuranFoundationTafsir(
                    resource_id=resource_id,
                    resource_name=f"Tafsir source {resource_id}",
                    language_name="english",
                    slug=f"source-{resource_id}",
                    verse_key="1:1",
                    text="Live Quran Foundation passage",
                )

        permission = {
            "permission_status": "approved",
            "verification_status": "verified",
            "license": "approved license",
            "verification_evidence": "Reviewed source record",
            "source_url": "https://example.test/source",
        }
        qf_client = FakeQfClient()
        with (
            patch.object(
                agents_router.settings,
                "quran_tafsir_resource_map",
                {"ibn_kathir": 168, "al_tabari": 170},
            ),
            patch.object(agents_router, "get_engine", return_value=object()),
            patch.object(
                agents_router,
                "_get_api_source_permission",
                return_value=permission,
            ),
            patch.object(
                agents_router,
                "get_qf_tafsir_client",
                return_value=qf_client,
            ),
        ):
            sources = await agents_router._approved_source_passages(
                1, 1, ["ibn_kathir", "al_tabari"]
            )

        self.assertEqual(qf_client.calls, [(168, 1, 1), (170, 1, 1)])
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["passage_id"], "qf:168:1:1")
        self.assertEqual(sources[0]["scholar_id"], "ibn_kathir")
        self.assertEqual(sources[0]["arabic_text"], "Live Quran Foundation passage")
        self.assertEqual(sources[0]["resource_id"], 168)
        self.assertEqual(sources[0]["verse_key"], "1:1")
        self.assertEqual(sources[0]["source_kind"], "tafsir")
        self.assertEqual(sources[1]["passage_id"], "qf:170:1:1")
        self.assertEqual(sources[1]["scholar_id"], "al_tabari")
        self.assertEqual(sources[1]["resource_id"], 170)
        self.assertEqual(
            sources[0]["source_reference"],
            "https://apis-prelive.quran.foundation/content/api/v4/tafsirs/168/by_ayah/1:1",
        )

    async def test_only_approved_passages_and_matching_citations_are_returned(self):
        agent = AgentStub()
        orchestrator = AgentOrchestratorService({"scholar": agent})
        context = {"question": "study"}

        result = await orchestrator.execute_agent_analysis(
            1, 1, ["scholar"], context, source_passages=[TRUSTED_PASSAGE]
        )

        self.assertEqual(result["agents_executed"], ["scholar"])
        self.assertEqual(result["evidence_summary"]["verified_sources"], 1)
        citation = result["agent_outputs"]["scholar"]["citations"][0]
        self.assertEqual(citation["reference"]["url"], TRUSTED_PASSAGE["source_reference"])
        self.assertEqual(citation["evidence_status"], "VERIFIED")
        self.assertEqual(
            result["agent_outputs"]["scholar"]["evidence_level"],
            "SOURCE-ATTRIBUTED",
        )
        self.assertEqual(agent.contexts[0]["source_passages"], [TRUSTED_PASSAGE])
        self.assertEqual(context, {"question": "study"})

    async def test_unapproved_or_unverified_passages_are_not_sent_to_agents(self):
        agent = AgentStub()
        orchestrator = AgentOrchestratorService({"scholar": agent})
        passage = {**TRUSTED_PASSAGE, "permission_status": "development_only"}

        with self.assertRaisesRegex(ValueError, "No approved, verified"):
            await orchestrator.execute_agent_analysis(
                1, 1, ["scholar"], source_passages=[passage]
            )

        self.assertEqual(agent.calls, 0)

    async def test_citations_outside_the_approved_context_fail_closed(self):
        agent = AgentStub(citation_id="invented-source")
        orchestrator = AgentOrchestratorService({"scholar": agent})

        result = await orchestrator.execute_agent_analysis(
            1, 1, ["scholar"], source_passages=[TRUSTED_PASSAGE]
        )

        self.assertEqual(result["agents_executed"], [])
        self.assertEqual(
            result["agent_outputs"]["scholar"]["error"],
            "Agent citations did not match approved source passages",
        )

    async def test_agent_failures_are_reported_without_leaking_exception_text(self):
        class FailingAgent:
            async def explain_ayah(self, *_args):
                raise RuntimeError("sensitive provider response")

        orchestrator = AgentOrchestratorService({"scholar": FailingAgent()})
        result = await orchestrator.execute_agent_analysis(
            1, 1, ["scholar"], source_passages=[TRUSTED_PASSAGE]
        )

        self.assertEqual(result["agent_outputs"]["scholar"]["error"], "Agent execution failed")
        self.assertNotIn("sensitive provider response", str(result))

    async def test_timeout_and_concurrency_are_bounded(self):
        class TrackingAgent(AgentStub):
            def __init__(self, active):
                super().__init__(delay=0.02)
                self.active = active

            async def explain_ayah(self, *args):
                self.active[0] += 1
                self.active[1] = max(self.active[1], self.active[0])
                try:
                    return await super().explain_ayah(*args)
                finally:
                    self.active[0] -= 1

        active = [0, 0]
        agents = {name: TrackingAgent(active) for name in ("one", "two", "three")}
        orchestrator = AgentOrchestratorService(agents, max_concurrency=2)
        result = await orchestrator.execute_agent_analysis(
            1,
            1,
            list(agents),
            source_passages=[TRUSTED_PASSAGE],
        )

        self.assertEqual(len(result["agents_executed"]), 3)
        self.assertEqual(active[1], 2)

        slow = AgentOrchestratorService(
            {"slow": AgentStub(delay=0.1)}, timeout_seconds=0.01
        )
        timed_out = await slow.execute_agent_analysis(
            1, 1, ["slow"], source_passages=[TRUSTED_PASSAGE]
        )
        self.assertEqual(timed_out["agent_outputs"]["slow"]["error"], "Agent timed out")

    async def test_invalid_requests_are_rejected(self):
        orchestrator = AgentOrchestratorService({"scholar": AgentStub()})

        with self.assertRaises(ValueError):
            await orchestrator.execute_agent_analysis(115, 1, ["scholar"])
        with self.assertRaises(ValueError):
            await orchestrator.execute_agent_analysis(1, 1, ["unknown"])
        with self.assertRaises(ValueError):
            await orchestrator.execute_agent_analysis(1, 1, [])

    def test_bulk_validation_marks_agent_failures_invalid(self):
        result = EvidenceValidationService().bulk_validate_agent_outputs(
            {"scholar": {"status": "failed", "error": "Agent timed out"}}
        )

        self.assertFalse(result["overall_valid"])
        self.assertEqual(result["summary"]["invalid_agents"], 1)
        self.assertEqual(
            result["agent_validations"]["scholar"]["evidence_level"],
            "UNVERIFIED",
        )

    def test_reference_validation_does_not_promote_ai_text_to_verified(self):
        result = EvidenceValidationService().validate_explanation(
            "According to Tafsir, Arabic text is discussed in the source.",
            [{"book": "A source", "volume": 1, "page": 1, "verified": True}],
            "A scholar",
            "scholar",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["evidence_level"], "AI-SYNTHESIS")

    def test_unverified_citations_cannot_promote_agent_output(self):
        result = EvidenceValidationService().bulk_validate_agent_outputs(
            {
                "al_qurtubi": {
                    "explanation": {
                        "analysis": "According to Tafsir, Arabic text is discussed."
                    },
                    "citations": [{
                        "book": "A source",
                        "volume": 1,
                        "page": 1,
                        "verified": True,
                    }],
                }
            }
        )

        self.assertFalse(result["overall_valid"])
        self.assertEqual(result["summary"]["invalid_agents"], 1)
        self.assertEqual(
            result["agent_validations"]["al_qurtubi"]["evidence_level"],
            "UNVERIFIED",
        )

    def test_canonical_source_citations_label_generated_text_source_attributed(self):
        result = EvidenceValidationService().bulk_validate_agent_outputs(
            {
                "al_qurtubi": {
                    "explanation": {
                        "analysis": "According to Tafsir, Arabic text is discussed."
                    },
                    "citations": [{
                        "passage_id": "passage-1",
                        "evidence_status": "VERIFIED",
                        "reference": {
                            "book": "A source",
                            "volume": 1,
                            "page": 1,
                            "url": "https://example.test/source",
                        },
                    }],
                }
            }
        )

        validation = result["agent_validations"]["al_qurtubi"]
        self.assertTrue(result["overall_valid"])
        self.assertEqual(validation["evidence_level"], "SOURCE-ATTRIBUTED")

    def test_versioned_agent_route_fails_closed_without_approved_sources(self):
        with (
            patch.object(
                agents_router,
                "_approved_source_passages",
                new_callable=AsyncMock,
                return_value=[],
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/agents/explain",
                params={"ayah_id": "1:1"},
                json={
                    "agent_types": ["ibn_kathir"],
                    "context": {"question": "Please explain"},
                },
            )

        self.assertEqual(response.status_code, 503)

    def test_versioned_comparison_route_fails_closed_without_approved_sources(self):
        with (
            patch.object(
                agents_router,
                "_approved_source_passages",
                new_callable=AsyncMock,
                return_value=[],
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/agents/compare",
                params={"ayah_id": "1:1"},
            )

        self.assertEqual(response.status_code, 503)

    def test_versioned_agent_route_returns_source_attributed_output_with_canonical_citation(self):
        agent_result = {
            "ayah_id": "1:1",
            "agents_executed": ["ibn_kathir"],
            "agent_outputs": {
                "ibn_kathir": {
                    "ayah_id": "1:1",
                    "explanation": "According to Tafsir, Arabic text is discussed in the source.",
                    "evidence_level": "SOURCE-ATTRIBUTED",
                    "citations": [{
                        "passage_id": "passage-1",
                        "evidence_status": "VERIFIED",
                        "reference": {
                            "book": "A source",
                            "scholar": "A scholar",
                            "url": "https://example.test/source",
                        },
                    }],
                }
            },
            "evidence_summary": {
                "total_sources": 1,
                "verified_sources": 1,
                "unverified_sources": 0,
                "ai_synthesis": 0,
            },
        }
        with (
            patch.object(
                agents_router,
                "_approved_source_passages",
                new_callable=AsyncMock,
                return_value=[TRUSTED_PASSAGE],
            ),
            patch.object(
                agents_router.agent_orchestrator,
                "execute_agent_analysis",
                new_callable=AsyncMock,
                return_value=agent_result,
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/v1/tafsir/agents/explain",
                params={"ayah_id": "1:1"},
                json={
                    "agent_types": ["ibn_kathir"],
                    "context": {"question": "Please explain"},
                },
            )

        self.assertEqual(response.status_code, 200, response.json())
        output = response.json()["data"]["agent_outputs"]["ibn_kathir"]
        self.assertEqual(output["evidence_level"], "SOURCE-ATTRIBUTED")
        self.assertEqual(output["citations"][0]["evidence_status"], "VERIFIED")
        self.assertTrue(response.json()["data"]["validation"]["overall_valid"])

    def test_versioned_agent_route_persists_question_and_relevance_threshold(self):
        source = {
            "passage_id": "qf:168:1:1",
            "resource_id": 168,
            "verse_key": "1:1",
            "arabic_text": "Approved exact source passage",
            "scholar_id": "ibn_kathir",
            "scholar_name": "Tafsir Ibn Kathir",
            "volume": None,
            "page": None,
            "source_kind": "tafsir",
        }
        agent_result = {
            "ayah_id": "1:1",
            "agents_executed": ["ibn_kathir"],
            "agent_outputs": {"ibn_kathir": {"explanation": "Grounded"}},
            "evidence_summary": {
                "total_sources": 1,
                "verified_sources": 1,
                "unverified_sources": 0,
                "ai_synthesis": 0,
            },
        }

        for score, expected_available in ((0.719, False), (0.72, True)):
            with self.subTest(score=score):
                browser_id, session_id = uuid4(), uuid4()
                scored_source = {
                    "source_id": "qf:168:1:1",
                    "resource_id": 168,
                    "verse_key": "1:1",
                    "similarity": score,
                    "content_hash": "a" * 64,
                    "scholar_id": "ibn_kathir",
                    "scholar_name": "Tafsir Ibn Kathir",
                    "volume": None,
                    "page": None,
                    "source_kind": "tafsir",
                }
                app.dependency_overrides[agents_router.current_browser_id] = (
                    lambda: browser_id
                )
                try:
                    with (
                        patch.object(
                            agents_router,
                            "_approved_source_passages",
                            new_callable=AsyncMock,
                            return_value=[source],
                        ),
                        patch.object(
                            agents_router.agent_orchestrator,
                            "execute_agent_analysis",
                            new_callable=AsyncMock,
                            return_value=agent_result,
                        ),
                        patch.object(
                            agents_router.evidence_validator,
                            "bulk_validate_agent_outputs",
                            return_value={
                                "overall_valid": True,
                                "agent_validations": {},
                            },
                        ),
                        patch.object(
                            agents_router,
                            "score_retrieved_sources",
                            new_callable=AsyncMock,
                            return_value=[scored_source],
                        ) as score_sources,
                        patch.object(agents_router, "get_engine", return_value=object()),
                        patch.object(agents_router, "store_message_snapshot") as store_snapshot,
                        TestClient(app) as client,
                    ):
                        response = client.post(
                            "/api/v1/tafsir/agents/explain",
                            params={
                                "ayah_id": "1:1",
                                "session_id": str(session_id),
                            },
                            json={
                                "agent_types": ["ibn_kathir"],
                                "context": {
                                    "question": "  Explain this selected ayah  ",
                                    "language": "th",
                                },
                            },
                        )
                finally:
                    app.dependency_overrides.pop(
                        agents_router.current_browser_id,
                        None,
                    )

                self.assertEqual(response.status_code, 200, response.json())
                data = response.json()["data"]
                self.assertEqual(data["session_id"], str(session_id))
                self.assertTrue(data["message_id"])
                self.assertEqual(data["followups_available"], expected_available)
                score_sources.assert_awaited_once_with(
                    "  Explain this selected ayah  ",
                    [source],
                )
                store_snapshot.assert_called_once()
                self.assertEqual(
                    store_snapshot.call_args.kwargs["question"],
                    "  Explain this selected ayah  ",
                )
                self.assertEqual(store_snapshot.call_args.kwargs["selected_agent_ids"], ["ibn_kathir"])
                self.assertEqual(
                    store_snapshot.call_args.kwargs["source_snapshots"],
                    [scored_source],
                )

    def test_versioned_agent_route_keeps_answer_on_scoring_and_persistence_failures(self):
        source = {
            "passage_id": "qf:168:1:1",
            "resource_id": 168,
            "verse_key": "1:1",
            "arabic_text": "Approved exact source passage",
            "scholar_id": "ibn_kathir",
            "scholar_name": "Tafsir Ibn Kathir",
            "volume": None,
            "page": None,
            "source_kind": "tafsir",
        }
        agent_result = {
            "ayah_id": "1:1",
            "agents_executed": ["ibn_kathir"],
            "agent_outputs": {"ibn_kathir": {"explanation": "Grounded"}},
            "evidence_summary": {
                "total_sources": 1,
                "verified_sources": 1,
                "unverified_sources": 0,
                "ai_synthesis": 0,
            },
        }

        for scoring_fails in (True, False):
            with self.subTest(scoring_fails=scoring_fails):
                browser_id = uuid4()
                app.dependency_overrides[agents_router.current_browser_id] = lambda: browser_id
                score_snapshot = {
                    "source_id": "qf:168:1:1",
                    "resource_id": 168,
                    "verse_key": "1:1",
                    "similarity": 0.9,
                    "content_hash": "a" * 64,
                    "scholar_id": "ibn_kathir",
                    "scholar_name": "Tafsir Ibn Kathir",
                    "volume": None,
                    "page": None,
                    "source_kind": "tafsir",
                }
                try:
                    with (
                        patch.object(
                            agents_router,
                            "_approved_source_passages",
                            new_callable=AsyncMock,
                            return_value=[source],
                        ),
                        patch.object(
                            agents_router.agent_orchestrator,
                            "execute_agent_analysis",
                            new_callable=AsyncMock,
                            return_value=agent_result,
                        ),
                        patch.object(
                            agents_router.evidence_validator,
                            "bulk_validate_agent_outputs",
                            return_value={
                                "overall_valid": True,
                                "agent_validations": {},
                            },
                        ),
                        patch.object(
                            agents_router,
                            "score_retrieved_sources",
                            new_callable=AsyncMock,
                            side_effect=(
                                EmbeddingProviderError("embedding unavailable")
                                if scoring_fails
                                else None
                            ),
                            return_value=[] if scoring_fails else [score_snapshot],
                        ),
                        patch.object(agents_router, "get_engine", return_value=object()),
                        patch.object(
                            agents_router,
                            "store_message_snapshot",
                            side_effect=SQLAlchemyError("database unavailable")
                            if not scoring_fails
                            else None,
                        ),
                        TestClient(app) as client,
                    ):
                        response = client.post(
                            "/api/v1/tafsir/agents/explain",
                            params={"ayah_id": "1:1", "session_id": str(uuid4())},
                            json={
                                "agent_types": ["ibn_kathir"],
                                "context": {"question": "Explain this"},
                            },
                        )
                finally:
                    app.dependency_overrides.pop(
                        agents_router.current_browser_id,
                        None,
                    )

                self.assertEqual(response.status_code, 200, response.json())
                self.assertFalse(response.json()["data"]["followups_available"])
                self.assertIsNone(response.json()["data"]["message_id"])


class AgentRouteTests(unittest.TestCase):
    def test_explain_fails_when_api_has_no_approved_passages(self):
        with (
            patch.object(
                agents_router,
                "_approved_source_passages",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch.object(
                agents_router.agent_orchestrator,
                "execute_agent_analysis",
                new_callable=AsyncMock,
            ) as execute,
            TestClient(app) as client,
        ):
            response = client.post(
                "/explain",
                params={"ayah_id": "1:1"},
                json={
                    "agent_types": ["ibn_kathir"],
                    "context": {"question": "Please explain"},
                },
            )

        self.assertEqual(response.status_code, 503, response.json())
        execute.assert_not_awaited()

    def test_explain_rejects_client_supplied_source_passages(self):
        with (
            patch.object(
                agents_router,
                "_approved_source_passages",
                new_callable=AsyncMock,
                return_value=[TRUSTED_PASSAGE],
            ),
            patch.object(
                agents_router.agent_orchestrator,
                "execute_agent_analysis",
                new_callable=AsyncMock,
            ) as execute,
            TestClient(app) as client,
        ):
            response = client.post(
                "/explain",
                params={"ayah_id": "1:1"},
                json={
                    "agent_types": ["ibn_kathir"],
                    "context": {"source_passages": [TRUSTED_PASSAGE]},
                },
            )

        self.assertEqual(response.status_code, 422)
        execute.assert_not_awaited()

    def test_explain_reports_failure_when_agents_cannot_ground_their_output(self):
        with (
            patch.object(
                agents_router,
                "_approved_source_passages",
                new_callable=AsyncMock,
                return_value=[TRUSTED_PASSAGE],
            ),
            patch.object(
                agents_router.agent_orchestrator,
                "execute_agent_analysis",
                new_callable=AsyncMock,
                return_value={
                    "agents_executed": [],
                    "agent_outputs": {
                        "ibn_kathir": {
                            "status": "failed",
                            "error": "Agent citations did not match approved source passages",
                        }
                    },
                },
            ) as execute,
            TestClient(app) as client,
        ):
            response = client.post(
                "/explain",
                params={"ayah_id": "1:1"},
                json={
                    "agent_types": ["ibn_kathir"],
                    "context": {"question": "Please explain"},
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("Agents could not produce", response.json()["error"])
        self.assertEqual(execute.await_args.args[3], {"question": "Please explain"})
        self.assertEqual(
            execute.await_args.kwargs["source_passages"],
            [TRUSTED_PASSAGE],
        )

    def test_legacy_quiz_endpoint_does_not_return_placeholder_questions(self):
        with TestClient(app) as client:
            response = client.post("/quiz", params={"surah": 1})

        self.assertEqual(response.status_code, 503)
        self.assertIn("Source-grounded", response.json()["error"])


if __name__ == "__main__":
    unittest.main()
