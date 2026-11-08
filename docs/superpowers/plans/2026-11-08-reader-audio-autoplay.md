# Reader Audio Playback UX Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace duplicate visible Alafasy controls with a single-ayah `Listen Audio` action, optional Thai/English/Indonesian spoken translation, and cancellable Auto playback that advances and scrolls ayah by ayah.

**Architecture:** Extend the existing Quran translation route's edition allowlist. Put audio sequencing, Web Speech voice selection, cancellation generations, and stale-event protection in a testable playback controller; keep its controls in a reusable Reader control component. Wire the controller to the existing Reader state and API-backed data loader, rendering the same controls in the desktop and mobile Reader canvases while keeping one shared internal audio element.

**Tech Stack:** Next.js 14 App Router, React, TypeScript, Jest, Testing Library, Quran Cloud editions, browser HTMLAudioElement and Web Speech API.

---

## File map

- Modify `apps/web/app/api/quran/surahs/[surah]/route.ts` to allow only the existing Thai, Alafasy, English, and Indonesian editions.
- Create `apps/web/app/api/quran/surahs/[surah]/route.test.ts` to exercise supported and rejected edition requests.
- Create `apps/web/src/lib/quran/reader-audio-playback.ts` as the browser-independent-by-injection playback coordinator. It owns sequence modes, voice matching/waiting, audio/TTS sequencing, cancellation generations, and callbacks; it does not fetch Quran content.
- Create `apps/web/src/lib/quran/reader-audio-playback.test.ts` with deterministic audio and speech-synthesis fakes for playback lifecycle tests.
- Create `apps/web/src/components/workspace/ReaderAudioControls.tsx` as the shared, accessible mode/language selector, `Listen Audio` / `Stop Audio`, `Auto` / `Stop Auto`, and live status UI.
- Create `apps/web/src/components/workspace/ReaderAudioControls.test.tsx` for control labels, selected values, and accessible status behavior.
- Modify `apps/web/app/page.tsx` to load only the selected playback translation edition, connect the controller and shared hidden audio element, stop playback on manual selection/settings changes/unmount, and render shared controls in both responsive Reader canvases.
- Extend `apps/web/app/page.test.tsx` for route integration, duplicate-player removal, selected-language data, auto navigation/scrolling, user interruption, and desktop/mobile control parity.

Keep the current uncommitted Reader UX changes in `page.tsx` and `page.test.tsx`; do not overwrite or discard those changes while implementing this plan.

## Chunk 1: Allow the supported translation editions

### Task 1: Specify the edition allowlist at the route boundary

**Files:**
- Create: `apps/web/app/api/quran/surahs/[surah]/route.test.ts`

- [ ] **Step 1: Write a failing route test for the existing and requested editions**

Create a test that calls the route's `GET` handler with `edition=th.thai`,
`edition=ar.alafasy`, `edition=en.sahih`, and `edition=id.indonesian`. For each
request, mock upstream `fetch` with a successful Quran Cloud response containing
`code: 200` and `data.ayahs`, then assert the handler returns HTTP 200 and the
same normalized `data` payload.

- [ ] **Step 2: Run the route test and confirm English/Indonesian are rejected**

Run: `cd apps/web && npm test -- --runInBand --runTestsByPath 'app/api/quran/surahs/[surah]/route.test.ts'`

Expected: FAIL for `en.sahih` and `id.indonesian` because the current handler
returns HTTP 400 for each; the existing Thai and Alafasy cases pass.

- [ ] **Step 3: Add rejection coverage for unrelated editions**

Add a test for an unsupported value such as `edition=ar.abdurrahmaansudais`.
Assert HTTP 400 and assert upstream `fetch` was not called. Restore the original
global fetch after each test.

- [ ] **Step 4: Run the route test to verify the rejection assertion**

Run: `cd apps/web && npm test -- --runInBand --runTestsByPath 'app/api/quran/surahs/[surah]/route.test.ts'`

Expected: The unsupported-edition test passes; the requested English/Indonesian
acceptance cases still fail.

### Task 2: Extend the explicit allowlist

**Files:**
- Modify: `apps/web/app/api/quran/surahs/[surah]/route.ts`
- Test: `apps/web/app/api/quran/surahs/[surah]/route.test.ts`

- [ ] **Step 1: Add only the two requested translation editions**

Add `en.sahih` and `id.indonesian` to `supportedEditions`. Keep `th.thai` and
`ar.alafasy`, and do not accept arbitrary edition strings.

- [ ] **Step 2: Run all route cases**

