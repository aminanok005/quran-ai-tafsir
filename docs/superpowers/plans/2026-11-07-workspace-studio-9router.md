# Workspace Studio and Local 9Router Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalize the three-panel workspace and the Audio, Quiz, and Infographic flows, with safe local-only generation and explicit saving of validated artifacts to browser-scoped Notes.

**Architecture:** Keep the existing Next.js, FastAPI, and PostgreSQL boundaries. The API validates the selected ayah, reads Tafsir only from its existing approved in-memory cache, enforces development/loopback 9Router configuration, and validates strict per-kind JSON before returning server-created citations. The browser requests generation only after a manual click, renders and edits the validated envelope locally, and creates a Note only after an explicit Save action.

**Tech Stack:** Next.js 14, React, TypeScript, TanStack Query, FastAPI, Pydantic, PostgreSQL, pytest, Jest, React Testing Library, Bun.

---

## File map

- `services/api/data/surah_ayah_counts.json` - the shared canonical 114-entry verse-count metadata currently embedded in the Quran seeder.
- `services/api/services/quran_metadata.py` - loads and validates the shared local Quran metadata for citation identity checks.
- `scripts/seed_quran_data.py` - reads the shared counts rather than maintaining a second copy.
- `services/api/services/quran_foundation_tafsir.py` - exposes a cache-only lookup without changing the existing live-fetch route behavior.
- `services/api/services/studio_artifact_contracts.py` - strict Pydantic schemas and per-kind validation for the new Audio, Quiz, and Infographic contracts.
- `services/api/services/studio_generation.py` - prompts for the new `content` shape for the three in-scope kinds, validates it, and authenticates the mocked/local provider request correctly; preserves legacy kinds.
- `services/api/routers/workspace.py` - development/loopback guard, cache-only Tafsir grounding, citation construction, and the target-kind response envelope; existing Notes endpoints and browser identity remain intact.
- `services/api/tests/test_quran_metadata.py`, `services/api/tests/test_quran_foundation_tafsir.py`, `services/api/tests/test_studio_generation.py`, `services/api/tests/test_workspace.py` - offline tests for metadata, cache behavior, schemas, provider transport, route guards, citations, and Notes.
- `apps/web/jest.config.js`, `apps/web/package.json`, `bun.lock` - configure the existing Jest runner for React DOM tests; add only its required `jest-environment-jsdom` environment.
- `apps/web/src/lib/api/client.ts` - typed target-kind requests and artifact envelopes.
- `apps/web/src/lib/studio-artifact-validation.ts` - browser-side edit validation for `{ title, summary, content }`.
- `apps/web/src/components/workspace/StudioArtifactView.tsx` - Audio, Quiz, Infographic, and citation rendering.
- `apps/web/src/components/workspace/StudioArtifactView.test.tsx`, `apps/web/src/lib/studio-artifact-validation.test.ts` - focused offline UI and edit-validation tests.
- `apps/web/src/components/workspace/WorkspacePanels.tsx` - connect generation, editable preview, validated export, and explicit Note-save behavior while leaving other artifact kinds unchanged.
- `apps/web/src/lib/workspace-layout.ts`, `apps/web/src/components/workspace/WorkspaceMobileTabs.tsx` - isolate existing persistence/shortcut behavior and mobile tabs for direct tests without changing their UX.
- `apps/web/src/lib/workspace-layout.test.ts`, `apps/web/src/components/workspace/WorkspaceMobileTabs.test.tsx` - verify layout persistence, shortcut focus guards, and mobile tab selection.
- `apps/web/app/page.test.tsx` - page-level integration coverage for persisted panel state, shortcut-driven panel visibility, and mobile tab rendering with mocked API/query/panel dependencies.
- `apps/web/app/page.tsx` - wire the extracted layout helpers and save the exact artifact envelope with the specified source label.
- `README.md`, `services/api/README.md` - document the local-only generation guard, cache prerequisite, and offline verification.

## Chunk 1: API safety, Quran metadata, and strict artifact contracts

### Task 1: Share and validate canonical verse-count metadata

**Files:**
- Create: `services/api/data/surah_ayah_counts.json`
- Create: `services/api/services/quran_metadata.py`
- Modify: `scripts/seed_quran_data.py`
- Test: `scripts/test_seed_quran_data.py`
- Test: `services/api/tests/test_quran_metadata.py`

