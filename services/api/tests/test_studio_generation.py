import json
import unittest

import httpx

from services.api.services.studio_artifact_contracts import validate_studio_artifact
from services.api.services.studio_generation import (
    StudioGenerationError,
    generate_artifact,
)


def valid_audio_content(segment_count=4):
    return {
        "segments": [
            {
                "host": "Host A" if index % 2 == 0 else "Host B",
                "text": f"คำอธิบายช่วงที่ {index + 1}",
            }
            for index in range(segment_count)
        ],
    }


def valid_quiz_content():
    return {
        "questions": [
            {
                "question": f"Question {index + 1}?",
                "options": ["Choice A", "Choice B", "Choice C"],
                "answer_index": 1,
                "explanation": "Supported by the source.",
            }
            for index in range(5)
        ],
    }


def valid_infographic_content():
    return {
        "takeaway": "A concise, source-supported takeaway.",
        "cards": [
            {
                "heading": f"Card {index + 1}",
                "points": ["First source-supported point.", "Second source-supported point."],
            }
            for index in range(3)
        ],
    }


class StudioArtifactContractTests(unittest.TestCase):
    def assert_invalid(self, kind, content, *, title="Title", summary="Summary"):
        with self.assertRaises(StudioGenerationError):
            validate_studio_artifact(kind, title, summary, content)

    def test_audio_enforces_thai_alternation_counts_and_nested_fields(self):
        validated = validate_studio_artifact("audio", "Title", "", valid_audio_content(8))
        self.assertEqual(set(validated), {"title", "summary", "content"})
        self.assertEqual(len(validated["content"]["segments"]), 8)
        maximal_audio = valid_audio_content(8)
        maximal_audio["segments"][0]["text"] = "ค" * 1200
        validate_studio_artifact("audio", "T" * 160, "", maximal_audio)

        invalid_contents = []
        invalid = valid_audio_content(3)
        invalid_contents.append(invalid)
        invalid = valid_audio_content()
        invalid["segments"][0]["host"] = "Host B"
        invalid_contents.append(invalid)
        invalid = valid_audio_content()
        invalid["segments"][1]["host"] = "Host A"
        invalid_contents.append(invalid)
        invalid = valid_audio_content()
        invalid["segments"][0]["text"] = "English only"
        invalid_contents.append(invalid)
        invalid = valid_audio_content()
        invalid["segments"][0]["extra"] = "forbidden"
        invalid_contents.append(invalid)
        invalid = valid_audio_content()
        invalid["extra"] = "forbidden"
        invalid_contents.append(invalid)
        invalid = valid_audio_content()
        invalid["segments"][0]["text"] = ""
        invalid_contents.append(invalid)
        invalid = valid_audio_content()
        invalid["segments"][0]["text"] = "คำ" * 1201
        invalid_contents.append(invalid)
        invalid = valid_audio_content(9)
        invalid_contents.append(invalid)

        for content in invalid_contents:
            with self.subTest(content=content):
                self.assert_invalid("audio", content)

    def test_quiz_requires_five_three_choice_questions_and_strict_indices(self):
        maximal_quiz = valid_quiz_content()
        maximal_quiz["questions"][0]["question"] = "Q" * 500
        maximal_quiz["questions"][0]["options"][0] = "O" * 200
        maximal_quiz["questions"][0]["explanation"] = "E" * 1000
        validated = validate_studio_artifact(
            "quiz",
            "T" * 160,
            "S" * 500,
            maximal_quiz,
        )
        self.assertEqual(len(validated["content"]["questions"]), 5)

        invalid_contents = []
        invalid = valid_quiz_content()
        invalid["questions"][0]["options"].pop()
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["questions"][0]["options"].append("D")
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["questions"][0]["answer_index"] = True
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["questions"].pop()
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["questions"].append(
            {
                "question": "Extra question?",
                "options": ["A", "B", "C"],
                "answer_index": 0,
                "explanation": "Supported.",
            }
        )
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["questions"][0]["extra"] = "forbidden"
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["extra"] = "forbidden"
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["questions"][0]["options"][0] = ""
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["questions"][0]["question"] = "Q" * 501
        invalid_contents.append(invalid)
        invalid = valid_quiz_content()
        invalid["questions"][0]["explanation"] = "E" * 1001
        invalid_contents.append(invalid)

        for content in invalid_contents:
            with self.subTest(content=content):
                self.assert_invalid("quiz", content)

    def test_infographic_enforces_card_bounds_and_rejects_nested_fields(self):
        maximal_infographic = valid_infographic_content()
        maximal_infographic["takeaway"] = "T" * 500
        maximal_infographic["cards"][0]["heading"] = "H" * 100
        maximal_infographic["cards"][0]["points"] = ["P" * 280] * 5
        maximal_infographic["cards"].extend(
            [
                {"heading": f"Card {index}", "points": ["First point.", "Second point."]}
                for index in range(4, 7)
            ]
        )
        validated = validate_studio_artifact(
            "infographic",
            "Title",
            "Summary",
            maximal_infographic,
        )
        self.assertEqual(len(validated["content"]["cards"]), 6)

        invalid_contents = []
        invalid = valid_infographic_content()
        invalid["cards"].pop()
        invalid_contents.append(invalid)
        invalid = valid_infographic_content()
        invalid["cards"][0]["points"].pop()
        invalid_contents.append(invalid)
        invalid = valid_infographic_content()
        invalid["cards"][0]["points"].extend(
            ["Third point.", "Fourth point.", "Fifth point.", "Sixth point."]
        )
        invalid_contents.append(invalid)
        invalid = valid_infographic_content()
        invalid["cards"].extend(
            [
                {"heading": f"Card {index}", "points": ["First point.", "Second point."]}
                for index in range(4, 8)
            ]
        )
        invalid_contents.append(invalid)
        invalid = valid_infographic_content()
        invalid["cards"][0]["extra"] = "forbidden"
        invalid_contents.append(invalid)
        invalid = valid_infographic_content()
        invalid["extra"] = "forbidden"
        invalid_contents.append(invalid)
        invalid = valid_infographic_content()
        invalid["cards"][0]["heading"] = "H" * 101
        invalid_contents.append(invalid)
        invalid = valid_infographic_content()
        invalid["cards"][0]["points"][0] = "P" * 281
        invalid_contents.append(invalid)
        invalid = valid_infographic_content()
        invalid["takeaway"] = "T" * 501
        invalid_contents.append(invalid)

        for content in invalid_contents:
            with self.subTest(content=content):
                self.assert_invalid("infographic", content)

    def test_infographic_accepts_supported_optional_layout_hint(self):
        without_hint = validate_studio_artifact(
            "infographic",
            "Title",
            "",
            valid_infographic_content(),
        )
        self.assertNotIn("layout_hint", without_hint["content"])

        content = valid_infographic_content()
        content["layout_hint"] = "two-column"
        validated = validate_studio_artifact("infographic", "Title", "", content)
        self.assertEqual(validated["content"]["layout_hint"], "two-column")

        invalid = valid_infographic_content()
        invalid["layout_hint"] = "freeform"
        self.assert_invalid("infographic", invalid)
        invalid = valid_infographic_content()
        invalid["layout_hint"] = None
        self.assert_invalid("infographic", invalid)

    def test_shared_title_and_summary_bounds(self):
        self.assert_invalid("audio", valid_audio_content(), title="T" * 161)
        self.assert_invalid("audio", valid_audio_content(), title=" ")
        self.assert_invalid("audio", valid_audio_content(), summary="S" * 501)


class StudioGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_generates_validated_quiz_with_bearer_authentication(self):
        requests = []
        artifact = {
            "title": "Quiz",
            "summary": "A short quiz",
            "content": valid_quiz_content(),
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
            api_key="unit-test-key",
            model="test-model",
            base_url="https://llm.example.test/v1",
            wire_api="chat_completions",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(result["title"], "Quiz")
        self.assertEqual(set(result), {"title", "summary", "content"})
        self.assertEqual(len(result["content"]["questions"]), 5)
        self.assertEqual(requests[0].headers["authorization"], "Bearer unit-test-key")
        body = json.loads(requests[0].content)
        self.assertIn("Do not invent tafsir", body["messages"][0]["content"])
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertIn('"reference": "Surah 1:1"', body["messages"][1]["content"])

    async def test_rejects_quiz_without_three_options(self):
        invalid = {
            "title": "Quiz",
            "summary": "",
            "content": {
                "questions": [
                    {
                        "question": f"Question {index + 1}?",
                        "options": ["A", "B", "C"],
                        "answer_index": 0,
                        "explanation": "Supported.",
                    }
                    for index in range(5)
                ],
            },
        }
        invalid["content"]["questions"][0]["options"].pop()

        async def handler(_request):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps(invalid)}}]},
            )

        with self.assertRaisesRegex(StudioGenerationError, "required contract"):
            await generate_artifact(
                "quiz",
                {"reference": "Surah 1:1"},
                api_key="test-key",
                model="test-model",
                base_url="https://llm.example.test/v1",
                wire_api="chat_completions",
                transport=httpx.MockTransport(handler),
            )

    async def test_generates_audio_using_responses_json_contract(self):
        requests = []
        artifact = {
            "title": "Audio",
            "summary": "Summary",
            "content": valid_audio_content(),
        }
        source_context = {"source_text": "private source passage"}

        async def handler(request):
            requests.append(request)
            return httpx.Response(
                200,
                json={"output_text": json.dumps(artifact, ensure_ascii=False)},
            )

        result = await generate_artifact(
            "audio",
            source_context,
            api_key="unit-test-key",
            model="test-model",
            base_url="https://llm.example.test/v1",
            wire_api="responses",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(set(result), {"title", "summary", "content"})
        self.assertEqual(len(result["content"]["segments"]), 4)
        self.assertEqual(requests[0].headers["authorization"], "Bearer unit-test-key")
        body = json.loads(requests[0].content)
        self.assertEqual(body["text"]["format"], {"type": "json_object"})
        self.assertIn("private source passage", body["input"][1]["content"][0]["text"])

    async def test_rejects_extra_fields_in_target_kind_envelope(self):
        artifact = {
            "title": "Quiz",
            "summary": "",
            "content": valid_quiz_content(),
            "provider_metadata": "not allowed",
        }

        async def handler(_request):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps(artifact)}}]},
            )

        with self.assertRaisesRegex(StudioGenerationError, "required contract"):
            await generate_artifact(
                "quiz",
                {"reference": "Surah 1:1"},
                api_key="unit-test-key",
                model="test-model",
                base_url="https://llm.example.test/v1",
                wire_api="chat_completions",
                transport=httpx.MockTransport(handler),
            )

    async def test_provider_errors_are_sanitized_and_single_attempt(self):
        source_text = "private source passage"
        api_key = "unit-test-key"

        for error_kind in ("status", "transport"):
            requests = []

            async def handler(request):
                requests.append(request)
                if error_kind == "transport":
                    raise httpx.ConnectError(f"{api_key} {source_text}", request=request)
                return httpx.Response(401, text=f"{api_key} {source_text}")

            with self.subTest(error_kind=error_kind):
                with self.assertRaisesRegex(
                    StudioGenerationError,
                    "provider request failed",
                ) as caught:
                    await generate_artifact(
                        "audio",
                        {"source_text": source_text},
                        api_key=api_key,
                        model="test-model",
                        base_url="https://llm.example.test/v1",
                        wire_api="responses",
                        transport=httpx.MockTransport(handler),
                    )

                self.assertEqual(len(requests), 1)
                self.assertNotIn(api_key, str(caught.exception))
                self.assertNotIn(source_text, str(caught.exception))
                self.assertEqual(
                    caught.exception.status_code,
                    401 if error_kind == "status" else None,
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