Run: `cd apps/web && npm test -- --runInBand --runTestsByPath 'app/api/quran/surahs/[surah]/route.test.ts'`

Expected: All four supported-edition cases return 200; an unrelated edition
returns 400 without an upstream call.

- [ ] **Step 3: Commit the route boundary change**

```bash
git add 'apps/web/app/api/quran/surahs/[surah]/route.ts' 'apps/web/app/api/quran/surahs/[surah]/route.test.ts'
git commit -m "feat: allow selected Quran translations"
```

## Chunk 2: Build and verify the playback coordinator and controls

### Task 3: Define playback behavior through controller tests

**Files:**
- Create: `apps/web/src/lib/quran/reader-audio-playback.test.ts`

- [ ] **Step 1: Add deterministic fake audio and speech adapters**

In the new test file, define small fakes for the audio element and speech
synthesis interface. Allow tests to dispatch `ended`, `error`, and
`voiceschanged` events and to inspect play, pause, utterance, and cancellation
calls. Use fake timers for the three-second voice discovery deadline.

- [ ] **Step 2: Test single-ayah recitation and spoken translation**

Assert recitation mode starts only the selected ayah URL, translation mode
waits for the selected ayah's translation and matching voice, and a missing
translation rejects playback with an error status.

- [ ] **Step 3: Test combined sequence ordering and non-overlap**

Assert combined mode waits for recitation `ended` before speaking the selected
translation, and waits for utterance completion before Auto advances. Assert
the next ayah does not begin until the current ayah's whole sequence completes.
Assert the controller emits one ayah-advance announcement per verse and does
not emit a separate progress announcement for the internal recitation-to-
translation transition.

- [ ] **Step 4: Test voice matching and discovery timeout**

Cover `th`, `en`, and `id` primary-language matching with locale variants;
initial empty and non-matching voice lists; a later matching `voiceschanged`
event; a non-matching event followed by a matching event; and timeout with no
matching voice. Assert the controller never uses an unrelated default voice.

- [ ] **Step 5: Test unsupported speech synthesis**

Run translation playback with speech synthesis unavailable. Assert playback
stops, an actionable error status is emitted, and neither a later ayah nor an
unrelated voice is used.

- [ ] **Step 6: Test replacement, stop, and stale callback suppression**

Cover Auto stopping at the final ayah, `stop()` resetting audio and cancelling
speech, each new start replacing the previous sequence, and late `ended`,
utterance, voice, or translation callbacks being ignored after a generation
change. Assert errors stop the sequence and do not advance it.

- [ ] **Step 7: Run the controller tests to confirm they fail first**

Run: `cd apps/web && npm test -- --runInBand 'src/lib/quran/reader-audio-playback.test.ts'`

Expected: FAIL because the controller module does not exist yet.

### Task 4: Implement the injected playback coordinator

**Files:**
- Create: `apps/web/src/lib/quran/reader-audio-playback.ts`
- Test: `apps/web/src/lib/quran/reader-audio-playback.test.ts`

- [ ] **Step 1: Define the typed controller interface**

Define playback mode as `recitation`, `translation`, or
`recitation-then-translation`; define translation language as `th`, `en`, or
`id`. Accept the shared audio element, a translation loader, and callbacks for
ayah selection and status. Expose start-single, start-auto, and stop operations.
Inject speech synthesis and voice-list event access so the module is testable
without relying on real browser audio.

- [ ] **Step 2: Implement language voice selection**

Match the first browser voice whose BCP-47 primary language equals the requested
language, case-insensitively. If the initial list has no match, wait for
`voiceschanged` up to three seconds from the playback request; continue waiting
through non-matching events. Reject with a user-displayable error at the
deadline, and never fall back to another language.

- [ ] **Step 3: Implement generation-based cancellation**

Increment a generation for every playback start and stop. Each awaited
translation, audio event, utterance callback, timeout, and ayah-change callback
must verify its captured generation before acting. Cancellation pauses and
resets audio, neutralizes its completion handler, cancels speech synthesis,
clears timers/listeners, and invalidates outstanding continuations.

- [ ] **Step 4: Implement single and automatic ayah sequences**

For each ayah, play the selected sequence serially. Auto selects the next
provided ayah only after the current sequence completes; it stops after the
last ayah. Resolve a matching speech voice once per playback sequence and reuse
it for its translation utterances. Surface audio, translation, and speech
failures through the status callback and do not advance on failure.

- [ ] **Step 5: Run the controller suite**

Run: `cd apps/web && npm test -- --runInBand 'src/lib/quran/reader-audio-playback.test.ts'`