- [ ] **Step 1: Write failing tests for the shared counts**

Add tests that load the metadata and assert there are exactly 114 positive integer counts, their sum is 6236, and the boundary counts include Surah 1 = 7, Surah 2 = 286, and Surah 114 = 6. Test the metadata validator rejects zero, negative, and boolean entries. Add `is_valid_ayah(surah, ayah)` cases for `(1, 1)`, `(1, 7)`, `(1, 8)`, `(114, 6)`, `(114, 7)`, and out-of-range surah numbers.

- [ ] **Step 2: Run the metadata tests and confirm they fail**

Run: `PYTHONPATH=. pytest scripts/test_seed_quran_data.py services/api/tests/test_quran_metadata.py -q`
Expected: FAIL because the shared metadata module/file and validation helper do not exist yet.

- [ ] **Step 3: Move the existing count table to one shared source**

Move the exact `SURAH_AYAH_COUNTS` values from `scripts/seed_quran_data.py` into `services/api/data/surah_ayah_counts.json`. Add `services/api/services/quran_metadata.py` to load that file once, validate every value is an integer but not a boolean, enforce its length, positivity, and total at import, expose the immutable counts, and implement `is_valid_ayah`. Update the seeder to use that same file; do not introduce a second copy of the values.

- [ ] **Step 4: Run the metadata tests**

Run: `PYTHONPATH=. pytest scripts/test_seed_quran_data.py services/api/tests/test_quran_metadata.py -q`
Expected: PASS, including the existing seeder total-count checks and the new citation-boundary cases.

- [ ] **Step 5: Commit the metadata boundary**

```bash
git add services/api/data/surah_ayah_counts.json services/api/services/quran_metadata.py scripts/seed_quran_data.py scripts/test_seed_quran_data.py services/api/tests/test_quran_metadata.py
git commit -m "refactor: share canonical Quran verse counts"
```

### Task 2: Add a no-network Tafsir cache accessor

**Files:**
- Modify: `services/api/services/quran_foundation_tafsir.py`
- Test: `services/api/tests/test_quran_foundation_tafsir.py`

- [ ] **Step 1: Write cache-only lookup tests**

Test that a fresh `(resource_id, surah, ayah)` entry is returned, a missing entry returns `None`, and an expired entry returns `None`. Replace or spy on `_fetch_ayah_uncached` so each test fails if lookup attempts a request.

- [ ] **Step 2: Run the focused tests and confirm the new cases fail**

Run: `PYTHONPATH=. pytest services/api/tests/test_quran_foundation_tafsir.py -q`
Expected: the existing cache tests pass and the new `get_cached_ayah` tests fail because that accessor is not implemented.

- [ ] **Step 3: Implement the cache-only accessor**

Add synchronous `get_cached_ayah(resource_id, surah, ayah) -> QuranFoundationTafsir | None`. Return only entries whose monotonic expiry is still in the future; remove an expired entry before returning `None`. Do not call `fetch_ayah`, `_fetch_ayah_uncached`, authentication, or HTTP from this method.

- [ ] **Step 4: Run the focused tests**

Run: `PYTHONPATH=. pytest services/api/tests/test_quran_foundation_tafsir.py -q`
Expected: PASS, with zero mocked transport requests from cache-only lookup.

- [ ] **Step 5: Commit the cache boundary**

```bash
git add services/api/services/quran_foundation_tafsir.py services/api/tests/test_quran_foundation_tafsir.py
git commit -m "feat: expose cache-only Tafsir lookup"
```

### Task 3: Enforce strict target-kind schemas and provider authentication

**Files:**
- Create: `services/api/services/studio_artifact_contracts.py`
- Modify: `services/api/services/studio_generation.py`
- Test: `services/api/tests/test_studio_generation.py`

- [ ] **Step 1: Add failing contract tests**

Cover valid and invalid Audio, Quiz, and Infographic content:

```python
def test_audio_requires_thai_alternating_hosts_and_bounded_segments():
    with pytest.raises(StudioGenerationError):
        validate_studio_artifact("audio", valid_title, valid_summary, invalid_audio_content)

def test_quiz_requires_five_three_choice_questions_and_non_boolean_answer_index():
    with pytest.raises(StudioGenerationError):
        validate_studio_artifact("quiz", valid_title, valid_summary, invalid_quiz_content)

def test_infographic_rejects_unknown_nested_fields_and_out_of_range_cards():
    with pytest.raises(StudioGenerationError):
        validate_studio_artifact("infographic", valid_title, valid_summary, invalid_infographic_content)
```

Also test the exact bounds from the spec: title 1-160 characters; summary 0-500; Audio 4-8 segments with each Thai-script text 1-1,200 characters and alternating Host A/Host B starting with Host A; Quiz exactly five questions, each question 1-500 characters, exactly three options each 1-200 characters, `answer_index` an integer 0-2 but not a boolean, and explanation 1-1,000 characters; Infographic takeaway 1-500 characters, 3-6 cards, headings 1-100 characters, and 2-5 points per card of 1-280 characters. Test unknown fields at every object depth.

- [ ] **Step 2: Test the configured provider request with a mock transport**

Use `httpx.MockTransport` only. Assert the Responses endpoint path, JSON-only request, and source context. Assert the `Authorization` header is built from the documented `Bearer` scheme and the test-only key `unit-test-key`; return a valid sample body and assert the resulting target-kind value contains only `title`, `summary`, and `content`. Add mock 401 and transport-error cases, assert each makes exactly one provider request, and use `caplog` plus exception assertions to verify neither the test key nor source text appears in logs or surfaced errors. Never use the configured live 9Router URL in a test.

- [ ] **Step 3: Run generation tests and confirm the new cases fail**

Run: `PYTHONPATH=. pytest services/api/tests/test_studio_generation.py -q`
Expected: FAIL for the missing strict validator and incorrect/missing provider authorization behavior; existing legacy-kind tests remain unchanged.

- [ ] **Step 4: Implement strict schemas and target-kind generation**

Use Pydantic models with `extra="forbid"` recursively for shared fields, Audio segments, Quiz questions/options, and Infographic cards. Enforce the tested bounds and requirements from the approved spec. For only `audio`, `quiz`, and `infographic`, ask the model for `{ "title", "summary", "content" }` and validate the returned object before returning it. Preserve the existing legacy output/validation path for `report`, `slides`, `video`, `flashcards`, and `comparison`. Set `Authorization` to the documented `Bearer` scheme followed by `api_key`; never include the key or source text in logs or surfaced errors.

- [ ] **Step 5: Run generation tests**

Run: `PYTHONPATH=. pytest services/api/tests/test_studio_generation.py -q`
Expected: PASS with all network interactions served by `MockTransport`.

- [ ] **Step 6: Commit strict generation contracts**

```bash
git add services/api/services/studio_artifact_contracts.py services/api/services/studio_generation.py services/api/tests/test_studio_generation.py
git commit -m "feat: validate structured Studio artifacts"
```

### Task 4: Gate generation and return server-built citations

**Files:**
- Modify: `services/api/routers/workspace.py`
- Test: `services/api/tests/test_workspace.py`
- Test: `services/api/tests/test_quran_metadata.py`

- [ ] **Step 1: Add failing route tests for safe generation**

Mock `generate_artifact`, the permission lookup, and the Tafsir client. Assert the route rejects non-development settings, missing provider configuration, non-loopback/malformed provider URLs, invalid ayah pairs, missing Quran selection, unapproved Tafsir, and an expired/missing Tafsir cache entry before calling the generator. Assert missing configuration tells the user which setting is missing, and a cache miss instructs the user to load the Tafsir passage first. Assert the cache-miss case never calls `fetch_ayah` or any HTTP transport.

- [ ] **Step 2: Add failing target-envelope and citation tests**

For each target kind, assert the success payload and nested artifact have exactly the approved keys, and every source has exactly `id`, `label`, and `url`. Source IDs are unique, Quran appears once, Tafsir is present only when selected/approved/cached, evidence is exactly `AI-SYNTHESIS`, and URLs/labels are server-built. Assert the Quran URL is `https://quran.com/<surah>/<ayah>`. Assert the Tafsir URL is exactly `{configured_content_api_base}/tafsirs/{resource_id}/by_ayah/{surah}:{ayah}`, and reject the cached passage unless its `verse_key` equals the selected `{surah}:{ayah}`. Add negative cases for a non-HTTPS Content API base and a host that differs from the configured Quran Foundation host. Assert legacy kinds keep their existing response shape.

