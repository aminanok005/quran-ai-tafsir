# Gemini Translation Route Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Expose the grounded Gemini Arabic-to-Thai translation workflow through `POST /api/v1/tafsir/gemini-translation`.

**Architecture:** A thin route in `routers/tafsir.py` fetches approved passages with the existing `_approved_source_passages` helper (from `routers/agents.py`), calls `translate_ayah` from `services/gemini_translation.py`, and maps `GeminiError` kinds to generic HTTP errors. The Arabic text comes from the server-side source, never from the request. With Gemini unconfigured the route returns 503 and makes no provider call.

**Tech Stack:** FastAPI, Pydantic v2, httpx MockTransport, pytest.

---

## Chunk 1: Route

### Task 1: Error mapping helper

**Files:**
- Create: `services/api/services/gemini_http.py`
- Test: `services/api/tests/test_gemini_http.py`

- [x] **Step 1: Write the failing test**

```python
from services.api.services.gemini_http import http_status_for
from services.api.services.gemini_provider import GeminiError, GeminiErrorKind

def test_mapping():
    assert http_status_for(GeminiError(GeminiErrorKind.CONFIGURATION)) == 503
    assert http_status_for(GeminiError(GeminiErrorKind.RATE_LIMIT)) == 429
    assert http_status_for(GeminiError(GeminiErrorKind.TIMEOUT)) == 504
    assert http_status_for(GeminiError(GeminiErrorKind.AUTHENTICATION)) == 503
    assert http_status_for(GeminiError(GeminiErrorKind.MALFORMED)) == 502
```

- [x] **Step 2: Run** `.venv/bin/python -m pytest services/api/tests/test_gemini_http.py -v`. Expected: FAIL (module missing).
- [x] **Step 3: Implement** `http_status_for(error)` as a dict lookup on `error.kind`, defaulting to 502. The detail string is always generic.
- [x] **Step 4: Run again.** Expected: PASS.
- [x] **Step 5: Commit** `git add` the two files, `git commit -m "feat: map Gemini errors to HTTP statuses"`.

### Task 2: Route

**Files:**
- Modify: `services/api/routers/tafsir.py` (append after the translate routes, about line 410)
- Test: `services/api/tests/test_gemini_translation_route.py`

- [x] **Step 1: Write failing tests** with FastAPI `TestClient`, patching `_approved_source_passages` and the module-level `ModelRouter`:
  - Success returns the Arabic from the passage and only references the supplied source IDs.
  - No approved passages returns 503 and makes no router call.
  - Unconfigured Gemini returns 503 with a generic detail that contains no key.
  - An out-of-range surah or ayah returns 400.
- [x] **Step 2: Run** `.venv/bin/python -m pytest services/api/tests/test_gemini_translation_route.py -v`. Expected: FAIL (404).
- [x] **Step 3: Implement** `POST /tafsir/gemini-translation?surah=&ayah=&agent_type=`:
  validate ranges, fetch passages, pass `arabic_text` from the passage plus `sources` built from the passage metadata, and return `{"success": true, "data": record}`. Use the existing rate-limit helper `_enforce_translation_rate_limit`.
- [x] **Step 4: Run.** Expected: PASS, and the earlier tafsir tests still pass.
- [x] **Step 5: Commit** `git commit -m "feat: add Gemini translation route"`.

### Task 3: Verify

- [x] **Step 1:** `.venv/bin/python -m pytest services/api/tests -q -p no:warnings`. Expected: only the known legacy async failures in `test_agents.py`.
- [x] **Step 2:** `.venv/bin/python -m compileall -q services/api`. Expected: no output.

## Out of scope
Embeddings migration, TTS, the multi-agent engine, content generators, UI wiring.