Expected: All controller lifecycle, sequencing, voice, cancellation, and stale
event tests pass.

- [ ] **Step 6: Commit the controller**

```bash
git add apps/web/src/lib/quran/reader-audio-playback.ts apps/web/src/lib/quran/reader-audio-playback.test.ts
git commit -m "feat: coordinate Quran audio playback"
```

### Task 5: Specify the shared playback controls

**Files:**
- Create: `apps/web/src/components/workspace/ReaderAudioControls.test.tsx`

- [ ] **Step 1: Add control accessibility tests**

Test labeled native selectors for playback mode and translation language,
retention of `Listen Audio`, `Stop Audio` while a single-ayah sequence is
active, `Auto` / `Stop Auto` while auto mode is idle/active, and a single
live region with `role="status"` and `aria-live="polite"`, with playback,
ayah-advance, stop, error, and completion text. Assert both attributes and that
there is only one status region per rendered control component. Assert that the
language selector is absent in recitation mode and shown for both translation
modes. Check the control container has responsive wrapping/stacking classes so
the controls fit narrow screens.

- [ ] **Step 2: Run the controls tests to confirm they fail first**

Run: `cd apps/web && npm test -- --runInBand 'src/components/workspace/ReaderAudioControls.test.tsx'`

Expected: FAIL because the shared controls component does not exist yet.

### Task 6: Implement the responsive-safe controls component

**Files:**
- Create: `apps/web/src/components/workspace/ReaderAudioControls.tsx`
- Test: `apps/web/src/components/workspace/ReaderAudioControls.test.tsx`

- [ ] **Step 1: Implement the controlled component**

Accept mode, language, playback state, status, and typed callbacks as props.
Show the language selector only when the mode includes translation. Use
`Listen Audio` / `Stop Audio` and `Auto` / `Stop Auto` labels as specified.
Provide visible focus styles, labels, and one live status region. Keep mode and
language state in the Reader rather than duplicating state inside the component.

- [ ] **Step 2: Run the control tests**

Run: `cd apps/web && npm test -- --runInBand 'src/components/workspace/ReaderAudioControls.test.tsx'`

Expected: All control label, selector, live-status, and responsive-class tests
pass.

- [ ] **Step 3: Commit the controls component**

```bash
git add apps/web/src/components/workspace/ReaderAudioControls.tsx apps/web/src/components/workspace/ReaderAudioControls.test.tsx
git commit -m "feat: add Reader playback controls"
```

## Chunk 3: Connect Reader data and playback, then verify both layouts

### Task 7: Add Reader playback integration tests

**Files:**
- Modify: `apps/web/app/page.test.tsx`

- [ ] **Step 1: Add translation edition fixtures and fetch behavior**

Extend the local Quran test fetch mock with `en.sahih` and `id.indonesian`
translation responses. Assert the Reader requests only the selected spoken
translation edition in addition to the existing Thai display translation and
Alafasy data, and that malformed, missing, or failed selected translation
results produce a visible playback error.

- [ ] **Step 2: Add tests for the unified visible controls**

Assert both responsive Reader canvases render the shared controls with matching
mode/language state and callbacks, while the duplicate native Alafasy player
and repeated “เสียงอ่าน · อัลอะฟาซี” label are absent. Assert `Listen Audio`
remains present.

- [ ] **Step 3: Add Auto navigation, scroll, and interruption tests**

With the audio and speech adapters mocked, assert Auto advances selected ayah
after each full sequence, scrolls the next ayah into view, clears search when
started, and stops at the last ayah. Assert manual ayah/surah selection and
mode/language changes stop the sequence. Ensure Auto's own ayah callback
updates the selected ayah and URL without invoking the manual-navigation
cancellation path.

Also test that activating Auto during single-ayah playback replaces it with
Auto from the selected ayah, and activating `Listen Audio` during Auto stops
Auto and replaces it with single-ayah playback from the current ayah.

- [ ] **Step 4: Run the page tests and confirm missing integration**

Run: `cd apps/web && npm test -- --runInBand --runTestsByPath app/page.test.tsx`

Expected: New feature tests fail, while existing Reader tests continue to pass.

### Task 8: Wire the controller and translation loader into Reader

**Files:**
- Modify: `apps/web/app/page.tsx`
- Test: `apps/web/app/page.test.tsx`

- [ ] **Step 1: Add language and playback state**

Keep the current Thai translation map for the visible translation and saved
notes. Add controlled playback mode, language, playback status, and a completed
translation cache keyed by surah and edition. Load only the selected spoken
translation; reuse the current Thai map when Thai is selected.