- [ ] **Step 3: Run the route tests and confirm the new cases fail**

Run: `PYTHONPATH=. pytest services/api/tests/test_workspace.py services/api/tests/test_quran_metadata.py -q --asyncio-mode=auto`
Expected: FAIL for missing development/loopback/cache-only/envelope behavior; existing Notes and legacy artifact tests continue to execute.

- [ ] **Step 4: Implement route guards and cache-only grounding**

Require `ENVIRONMENT == "development"` and a parsed provider host of `localhost`, `127.0.0.1`, or `::1` before generation. Validate the selected ayah with `is_valid_ayah`. For a selected Tafsir, retain the configured resource and server-side approved-permission checks, then use only `get_cached_ayah`; return an actionable conflict response on cache miss. Do not accept client Tafsir text, approval, or citation URL. Keep the existing per-browser rate limit and Notes behavior.

- [ ] **Step 5: Build citations and the exact target-kind envelope**

Construct citation IDs, labels, and URLs on the server. Validate the configured Content API URL is HTTPS and its host matches the configured Quran Foundation host before creating a Tafsir citation. Return the exact target envelope for the three in-scope kinds; leave legacy kinds on their established response shape.

- [ ] **Step 6: Run route tests**

Run: `PYTHONPATH=. pytest services/api/tests/test_workspace.py services/api/tests/test_quran_metadata.py -q --asyncio-mode=auto`
Expected: PASS. Every provider and source boundary is mocked; no external request is made.

- [ ] **Step 7: Commit route behavior**

```bash
git add services/api/routers/workspace.py services/api/tests/test_workspace.py services/api/tests/test_quran_metadata.py
git commit -m "feat: gate grounded Studio generation"
```

## Chunk 2: Typed web contracts and Studio interactions

### Task 5: Configure DOM tests using the existing Jest runner

**Files:**
- Create: `apps/web/jest.config.js`
- Modify: `apps/web/package.json`
- Modify: `bun.lock`

- [ ] **Step 1: Add the minimal DOM test environment dependency**

Add `jest-environment-jsdom` to `apps/web` devDependencies and configure `next/jest` with `testEnvironment: "jsdom"`. Keep the existing `jest` script and existing Jest/React Testing Library packages; do not add another runner or user-event package.

- [ ] **Step 2: Install/update the existing Bun lockfile**

Run: `bun install`
Expected: Bun installs the required Jest DOM environment and updates `bun.lock` with only the required dependency changes.

- [ ] **Step 3: Verify Jest discovers an empty targeted test selection cleanly**

Run: `bun --cwd apps/web run test --runInBand --passWithNoTests`
Expected: Jest starts through `next/jest` and exits successfully with no tests selected. The later React Testing Library tests must render DOM elements and exercise click events, verifying the configured jsdom environment is active.

- [ ] **Step 4: Commit the test environment**

```bash
git add apps/web/jest.config.js apps/web/package.json bun.lock
git commit -m "test: configure web component test environment"
```

### Task 6: Add typed API envelope and client-side edit validation

**Files:**
- Modify: `apps/web/src/lib/api/client.ts`
- Create: `apps/web/src/lib/studio-artifact-validation.ts`
- Test: `apps/web/src/lib/studio-artifact-validation.test.ts`

- [ ] **Step 1: Add failing edit-validation tests**

Test valid per-kind `{ title, summary, content }` edits and rejection of malformed JSON, unknown top-level/nested fields, whitespace-only required strings, and these boundaries: title 1-160 characters; summary 0-500; Audio 4-8 Thai-script segments of 1-1,200 characters, with only `Host A`/`Host B`, starting at `Host A` and alternating; Quiz exactly five questions, each with a 1-500-character prompt, three 1-200-character options, an integer-but-not-boolean answer index 0-2, and 1-1,000-character explanation; Infographic takeaway 1-500 characters, 3-6 cards, 1-100-character headings, and 2-5 points of 1-280 characters, with optional `layout_hint` restricted to `stacked`, `two-column`, or `sequence`. For every numeric/string limit and array count, test both the accepted boundary and one value beyond it. Verify omitting `layout_hint` is valid. Verify validation returns a usable error message and never mutates the immutable server metadata.

