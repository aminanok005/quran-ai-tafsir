# Grounded Suggested Follow-Ups Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-answer, API-generated follow-up suggestions to Grounded dialogue, with server-verified source eligibility and separately cited multi-prompt answers.

**Architecture:** Persist browser-owned message/source snapshots in Postgres, calculate real relevance scores from the answer question and approved API passages, and generate/filter suggestions from those exact revalidated sources. Keep conversation turns in Reader state and render a separate selectable follow-up component for each answer.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy, Alembic, PostgreSQL, existing embedding and LLM clients, Next.js 14, React Query, TypeScript, Jest, pytest.

---

## File map

- `services/api/migrations/versions/0004_chat_message_retrievals.py` — browser-owned chat session and retrieval snapshot tables.
- `services/api/services/chat_message_store.py` — persist and load message snapshots with browser/session ownership checks.
- `services/api/services/retrieval_scoring.py` — score exact candidate passages with `embed_texts`; no default or synthetic scores.
- `services/api/tests/test_retrieval_scoring.py` — embedding inputs, vector validation, cosine score, and threshold boundary tests.
- `services/api/services/chat_suggestions.py` — generate and ground-check candidates, then enforce source/category/text safety.
- `services/api/routers/agents.py` — accept session/batch context, score and persist sources, return message IDs without making scoring failures fatal to answers.
- `services/api/routers/chat.py` — strict Pydantic request/response models, revalidation, candidate source-ID/category filtering, and `POST /api/v1/chat/suggestions`.
- `services/api/app.py` — register the chat router under `/api/v1`.
- `services/api/tests/test_chat_message_store.py` — repository ownership and snapshot persistence tests.
- `services/api/tests/test_chat_suggestions.py` — endpoint, relevance threshold, category, source, candidate-safety, and failure-isolation tests.
- `services/api/tests/test_agent_orchestrator.py` — answer response IDs, batch sections/citations, and non-fatal snapshot/scoring failures.
- `apps/web/src/lib/api/client.ts` — typed answer metadata, batch question input, and suggestions client call.
- `apps/web/src/components/workspace/SuggestedFollowUps.tsx` — API-backed loading/empty/error UI, selectable suggestion cards, and submit/clear/refresh actions.
- `apps/web/src/components/workspace/SuggestedFollowUps.test.tsx` — component states, accessibility, category/evidence labels, and selection behavior.
- `apps/web/app/page.tsx` and `apps/web/app/page.test.tsx` — retain dialogue turns, submit single/batch prompts, render independent citations, and keep the selected ayah context.

## Chunk 1: Persisting message-specific retrieval snapshots

### Task 1: Add schema migration and repository tests

**Files:**
- Create: `services/api/tests/test_chat_message_store.py`
- Create: `services/api/migrations/versions/0004_chat_message_retrievals.py`
- Create: `services/api/services/chat_message_store.py`

- [ ] **Step 1: Write failing repository tests** for creating a session/message snapshot, loading it only for the matching `browser_id`, rejecting a different browser, and storing source identity/score/hash without source text.
- [ ] **Step 2: Add a migration-contract test** that imports the revision without a database connection, checks its `down_revision`, and captures migration operations to assert the session/message tables, browser ownership fields, selected agent IDs, source snapshot fields, and lookup indexes are present.
- [ ] **Step 3: Run the focused tests and confirm they fail** because the repository and migration do not exist.

Run: `python -m pytest services/api/tests/test_chat_message_store.py -q`
Expected: collection or import failure for the missing store module.

- [ ] **Step 4: Add the migration** chained after `0003_tafsir_api_translations`. Create `chat_sessions` with UUID ID, browser UUID, and timestamps; create `chat_message_retrievals` with UUID message ID, session/browser IDs, user question, ayah, selected agent/source IDs, JSONB source snapshots, and timestamps. Add unique/index constraints for message lookup and browser ownership; do not store source passage text.
- [ ] **Step 5: Implement the repository** with parameterized SQLAlchemy statements and transaction-scoped writes. Validate UUID inputs at the boundary and include `browser_id` in every lookup predicate. Keep `source_snapshots` limited to source/resource identity, scholar/source metadata, similarity, content hash, and source kind.
- [ ] **Step 6: Run the repository and migration-contract tests** and verify all ownership, no-source-text, revision-chain, and schema assertions pass.

