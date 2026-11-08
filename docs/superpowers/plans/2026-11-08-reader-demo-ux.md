# Reader Demo UX Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the three-panel Reader/Studio workspace clearer and resilient on first load, with accurate loading, empty, error, and retry states for Quran data.

**Architecture:** Keep the existing Next.js Reader, local Quran API routes, and Sources/Reader/Studio panel architecture. Validate verse-list response shapes at the Reader boundary so a successful empty array is distinct from malformed or unavailable Quran data. Improve state presentation in the existing Reader canvas without adding mock Quran content or changing Tafsir/provider contracts.

**Tech Stack:** Next.js 14, React, TypeScript, Tailwind CSS, Jest, React Testing Library, Playwright browser tools.

---

## File map

- `apps/web/app/page.tsx` — Reader data normalization, loading/error/empty states, and selected-ayah presentation.
- `apps/web/app/page.test.tsx` — Page integration tests using the existing mocked Quran fetch boundary.
- `docs/superpowers/specs/2026-11-08-reader-demo-ux-design.md` — approved scope and no-fallback constraints.

## Chunk 1: Reliable Reader loading and recovery

### Task 1: Specify the Reader's Quran-data states in tests

**Files:**
- Modify: `apps/web/app/page.test.tsx`
- Reference: `apps/web/app/page.tsx`
- Reference: `apps/web/app/api/quran/surahs/[surah]/ayahs/route.ts`

- [ ] **Step 1: Add a deferred-response test for initial loading**

Add a test that holds the `/api/quran/surahs/1/ayahs/` request pending while the page renders. Assert the Reader exposes an accessible busy/loading state and does not render an empty-result message before the request resolves.

- [ ] **Step 2: Run the focused test and verify the expected failure**

Run: `cd apps/web && bun run test -- --runInBand app/page.test.tsx -t "shows loading"`

Expected: FAIL because the current loading skeleton does not expose the specified accessible status contract.

- [ ] **Step 3: Add tests for empty, malformed, missing, and unavailable Quran data**

Cover these independent outcomes:

1. A successful top-level `[]` and a successful `{ ayahs: [] }` response each render the empty state.
2. A successful response with a missing collection (`{}`) or null collection (`{ ayahs: null }`) renders the error state, not the empty state.
3. A malformed collection (`{ ayahs: {} }`) and a non-record item inside a verse array are each treated as malformed data rather than silently filtered into an empty result.
4. A non-OK response with a detail message renders an error and retry control; after retry succeeds, the selected Quran ayah appears.

Keep the existing successful QPC response fixture and assertions as the loaded-state regression, including its selected ayah.

- [ ] **Step 4: Run the focused tests and verify failures are behavioral**

Run: `cd apps/web && bun run test -- --runInBand app/page.test.tsx`

Expected: the newly added state-contract tests fail on the current implementation; existing page integration tests remain green.

### Task 2: Implement strict loading, empty, and retry presentation

**Files:**
- Modify: `apps/web/app/page.tsx`
- Test: `apps/web/app/page.test.tsx`

- [ ] **Step 1: Add a strict Quran verse-list parser**

Keep the existing permissive `listOf` helper for unrelated translation/audio metadata. Add a Reader-specific parser accepting a top-level array or one of the existing supported envelope keys (`data`, `surahs`, `ayahs`, `translations`) only when its value is an array containing records. Throw a descriptive error for missing/null collections, malformed envelopes, or non-record array entries; do not convert these cases to `[]`.

- [ ] **Step 2: Use strict parsing at the Quran-data boundary**

Use the strict parser for the local surah list and selected-surah ayah response before setting success/empty state. A valid array with zero records is the only empty result. Preserve the existing route error detail behavior. Add an explicit request-version trigger for retries so clicking retry re-fetches the same selected surah instead of relying on setting the ayah state to its existing value.

- [ ] **Step 3: Make loading and error feedback accessible and visually clear**

Expose loading with a live status and `aria-busy` on the Reader result region. Keep skeletons while pending. Mark fetch failures as alerts, keep the actionable retry button, and style the successful empty state as a distinct quiet card. Tighten selected-ayah hierarchy with a calm but clear selected-card treatment and intentional spacing, retaining `aria-current` semantics. Preserve the current green palette, responsive panels, Arabic size control, navigation, translation/audio, and all citation/source behavior.

- [ ] **Step 4: Run the focused page integration tests**

Run: `cd apps/web && bun run test -- --runInBand app/page.test.tsx`

Expected: all page tests pass, including loading, strict error/empty distinction, retry-to-loaded, and existing layout/Notes behavior.

### Task 3: Verify the demo and responsive workspace

**Files:**
- No code changes expected unless verification identifies a defect covered by Tasks 1–2.

- [ ] **Step 1: Run the full web test suite and typecheck**

Run: `cd apps/web && bun run test -- --runInBand`

Expected: all web suites and tests pass.

Run: `cd apps/web && bun run typecheck`

Expected: TypeScript exits with code 0.

- [ ] **Step 2: Verify the live Reader API routes**

Check `http://localhost:<demo-port>/api/quran/surahs/` and
`http://localhost:<demo-port>/api/quran/surahs/1/ayahs/` return successful
responses, where `<demo-port>` is 3000 unless the fallback below is needed. Do
not print or inspect environment secrets.

- [ ] **Step 3: Inspect both demo entry points in the browser**

Open `http://localhost:<demo-port>` and
`http://localhost:<demo-port>/?view=reader`. Verify the landing page remains
unchanged, the Reader loads sourced Quran content (not a fixture), the selected
ayah is visually primary, and the panel layout is usable at desktop and mobile
viewport sizes.

If the existing server returns 404 for its own `/_next/static` assets, do not
terminate an unidentified process. Start a separate dev server and report that
the existing port-3000 demo needs its owner to restart it. Use:
`cd apps/web && bun run next dev --port 3001`
If Next reports that port 3001 is busy, use the actual alternate port reported
by Next. Set `<demo-port>` to the port printed in the successful server-ready
message for all API-route and browser checks.

- [ ] **Step 4: Check the final worktree and patch**

Run: `git diff --check && git status --short`

Expected: no whitespace errors; only the planned frontend files are modified.