- [ ] **Step 2: Run the edit-validation tests and confirm they fail**

Run: `bun --cwd apps/web run test --runInBand src/lib/studio-artifact-validation.test.ts`
Expected: FAIL because the validator and target envelope types do not exist yet.

- [ ] **Step 3: Define discriminated target-kind types**

Add TypeScript types for the Audio, Quiz, and Infographic `content` values, the `{ id, label, url }` source entries, and the exact artifact envelope. Type `createStudioArtifact` to return the existing `{ success, data }` wrapper with a union for the three target kinds and preserve legacy artifact compatibility.

- [ ] **Step 4: Implement browser edit validation**

Parse only `{ title, summary, content }` from editor text and validate against the active kind, mirroring the API's string, array, Thai-script, count, and nested-field constraints. Return a discriminated valid/error result; do not use casts to force malformed JSON into the artifact type.

- [ ] **Step 5: Run the edit-validation tests**

Run: `bun --cwd apps/web run test --runInBand src/lib/studio-artifact-validation.test.ts`
Expected: PASS.

- [ ] **Step 6: Commit typed client contracts**

```bash
git add apps/web/src/lib/api/client.ts apps/web/src/lib/studio-artifact-validation.ts apps/web/src/lib/studio-artifact-validation.test.ts
git commit -m "feat: type and validate Studio artifact edits"
```

### Task 7: Render target artifacts, citations, and local Audio/Quiz controls

**Files:**
- Create: `apps/web/src/components/workspace/StudioArtifactView.tsx`
- Create: `apps/web/src/components/workspace/StudioArtifactView.test.tsx`
- Modify: `apps/web/src/components/workspace/WorkspacePanels.tsx`

- [ ] **Step 1: Write failing view tests**

Use mocked artifact data and mocked `window.speechSynthesis`. Test that:
- Audio renders the ordered host segments, speaks the Thai segment text through a Thai voice, stops/cancels playback, and explains unsupported browser or unavailable Thai voice.
- Quiz renders exactly five three-choice questions, immediately displays correctness and explanation, and keeps progress/score in component state only.
- Infographic renders its takeaway and cards responsively using the validated layout hint; assert the selected `data-layout`/layout class for `stacked`, `two-column`, and `sequence`.
- Citation pills render below the artifact title as clickable links using the response's server-created URLs and labels; target artifacts do not invent URLs from model content.
- A legacy kind such as `slides` still renders through its existing renderer.

- [ ] **Step 2: Run the view tests and confirm they fail**

Run: `bun --cwd apps/web run test --runInBand src/components/workspace/StudioArtifactView.test.tsx`
Expected: FAIL because the specialized target-kind view is not implemented.

- [ ] **Step 3: Implement focused artifact renderers**

Add small kind-specific renderers in `StudioArtifactView.tsx`. Keep browser speech local: queue the Audio segment text with a discovered Thai voice, expose Play/Stop, cancel on Stop/unmount, and surface unsupported/missing-voice status. Use no external media API and persist no playback or quiz progress.

- [ ] **Step 4: Connect the specialized renderers**

Update `WorkspacePanels.tsx` to render the new component only for `audio`, `quiz`, and `infographic`; preserve the existing renderer for all other artifact kinds.

- [ ] **Step 5: Run the view tests**

Run: `bun --cwd apps/web run test --runInBand src/components/workspace/StudioArtifactView.test.tsx`
Expected: PASS without browser/provider network access.

- [ ] **Step 6: Commit the focused renderers**

```bash
git add apps/web/src/components/workspace/StudioArtifactView.tsx apps/web/src/components/workspace/StudioArtifactView.test.tsx apps/web/src/components/workspace/WorkspacePanels.tsx
git commit -m "feat: render Studio audio quiz and infographics"
```

### Task 8: Make generation, editing, export, and Note save explicit and safe

**Files:**
- Modify: `apps/web/src/components/workspace/WorkspacePanels.tsx`
- Modify: `apps/web/app/page.tsx`
- Test: `apps/web/src/components/workspace/StudioArtifactView.test.tsx`
- Test: `apps/web/src/lib/studio-artifact-validation.test.ts`

