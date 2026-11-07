import json
import unittest

import httpx

from services.api.services.studio_generation import (
    StudioGenerationError,
    generate_artifact,
)


class StudioGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_generates_and_validates_three_choice_quiz(self):
        requests = []
        artifact = {
            "title": "Quiz",
            "summary": "A short quiz",
            "sections": [],
            "slides": [],
            "scenes": [],
            "questions": [
                {
                    "question": "Question?",
                    "options": ["A", "B", "C"],
                    "answer_index": 1,
                    "explanation": "Supported by the source.",
                },
            ],
            "flashcards": [],
            "rows": [],
        }

        async def handler(request):
            requests.append(request)
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps(artifact)}}]},
            )

        result = await generate_artifact(
            "quiz",
            {"reference": "Surah 1:1", "arabic": "ayah"},
            api_key="test-key",
            model="test-model",
            base_url="https://llm.example.test/v1",
            wire_api="chat_completions",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(result["title"], "Quiz")
        self.assertEqual(len(result["questions"][0]["options"]), 3)
        body = json.loads(requests[0].content)
        self.assertIn("Do not invent tafsir", body["messages"][0]["content"])
        self.assertEqual(body["response_format"], {"type": "json_object"})

    async def test_rejects_quiz_without_three_options(self):
        invalid = {
            "title": "Quiz",
            "summary": "",
            "questions": [{"options": ["A", "B"], "answer_index": 0}],
        }

        async def handler(_request):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps(invalid)}}]},
            )

        with self.assertRaisesRegex(StudioGenerationError, "exactly three"):
            await generate_artifact(
                "quiz",
                {"reference": "Surah 1:1"},
                api_key="test-key",
                model="test-model",
                base_url="https://llm.example.test/v1",
                wire_api="chat_completions",
                transport=httpx.MockTransport(handler),
            )

    async def test_supports_responses_api_json_output(self):
        async def handler(request):
            self.assertTrue(request.url.path.endswith("/responses"))
            return httpx.Response(
                200,
                json={
                    "output_text": json.dumps(
                        {
                            "title": "Report",
                            "summary": "Summary",
                            "sections": [],
                            "slides": [],
                            "scenes": [],
                            "questions": [],
                            "flashcards": [],
                            "rows": [],
                        }
                    ),
                },
            )

        result = await generate_artifact(
            "report",
            {"reference": "Surah 1:1"},
            api_key="test-key",
            model="test-model",
            base_url="https://llm.example.test/v1",
            wire_api="responses",
            transport=httpx.MockTransport(handler),
        )
        self.assertEqual(result["title"], "Report")


if __name__ == "__main__":
    unittest.main()
