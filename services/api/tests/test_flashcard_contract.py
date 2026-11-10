import pytest

from services.api.services.studio_artifact_contracts import validate_studio_artifact
from services.api.services.studio_generation import StudioGenerationError

CARD = {"front": "ما معنى الرحمن؟", "back": "ذو الرحمة الواسعة", "source_passage_id": "qf:168:1:1"}


def test_valid_flashcards_pass():
    out = validate_studio_artifact("flashcards", "t", "s", {"cards": [CARD] * 3})
    assert out["content"]["cards"][0]["source_passage_id"] == "qf:168:1:1"


@pytest.mark.parametrize(
    "cards",
    [
        [CARD] * 2,
        [{**CARD, "source_passage_id": ""}] * 3,
        [{"front": "x", "back": "y"}] * 3,
        [{**CARD, "extra": 1}] * 3,
    ],
)
def test_invalid_flashcards_rejected(cards):
    with pytest.raises(StudioGenerationError):
        validate_studio_artifact("flashcards", "t", "s", {"cards": cards})


import json

import httpx

from services.api.services.studio_generation import generate_artifact


def _run_flashcards(cards, allowed):
    import asyncio

    def handler(request):
        body = {"title": "T", "summary": "S", "flashcards": cards}
        return httpx.Response(200, json={"output_text": json.dumps(body)})

    return asyncio.run(
        generate_artifact(
            "flashcards",
            {"reference": "1:1"},
            api_key="k",
            model="m",
            base_url="https://x.test",
            wire_api="responses",
            transport=httpx.MockTransport(handler),
            allowed_source_ids=allowed,
        )
    )


def test_generation_accepts_cards_citing_supplied_sources():
    out = _run_flashcards([{"front": "a", "back": "b", "source_passage_id": "quran"}], {"quran"})
    assert out["flashcards"][0]["source_passage_id"] == "quran"


def test_generation_rejects_cards_citing_unknown_sources():
    with pytest.raises(StudioGenerationError):
        _run_flashcards([{"front": "a", "back": "b", "source_passage_id": "made-up"}], {"quran"})


def _quiz(source_id):
    q = {"question": "q", "options": ["a", "b", "c"], "answer_index": 0, "explanation": "e"}
    if source_id is not None:
        q["source_passage_id"] = source_id
    return {"title": "T", "summary": "S", "content": {"questions": [dict(q) for _ in range(5)]}}


def _run_quiz(source_id, allowed):
    import asyncio

    def handler(request):
        return httpx.Response(200, json={"output_text": json.dumps(_quiz(source_id))})

    return asyncio.run(
        generate_artifact(
            "quiz", {"reference": "1:1"}, api_key="k", model="m",
            base_url="https://x.test", wire_api="responses",
            transport=httpx.MockTransport(handler), allowed_source_ids=allowed,
        )
    )


def test_quiz_without_source_id_still_valid():
    assert _run_quiz(None, {"quran"})["content"]["questions"]


def test_quiz_with_supplied_source_id_valid():
    out = _run_quiz("quran", {"quran"})
    assert out["content"]["questions"][0]["source_passage_id"] == "quran"


def test_quiz_with_unknown_source_id_rejected():
    with pytest.raises(StudioGenerationError):
        _run_quiz("made-up", {"quran"})


def test_quiz_prompt_asks_for_supplied_source_ids():
    import asyncio

    seen = {}

    def handler(request):
        seen["body"] = request.content.decode()
        return httpx.Response(200, json={"output_text": json.dumps(_quiz("quran"))})

    asyncio.run(
        generate_artifact(
            "quiz", {"reference": "1:1", "source_ids": ["quran"]}, api_key="k", model="m",
            base_url="https://x.test", wire_api="responses",
            transport=httpx.MockTransport(handler), allowed_source_ids={"quran"},
        )
    )
    assert "source_passage_id" in seen["body"]