- [ ] **Step 1: Add failing Studio action tests**

Assert mount and source-selection changes call neither the artifact endpoint nor a provider; selecting an artifact kind also does not generate. One explicit Generate click calls the API once. Test visible errors for missing configuration, provider authorization/unavailability, invalid generated output, an unapproved-source permission rejection, and a Tafsir cache miss; also test invalid-edit preview preservation and that invalid edits disable both Export and Save.

- [ ] **Step 2: Add failing export and Note-save tests**

For a valid edit, assert Export creates a downloadable JSON file whose parsed contents are the full envelope with edited `title`, `summary`, and `content` plus unchanged `kind`, server `sources`, and `evidence_status`. Assert Save calls the existing Notes API once with exact `JSON.stringify(envelope)`, selected ayah identity, edited title, and each exact source-label form:
`Quran <surah name> <surah>:<ayah>` or `Quran <surah name> <surah>:<ayah>; <Tafsir resource name>`.

- [ ] **Step 3: Run focused Studio tests and confirm the new cases fail**

Run: `bun --cwd apps/web run test --runInBand src/components/workspace/StudioArtifactView.test.tsx src/lib/studio-artifact-validation.test.ts`
Expected: FAIL on the existing full-envelope editor/export/save and explicit-action gaps.

- [ ] **Step 4: Implement guarded editor and immutable metadata**

For target kinds, edit only `{ title, summary, content }`. Keep the last valid preview visible while invalid text is being corrected, show validation errors, and disable Export/Save until valid. Build the downloadable and saved envelope from validated editable fields plus immutable response metadata. Leave legacy-kind editor behavior unchanged.

- [ ] **Step 5: Preserve the manual-generation boundary**

Keep the artifact request inside the Generate click handler only; set mutation retry to false and do not add generation to mount effects, selection effects, or query prefetching. Display the API's actionable detail for missing server configuration, loopback/authorization failures, unapproved-source permission rejection, invalid model output, and Tafsir cache misses without automatic fallback.

- [ ] **Step 6: Wire exact Notes metadata**

Pass the complete validated target envelope to a dedicated page callback. Use `apiClient.createNote` with the edited title, exact envelope JSON, selected ayah numbers, and source label computed from the envelope's source entries. Keep ordinary Reader note saving and browser-ID-scoped persistence unchanged.

- [ ] **Step 7: Run focused web tests**

Run: `bun --cwd apps/web run test --runInBand src/components/workspace/StudioArtifactView.test.tsx src/lib/studio-artifact-validation.test.ts`
Expected: PASS, including one-call-on-click behavior and exact Note payload assertions.

- [ ] **Step 8: Commit Studio action wiring**

```bash
git add apps/web/src/components/workspace/WorkspacePanels.tsx apps/web/src/components/workspace/StudioArtifactView.test.tsx apps/web/src/lib/studio-artifact-validation.test.ts apps/web/app/page.tsx
git commit -m "feat: save validated Studio artifacts as notes"
```

## Chunk 3: Workspace persistence, documentation, and final verification

### Task 9: Test and preserve layout shortcuts and mobile navigation

**Files:**
- Create: `apps/web/src/lib/workspace-layout.ts`
- Create: `apps/web/src/lib/workspace-layout.test.ts`
- Create: `apps/web/src/components/workspace/WorkspaceMobileTabs.tsx`
- Create: `apps/web/src/components/workspace/WorkspaceMobileTabs.test.tsx`
- Create: `apps/web/app/page.test.tsx`
- Modify: `apps/web/app/page.tsx`

- [ ] **Step 1: Write failing layout helper tests**

Cover storage key `quran-workspace-layout`, valid persisted visibility/sizes, malformed JSON fallback with the existing warning behavior, and ignoring non-positive/non-finite layout sizes. Cover `[` toggling Sources and `]` toggling Studio, and confirm those shortcuts are ignored for input, textarea, select, and content-editable targets.

- [ ] **Step 2: Write failing mobile-tab tests**

Render the mobile tabs, select Reader/Sources/Dialogue/Studio, and assert the selected tab state and callback. Keep the existing labels and active/inactive presentation.

- [ ] **Step 3: Add page-level integration tests**