- [ ] **Step 2: Add abortable translation loading**

Allow the local Quran request helper to accept an optional `AbortSignal`.
Normalize selected-edition responses with the existing strict Quran list
validator and map translation text by ayah number. Abort obsolete requests on
surah/edition change and unmount; ignore late results with a mismatched key.
Keep the existing non-abortable callers unchanged by making the signal optional.

- [ ] **Step 3: Mount one shared audio element and controller**

Mount one internal audio element at the Reader root, not inside either
responsive verse list. Create the controller after the element is available,
keep its callbacks current as React state changes, and stop/dispose it on
unmount. Wire playback errors and progress to the shared status state.

- [ ] **Step 4: Separate manual navigation from Auto's ayah updates**

Keep manual `selectAyah` and `selectSurah` as cancellation boundaries. Factor
the shared selected-ayah/URL/Tafsir update so the controller's Auto callback can
advance and scroll without stopping its own generation. On Auto start, clear
search and start from the current ayah. On control mode/language changes, stop
the current playback before updating selection.

- [ ] **Step 5: Add stable ayah targets and scroll on Auto advancement**

Add a stable ID to each verse article. In the controller callback, after the
current generation is verified and the ayah state updates, scroll the target
into the Reader viewport with centered positioning. Keep ordinary manual
selection and search behavior unchanged.

### Task 9: Render the shared controls in both Reader canvases

**Files:**
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/src/components/workspace/ReaderAudioControls.tsx`
- Test: `apps/web/app/page.test.tsx`
- Test: `apps/web/src/components/workspace/ReaderAudioControls.test.tsx`

- [ ] **Step 1: Replace both duplicate action/player blocks**

Render `ReaderAudioControls` from each responsive Reader canvas, passing the
same Reader-owned state and handlers. Remove the two native `controls` players
and their Alafasy-only labels. Keep the existing `Listen Audio` action as the
single-ayah control and render the single internal audio element only once.

- [ ] **Step 2: Run the page and control suites**

Run: `cd apps/web && npm test -- --runInBand --runTestsByPath app/page.test.tsx src/components/workspace/ReaderAudioControls.test.tsx src/lib/quran/reader-audio-playback.test.ts 'app/api/quran/surahs/[surah]/route.test.ts'`

Expected: All targeted tests pass with no duplicate visible player, and all
existing Reader behavior remains green.

- [ ] **Step 3: Run the full web Jest suite and typecheck**

Run: `cd apps/web && npm test -- --runInBand`

Expected: All web Jest suites pass.

Run: `cd apps/web && npm run typecheck`

Expected: TypeScript exits successfully with no errors.

- [ ] **Step 4: Verify the browser on desktop and mobile**

If no development server for this worktree is running, start it with
`cd apps/web && npm run dev -- --port 3000` and confirm Next.js serves port 3000 before using
`http://localhost:3000/?view=reader&surah=1&ayah=1`. Verify at a desktop
viewport of 1440x900 and a mobile viewport of 390x844.
If another service already owns port 3000, do not terminate it blindly; confirm
the current server is this worktree's app or resolve the port conflict safely
before claiming the localhost verification passed.
Confirm desktop and mobile each show one `Listen Audio` control, the language
selector appears only for translation modes, playback switches to stop labels,
Auto scrolls to the next ayah, and stopping or changing ayah prevents further
advancement. Confirm a missing language voice or translation reports an error
instead of silently falling back.

- [ ] **Step 5: Check the final diff and commit integration**

Run: `git diff --check`

Expected: No whitespace errors.

Before staging, inspect `git status --short` and
`git diff -- apps/web/app/page.tsx apps/web/app/page.test.tsx`. Preserve the
pre-existing Reader UX changes in those files; stage only the audio feature
hunks from them. Use `git add --patch` for those two files, then stage the new
feature files explicitly. Inspect `git diff --cached` and confirm no earlier
Reader UX hunks or other unrelated changes were staged. Commit only after that
review:

```bash
git add apps/web/src/components/workspace/ReaderAudioControls.tsx apps/web/src/components/workspace/ReaderAudioControls.test.tsx apps/web/src/lib/quran/reader-audio-playback.ts apps/web/src/lib/quran/reader-audio-playback.test.ts 'apps/web/app/api/quran/surahs/[surah]/route.ts' 'apps/web/app/api/quran/surahs/[surah]/route.test.ts'
git commit -m "feat: add continuous Quran audio playback"
```
