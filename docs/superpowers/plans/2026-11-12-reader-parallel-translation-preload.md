# Reader Parallel Translation Preload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preload at most one next-ayah generated translation audio item while current recitation plays, avoiding a duplicate request when playback reaches it.

**Architecture:** Extend existing Reader playback controller with one pending generated-audio preload keyed by surah, ayah, language, edition, and speed. Consume it on matching playback; cancel and dispose stale generated URLs through existing generation lifecycle. No backend or API changes.

**Tech Stack:** TypeScript, React, Web Audio/native audio playback, Jest.

**Spec:** `docs/superpowers/specs/2026-11-12-reader-parallel-translation-preload-design.md`

## Global Constraints

- Preload at most one next ayah per sequence.
- Preload only generated translation audio, and only in recitation-then-translation mode with enabled capabilities.
- Preload failure never interrupts current recitation or automatic progression.
- Abort stale work on Stop, navigation, settings changes, and unmount.
- Never modify Quran, translation, Tafsir text, source attribution, or evidence state.
- Add no dependency and make no backend/Go/Rust changes.

## Review Focus

- Preload failure leaves current recitation active — test rejected preload during current play.
- Matching preload is reused without duplicate API call — test same target key.
- Settings/navigation invalidates stale work — test abort and stale URL cleanup.
- Ayah boundaries do not preload missing next item — test final ayah.
- Speed/language changes do not consume wrong cached audio — test key mismatch triggers normal load.

---

### Task 1: Playback Controller Preload Lifecycle

**Files:**
- Modify: `apps/web/src/lib/quran/reader-audio-playback.ts`
- Test: `apps/web/src/lib/quran/reader-audio-playback.test.ts`

**Interfaces:**
- Reuse existing `loadGeneratedTranslationAudio(surah, ayah, language, speed, signal)` dependency.
- Add controller-local single-item preload state; keep API contract unchanged.

- [ ] Write failing tests for one-next-only cap, failure isolation, abort on stop/navigation, final-ayah guard, and reuse without duplicate request.
- [ ] Run `cd apps/web && npm test -- --runInBand src/lib/quran/reader-audio-playback.test.ts` and confirm new assertions fail.
- [ ] Implement smallest controller change: derive only immediate next ayah, key by coordinates/language/speed, await/consume matching preload before on-demand generation, abort and dispose stale results.
- [ ] Run the focused test file and confirm pass.

### Task 2: Reader Integration and Regression

**Files:**
- Modify: `apps/web/app/page.tsx` only if existing dependency wiring needs preload-specific disposal/status support.
- Test: `apps/web/app/page.test.tsx`
- Verify: `apps/web/src/lib/api/client.test.ts`

**Interfaces:**
- Consume Task 1 controller lifecycle; preserve existing API call and cache key semantics.

- [ ] Add integration test proving one next translation request is reused during combined playback; cover cache hit and settings change key mismatch.
- [ ] Implement only required Reader wiring; do not add duplicate fetch/cache layers.
- [ ] Run `cd apps/web && npm test -- --runInBand app/page.test.tsx src/lib/quran/reader-audio-playback.test.ts src/lib/api/client.test.ts`.
- [ ] Run `cd apps/web && npm run typecheck` and `git diff --check`.

## Completion Criteria

- At most one generated translation preload is in flight per sequence.
- Matching ayah playback consumes preload without a second API request.
- Failure/cancellation/stale-result paths preserve current audio playback.
- Focused tests, typecheck, and diff check pass.