Run: `python -m pytest services/api/tests/test_chat_message_store.py -q`
Expected: PASS.

### Task 2: Score and persist selected approved API passages

**Files:**
- Create: `services/api/services/retrieval_scoring.py`
- Create: `services/api/tests/test_retrieval_scoring.py`
- Modify: `services/api/routers/agents.py`
- Modify: `services/api/tests/test_agent_orchestrator.py`

- [ ] **Step 1: Add failing scoring tests** for cosine similarity, empty passage sets, vector dimension mismatch, non-numeric/non-finite values, zero-norm vectors, provider/configuration failure, and threshold scores below/at/above `0.72`. Assert `embed_texts` receives the exact question followed by the exact approved passage texts in one batch.
- [ ] **Step 2: Add failing answer-route tests** asserting each approved API passage keeps its own `resource_id`, `verse_key`, selected `scholar_id`, and `source_kind`; a question with a session ID returns and persists the exact question, message IDs, scores, and hashes; `followups_available` is false below `0.72` and true at/above it; and score/persistence failures leave the answer successful with `followups_available: false`.
- [ ] **Step 3: Run the scoring and answer-route tests and confirm failure.**

Run: `python -m pytest services/api/tests/test_retrieval_scoring.py services/api/tests/test_agent_orchestrator.py -q`
Expected: FAIL because the scoring helper is absent.

- [ ] **Step 4: Implement scoring using the existing `services.api.services.embedding.embed_texts` client.** Embed the exact question and each approved candidate passage in one batch; calculate cosine similarity from the returned vectors; reject non-finite scores. Do not fabricate scores or call the retired local Tafsir search.
- [ ] **Step 5: Validate vectors structurally:** require matching dimensions, finite numeric values, and nonzero norms. Accept cosine results in `[-1, 1]`; clamp only results within `1e-6` beyond either endpoint to that endpoint, and reject results farther outside that tolerance.
- [ ] **Step 6: Keep each passage's resource identity and selected `agent_type` together** while fetching approved API sources; attach `resource_id`, `verse_key`, `scholar_id`, and `source_kind` to that exact passage.
- [ ] **Step 7: Extend `/agents/explain`** with an optional UUID `session_id` and the existing browser identity dependency. When a non-empty question is present, score the exact approved source passages, persist the exact question with their identity/metadata/score/hash snapshot and selected IDs, and return `session_id`, `message_id`, and `followups_available`. Keep the answer successful and set follow-up availability false on known embedding, validation, or database failures; log a specific warning and never fabricate a score or snapshot. Use the fixed inclusive `0.72` threshold to derive availability.
- [ ] **Step 8: Treat embedding configuration/provider errors as an unavailable suggestion source, not an answer failure.** The failing tests from Step 1 must prove `0.72` is eligible and any score below it is not.
- [ ] **Step 9: Run the focused scoring and answer-route tests.**

Run: `python -m pytest services/api/tests/test_retrieval_scoring.py services/api/tests/test_agent_orchestrator.py -q`
Expected: PASS.

## Chunk 2: Answer metadata, structured batches, and suggestions API

### Task 3: Add separately cited batch answer sections

**Files:**
- Modify: `services/api/routers/agents.py`
- Modify: `services/api/services/agent_orchestrator.py`
- Modify: `services/api/tests/test_agent_orchestrator.py`

- [ ] **Step 1: Add failing batch tests** proving one numbered user message can carry a structured prompt list and yields one separately headed result section per prompt, each with its own validated citation set. Verify ordinary single-question requests retain the existing answer shape.
- [ ] **Step 2: Run the focused batch tests and confirm failure.**

Run: `python -m pytest services/api/tests/test_agent_orchestrator.py -q`
Expected: FAIL on missing batch behavior.

- [ ] **Step 3: Extend request-context validation** to accept only the existing `question`/`language` fields plus bounded, non-empty structured batch prompts when present. Reject unknown keys, duplicate/empty batch items, and excessive batch counts.
- [ ] **Step 4: Extend the orchestrator** to run each batch prompt independently against the same approved source set and return section-scoped agent outputs/citations. Preserve the existing single-question response shape and validation behavior.
- [ ] **Step 5: Run the focused batch tests.**

Run: `python -m pytest services/api/tests/test_agent_orchestrator.py -q`
Expected: PASS, including unchanged single-question cases.