Render the actual page inside a real `QueryClientProvider`, mock `apiClient` responses and the Sources/Studio panel contents, and replace `PanelGroup` with a deterministic test double that can invoke `onLayout`. Verify a changed layout and visibility are written to `quran-workspace-layout` and restored on remount. Dispatch `[` and `]` and verify the corresponding actual panel is shown/hidden; dispatch the same keys from an input and verify visibility is unchanged. Select each mobile tab and assert the matching page content and selected tab update. All APIs are mocked; these tests must make zero network calls.

- [ ] **Step 4: Run the new tests and confirm they fail**

Run: `bun --cwd apps/web run test --runInBand src/lib/workspace-layout.test.ts src/components/workspace/WorkspaceMobileTabs.test.tsx app/page.test.tsx`
Expected: FAIL because the extracted helpers, tab component, and page-level behavior tests do not exist.

- [ ] **Step 5: Extract existing behavior without changing defaults**

Move only the storage parsing/serialization and editable-target shortcut decision into `workspace-layout.ts`; keep the same key, state shape, defaults, warning, panel sizes, and shortcut mapping. Extract the existing mobile tab strip into `WorkspaceMobileTabs.tsx` and wire it from `page.tsx`.

- [ ] **Step 6: Run the layout and mobile-tab tests**

Run: `bun --cwd apps/web run test --runInBand src/lib/workspace-layout.test.ts src/components/workspace/WorkspaceMobileTabs.test.tsx app/page.test.tsx`
Expected: PASS for layout save/restore, focus guards, actual panel visibility, and mobile tab selection.

- [ ] **Step 7: Commit the workspace behavior**

```bash
git add apps/web/src/lib/workspace-layout.ts apps/web/src/lib/workspace-layout.test.ts apps/web/src/components/workspace/WorkspaceMobileTabs.tsx apps/web/src/components/workspace/WorkspaceMobileTabs.test.tsx apps/web/app/page.test.tsx apps/web/app/page.tsx
git commit -m "refactor: isolate workspace layout behavior"
```

### Task 10: Document constraints and run offline verification

**Files:**
- Modify: `README.md`
- Modify: `services/api/README.md`
- Verify: API and web tests/typecheck

- [ ] **Step 1: Document the operational contract**

Document the non-secret setting names `ENVIRONMENT`, `LLM_API_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and `LLM_API_WIRE_API=responses`; state that `LLM_API_KEY` is server-only and must never reach client code, logs, or error responses. Explain that the API requires development mode and a loopback provider host. Also document that the three target kinds call that 9Router only after a manual Generate click, Tafsir grounding must already be loaded, approved, and present in the short-lived API cache, tests make no external requests, and artifacts persist only through Save to Note. Do not add or reveal credential values.

- [ ] **Step 2: Run targeted API tests**

Run: `PYTHONPATH=. pytest scripts/test_seed_quran_data.py services/api/tests/test_quran_metadata.py services/api/tests/test_quran_foundation_tafsir.py services/api/tests/test_studio_generation.py services/api/tests/test_workspace.py -q --asyncio-mode=auto`
Expected: PASS; generation and Quran Foundation transports are mocked and zero external requests occur.

- [ ] **Step 3: Run targeted web tests and typecheck**

Run: `bun --cwd apps/web run test --runInBand src/components/workspace/StudioArtifactView.test.tsx src/components/workspace/WorkspaceMobileTabs.test.tsx src/lib/studio-artifact-validation.test.ts src/lib/workspace-layout.test.ts app/page.test.tsx`
Expected: PASS.

Run: `bun run typecheck`
Expected: PASS with no TypeScript errors.

- [ ] **Step 4: Check the final diff**

Run: `git diff --check && git diff --cached --check`
Expected: no whitespace errors in unstaged or staged changes. Review both diffs and ensure no `.env.local` contents, credentials, generated artifacts, or unrelated worktree edits are staged.

- [ ] **Step 5: Commit documentation**

```bash
git add README.md services/api/README.md
git commit -m "docs: explain local Studio generation boundaries"
```

Follow `@superpowers:test-driven-development` for each implementation task and `@superpowers:verification-before-completion` before claiming the work is done. Do not make a live 9Router or Quran Foundation request during automated verification. The recorded 9Router `401 invalid_api_key` remains a manual configuration issue and is not a reason to weaken the local-only guard or add an automated provider request.