### Task 4: Add candidate generation and strict suggestions endpoint

**Files:**
- Create: `services/api/services/chat_suggestions.py`
- Create: `services/api/routers/chat.py`
- Modify: `services/api/app.py`
- Create: `services/api/tests/test_chat_suggestions.py`

- [ ] **Step 1: Write endpoint tests first** for empty retrieval, maximum score below `0.72`, exactly `0.72`, a single scholar excluding `compare`, missing volume/page excluding `deepen`, missing neighboring-ayah/asbab records excluding `context`, review labeled `AI_SYNTHESIS`, disabled/unavailable sources reducing `basisCount`, and browser ownership.
- [ ] **Step 2: Add candidate-provenance tests** for missing, empty, duplicate, unrecognized, and other-message source IDs; forged basis counts/evidence; exact source-text quotation; fatwa/ruling requests; malformed text; and more than four candidates. Prove category checks use each candidate's support set, not unrelated message sources. Add tests that suggestion-generation failures return a retryable `503` while the independent answer response remains successful, and that source revalidation fetches only saved identities while changed hashes and unavailable/disabled sources are excluded from generation and basis counts.
- [ ] **Step 3: Run the endpoint tests and confirm failure.**

Run: `python -m pytest services/api/tests/test_chat_suggestions.py -q`
Expected: collection/import failure for the missing chat router or models.

- [ ] **Step 4: Define strict Pydantic v2 models** with `extra="forbid"` for `{session_id: str, message_id: str}`, the public `Suggestion` shape, category/evidence literals, and a response capped at four.
- [ ] **Step 5: Implement the generator** using the configured existing LLM provider settings and a strict JSON candidate schema that includes internal supporting source IDs. Keep generation content limited to the re-fetched message snapshot and user question. Reject quote-like source overlap, fatwa/ruling solicitations in supported languages, and text that does not satisfy a question/instruction check.
- [ ] **Step 6: Implement the endpoint flow:** load by browser/session/message; return the same generic `404` for missing and other-browser records; re-fetch only saved source identities; re-check current source permission/readiness and exact content hashes; exclude changed or unavailable sources from the generator; gate on empty/low-score retrieval; generate candidates; require every supporting source ID to be non-empty, unique, and in the current message's approved set; enforce category rules against each candidate's support set; derive `basisCount` and `evidence` server-side; return up to four survivors. Return `200` with `suggestions: []` for valid empty/low-score results and `503` for suggestion-only store/provider/generation failures. Never include source IDs or browser details in errors.
- [ ] **Step 7: Register the router** at `/api/v1/chat` and run the complete endpoint test file.

Run: `python -m pytest services/api/tests/test_chat_suggestions.py -q`
Expected: PASS, including the user-requested retrieval/filter cases.

## Chunk 3: API client and accessible suggestion component

### Task 5: Add frontend contracts and API methods

**Files:**
- Modify: `apps/web/src/lib/api/client.ts`
- Modify: `apps/web/src/lib/api/client.test.ts`

- [ ] **Step 1: Add failing API client tests** for forwarding the session ID, batch prompt list, and exact suggestion request body `{session_id, message_id}`; test typed `suggestions` responses and HTTP error propagation.
- [ ] **Step 2: Run the targeted client tests and confirm failure.**

Run: `npm test -- --runInBand src/lib/api/client.test.ts`
Working directory: `apps/web`
Expected: FAIL because the new API methods/types are missing.

- [ ] **Step 3: Add TypeScript `Suggestion` and response types** matching the API contract, extend answer response metadata/sections, and add typed methods for answer batch submission and `POST /api/v1/chat/suggestions`.
- [ ] **Step 4: Run client tests and TypeScript check.**

Run: `npm test -- --runInBand src/lib/api/client.test.ts && npm run typecheck`
Working directory: `apps/web`
Expected: PASS.

### Task 6: Build the follow-up selection component

**Files:**
- Create: `apps/web/src/components/workspace/SuggestedFollowUps.tsx`
- Create: `apps/web/src/components/workspace/SuggestedFollowUps.test.tsx`

- [ ] **Step 1: Write failing component tests** for four-card loading skeleton, hidden empty/error states, category labels, API `AI_SYNTHESIS` displayed as `AI-SYNTHESIS`, multi-select `aria-pressed`, keyboard activation, disabled submit at zero, clear without submission, selected-prompt callback order, and refresh invoking a refetch.
- [ ] **Step 2: Run the focused test and confirm failure.**

Run: `npm test -- --runInBand src/components/workspace/SuggestedFollowUps.test.tsx`
Working directory: `apps/web`
Expected: FAIL because the component is absent.

- [ ] **Step 3: Implement the component** with API-fed titles/prompts only. Use `useQuery` scoped by session/message IDs. Render a two-column card grid, Thai category labels, basis text, selected check icon, main “ถามข้อที่เลือก (N)” button, clear button, and “คำแนะนำชุดอื่น” refresh action. Use real buttons, `aria-pressed`, visible focus rings, preserve selection order in the submit callback, and hide the entire component for empty/error responses.
- [ ] **Step 4: Run the component tests and typecheck.**

Run: `npm test -- --runInBand src/components/workspace/SuggestedFollowUps.test.tsx && npm run typecheck`
Working directory: `apps/web`
Expected: PASS.

## Chunk 4: Reader conversation history, integration, and verification

### Task 7: Integrate Grounded dialogue history in Reader

**Files:**
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/app/page.test.tsx`

- [x] **Step 1: Add failing integration tests** for retained turns with suggestions attached to the right answer, single and multi-prompt submission, independent section citations, and the Reader AI-tab context.
- [x] **Step 2: Add the toolbar regression test** asserting “ถาม AI” opens dialogue mode `explain` and keeps the selected surah/ayah in the question context.
- [x] **Step 3: Run the focused tests and confirm failure.**

Run: `npm test -- --runInBand src/components/workspace/GroundedDialogue.test.tsx app/page.test.tsx`
Working directory: `apps/web`
Expected: FAIL on missing history/component behavior and the toolbar integration regression.

- [x] **Step 4: Integrate dialogue history in Reader state** with a stable browser session UUID, per-answer suggestions, and independently cited batch sections.
- [x] **Step 5: Submit one selected prompt verbatim as the user message.** For multiple prompts, format one numbered message and send the same ordered prompt list as structured batch metadata. Clear selections after a successful response and preserve state when answer submission fails.
- [x] **Step 6: Keep current Reader navigation and AI-tab behavior** and ensure `openAiExplanation` retains the selected ayah.
- [x] **Step 7: Run integration tests and all focused frontend tests.**

Run: `npm test -- --runInBand src/components/workspace/GroundedDialogue.test.tsx src/components/workspace/SuggestedFollowUps.test.tsx app/page.test.tsx`
Working directory: `apps/web`
Expected: PASS.

### Task 8: Final verification and review loop

**Files:**
- Verify only; do not modify unrelated dirty files.

- [x] **Step 1: Run all API tests and compilation.**

Run: `python -m pytest services/api/tests -q && python -m compileall services/api`
Working directory: repository root
Result: compilation passed; focused API tests passed. The full suite reports 8 pre-existing async tests without an async marker, while the other 183 tests pass.

- [x] **Step 2: Run frontend typecheck, complete Jest suite, and production build.**

Run: `npm run typecheck && npm test -- --runInBand && npm run build`
Working directory: `apps/web`
Result: all commands exit 0; Jest reports 126 passing tests.

- [ ] **Step 3: Verify browser layout and behavior** at card widths 480px, 720px, and 850px. Automated component/integration tests cover selection and rendering; a live suggestion flow remains blocked because the local API at port 8011 is unavailable/CORS-blocked.
- [x] **Step 4: Review the implementation diff** for source authorization, browser isolation, score provenance, candidate supporting-source validation, and no fabricated religious content. The reviewer found and the implementation fixed the session query binding, missing semantic grounding gate, and short-quote filter; the follow-up review found no significant remaining issues.
- [x] **Step 5: Report actual test/build results and any environment limitation.** Do not run Alembic against production or stage unrelated worktree changes.

## Execution notes

- Follow `@superpowers:test-driven-development` for each behavior task and `@superpowers:verification-before-completion` before reporting success.
- Use the existing dirty worktree without resetting or staging unrelated files.
- The Alembic migration is authored and tested but is not applied automatically; deployment requires a separately approved disposable-development migration run.
- Do not add a local Tafsir fallback, hard-coded suggestion content, or a new dependency.
