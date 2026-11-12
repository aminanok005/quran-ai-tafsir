# Smart Translation Audio Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in AI-generated audio for the selected Thai, English, or Indonesian Quran translation, with an explicit device-voice alternative and a compact Reader settings summary.

**Architecture:** Add a separately configured FastAPI TTS service and a rights-gated route that resolves exact translation text server-side, synthesizes it, and returns bounded cached audio bytes. Extend the existing Reader audio coordinator and API client to consume generated audio or explicitly selected browser speech; move playback options behind a collapsed summary that exposes real status and never silently falls back.

**Tech Stack:** FastAPI, Pydantic Settings, httpx, bounded in-memory TTL/LRU cache, Next.js/React, TypeScript, Jest, pytest.

---

## Files and responsibilities

- `services/api/config.py`: isolated TTS provider, approved editions, voice, timeout, size, cache, and rate-limit configuration; defaults keep TTS off.
- `services/api/services/translation_audio.py`: translation-source resolution, provider request/validation, bounded successful-audio cache, and rate limiting.
- `services/api/routers/translation_audio.py`: capability and audio-byte HTTP contracts, input validation, Redis-backed rate limiting, and safe HTTP errors.
- `services/api/app.py`: mount the new router under `/api/v1`; create one service during lifespan and close its clients at shutdown.
- `services/api/tests/test_config.py`: TTS configuration validation and disabled defaults.
- `services/api/tests/test_translation_audio.py`: service, cache, allowlist, provider, and API route tests with injected HTTP clients.
- `.env.example`: document safe opt-in setup and edition-rights responsibility without real keys.
- `apps/web/src/lib/api/client.ts`: typed capability and audio-byte requests.
- `apps/web/src/lib/quran/reader-audio-settings.ts`: typed edition mapping and AI availability decisions shared by Reader integration and focused tests.
- `apps/web/src/lib/quran/reader-audio-settings.test.ts`: all supported language mappings, allowed/disabled edition gates, and unavailable capabilities.
- `apps/web/src/lib/quran/reader-audio-playback.ts`: engine/rate options, asynchronous AI audio, cancellation, and URL lifecycle hooks.
- `apps/web/src/lib/quran/reader-audio-playback.test.ts`: sequence, error, cancellation, and resource lifecycle tests.
- `apps/web/src/components/workspace/ReaderAudioControls.tsx`: collapsed selection summary, accessible expanded settings, voice engine and rate choices, and visible status.
- `apps/web/src/components/workspace/ReaderAudioControls.test.tsx`: control state, summary, option, status, and accessibility behavior.
- `apps/web/app/page.tsx`: load capabilities, maintain Reader choices/status, provide generated audio URLs, and revoke resources on replacement/unmount.
- `apps/web/src/lib/quran/reader-audio-playback.test.ts`: integration-boundary tests for AI audio requests, URL cleanup, speed behavior, and Auto.

## Chunk 1: Secure, opt-in TTS API

### Task 1: Add independent validated TTS configuration

**Files:**
- Modify: `services/api/config.py`
- Test: `services/api/tests/test_config.py`

- [x] **Step 1: Write failing settings tests** for the disabled default, separate TTS credentials/model/base URL, approved-edition parsing, language voice mapping, rejection of invalid base URLs, limits, and unknown languages, acceptance of HTTP only for loopback development endpoints while requiring HTTPS for every other provider host, and positive bounds for source-response bytes and aggregate cache bytes.
- [x] **Step 2: Run the focused settings tests** with `pytest -q services/api/tests/test_config.py`; confirm the new fields are missing or invalid.
- [x] **Step 3: Implement typed configuration** with TTS disabled unless both provider credentials and an explicit edition allowlist are configured. Validate HTTP(S) provider URLs and bounded positive values, including `TTS_MAX_SOURCE_BYTES` and `TTS_CACHE_MAX_BYTES`; keep TTS credentials separate from all LLM settings.
- [x] **Step 4: Re-run the focused settings tests** and the existing config tests; require all to pass.

### Task 2: Implement source resolution, synthesis, cache, and API

**Files:**
- Create: `services/api/services/translation_audio.py`
- Create: `services/api/routers/translation_audio.py`
- Modify: `services/api/app.py`
- Test: `services/api/tests/test_translation_audio.py`

- [x] **Step 1: Write failing service and route tests** for disabled TTS, unsupported or non-allowlisted editions, invalid surah/ayah/speed, source failures/missing verses, mismatched returned surah/ayah identifiers, exact text passed to TTS, boolean and numeric-string values for both `data.number` and `ayahs[].numberInSurah` rejected before provider calls, actual configured Bearer-key delivery without secret leakage, provider timeout/status/content-type/size failures including slow-drip source and provider responses that exceed an absolute deadline, safe error responses, Redis-unavailable fail-closed behavior, concurrent requests through one atomic Lua increment-and-expire call per request, expiry/recreation of fake Redis keys, and capabilities that reveal no secrets. For this Quran Cloud `/surah/{surah}/{edition}` response, treat `data.number` as the returned surah identifier and `ayahs[].numberInSurah` as each returned ayah identifier; do not require a separate nested `ayah.surah.number` field.
- [x] **Step 2: Write failing cache tests** for cache miss/hit, source-text/model/voice/speed key differences, expiry cleanup, entry-count and aggregate-byte LRU eviction, skipping an item larger than the aggregate budget, and caching only validated successes.
- [x] **Step 3: Run the new focused API tests** with `pytest -q services/api/tests/test_translation_audio.py`; confirm expected failures before implementation.
- [x] **Step 4: Implement a test-injectable Quran Cloud resolver** using the fixed existing Reader source endpoint `https://api.alquran.cloud/v1/surah/{surah}/{edition}` and only the fixed `th.thai`, `en.sahih`, and `id.indonesian` edition map. Stream and bound the whole upstream body with `TTS_MAX_SOURCE_BYTES` before JSON parsing and enforce a total deadline for request plus stream consumption; separately test both an over-limit `Content-Length` precheck and an oversized streamed body without that header, asserting neither path calls the provider. Validate `data.number` as the requested surah and `ayahs[].numberInSurah` as the requested ayah using actual JSON integers (rejecting booleans/numeric strings), plus non-empty bounded text; never accept arbitrary text or a source URL from the request.
- [x] **Step 5: Implement bounded TTL/LRU caching** keyed by edition, verse, text hash, model, voice, and speed. Enforce both entry count and `TTS_CACHE_MAX_BYTES`, prune expired items during maintenance, skip oversized cache entries, and test hit, miss, expiry cleanup, and eviction.
- [x] **Step 6: Implement atomic Redis rate limiting** with a single Lua increment-and-expire operation and hashed keys based only on the direct request client address (never untrusted forwarded headers). Verify keys expire and raw IPs are not stored. Fail closed with a safe 503 if Redis is unavailable; share limits across workers.
- [x] **Step 7: Implement the configured OpenAI-compatible provider call** with the exact resolved translation and per-language voice, enforcing a total deadline for request plus stream consumption and an output-size bound. Validate MPEG response bytes/type; keep credentials and provider bodies out of logs/errors. Do not execute this step until the Redis limiter is implemented and fail-closed tests pass.
- [x] **Step 8: Add capability and MPEG response routes**, reporting only enabled editions/languages and cache outcome. Add `expose_headers=["X-Audio-Cache"]` to `CORSMiddleware` in `services/api/app.py` so the cross-origin Reader can read the cache outcome. Reject requests before provider calls unless the edition, TTS configuration, language mapping, verse, and rate limit pass. Make the dependency retrieve only the single service managed by app lifespan; do not lazily create clients per request.
- [x] **Step 9: Initialize one translation-audio service during FastAPI lifespan startup in `services/api/app.py`, store it in app state, and close its HTTP/Redis clients once during shutdown. Test that concurrent route requests reuse the same instance and that a GET with `Origin: http://localhost:3000` returns `Access-Control-Allow-Origin: http://localhost:3000` and `Access-Control-Expose-Headers` containing `X-Audio-Cache`; also test both clients close exactly once, Redis close is still attempted if HTTP close fails, HTTP close still completes if Redis close fails, either single cleanup error propagates, simultaneous ordinary close failures preserve both errors, and cancellation remains the propagated outcome while any secondary cleanup failure is recorded.**
- [x] **Step 10: Run `pytest -q services/api/tests/test_translation_audio.py services/api/tests/test_config.py`; require all tests to pass.**

### Task 3: Document safe operator opt-in

**Files:**
- Modify: `.env.example`
- Modify: `services/api/tests/test_config.py` (only if needed to lock environment-variable names)

- [x] **Step 1: Add commented TTS configuration examples** for provider URL, key placeholder, model, voice mapping, approved editions, timeout, text/source/audio bounds, cache byte/TTL limits, and rate limit. Keep TTS disabled unless an operator explicitly configures it.
- [x] **Step 2: Document the allowlist obligation inline**: verify source-edition permissions for external TTS processing before enabling an edition; do not copy any real credentials.
- [x] **Step 3: Validate config parsing** with the focused config test command; review the template to ensure example values cannot accidentally enable provider calls.

## Chunk 2: Reader playback and compact controls

### Task 4: Add typed API client operations

**Files:**
- Modify: `apps/web/src/lib/api/client.ts`
- Test: existing API client tests, if present; otherwise add a focused client test alongside the existing API library test conventions.

- [x] **Step 1: Add tests** for capability JSON parsing and malformed payload rejection, successful `audio/mpeg` blob retrieval and asserted `X-Audio-Cache` normalization (`hit`/`miss`/`unknown`), URL-encoded edition/speed query values, abort signal propagation, JSON and non-JSON non-OK responses, and invalid MIME type.
- [x] **Step 2: Run the focused client tests** and confirm the methods do not yet exist.
- [x] **Step 3: Add typed `getTranslationAudioCapabilities` and `getTranslationAudio` methods**, returning capabilities and `Blob` respectively and preserving caller abort signals.
- [x] **Step 4: Re-run the focused client tests** and confirm failures surface as controlled API errors rather than JSON parse errors or success-shaped fallbacks, and assert every cache status mapping.

### Task 5: Extend the playback coordinator for explicit engines

**Files:**
- Modify: `apps/web/src/lib/quran/reader-audio-playback.ts`
- Test: `apps/web/src/lib/quran/reader-audio-playback.test.ts`

- [x] **Step 1: Write failing tests** for device voice and AI voice in all three languages, AI speed forwarding, device utterance rate, Alafasy playback rate in recitation-only and combined modes, AI audio finishing before Auto advances, cache-hit status, and generation/playback failures that each produce actionable status, include `HTMLMediaElement.error.message` only when it is a non-empty string (otherwise show a generic retry/device-voice instruction) in the status callback, stop Auto, do not advance the ayah or fall back to device voice, and revoke generated URLs after failed playback. Test missing, null, empty-string, and non-string media-error messages, and repeated AI playback revoking each URL exactly once without retaining historical URL references. Also test that the three-second matching-device-voice deadline is measured from the initial playback request even when translation loading is slow, abort on stop/settings/navigation, stale callbacks, and URL revocation after completion/cancel/replacement.
- [x] **Step 2: Run the focused coordinator tests** with `npm test -- --runInBand src/lib/quran/reader-audio-playback.test.ts`; confirm new cases fail.
- [x] **Step 3: Extend typed sequence options and dependencies** with voice engine, speed, abortable generated-audio loader, and explicit object-URL cleanup ownership. Keep exact translation text for device speech and preserve the existing Alafasy source.
- [x] **Step 4: Implement AI audio playback through the shared audio element** and device speech through the existing matching-language logic. Keep generation guards around every asynchronous continuation; stop Auto on any error and never switch engines implicitly.
- [x] **Step 5: Re-run coordinator tests** and confirm existing recitation, device translation, combined mode, and cancellation tests remain green.

### Task 6: Collapse settings and show smart status

**Files:**
- Modify: `apps/web/src/components/workspace/ReaderAudioControls.tsx`
- Modify: `apps/web/src/components/workspace/ReaderAudioControls.test.tsx`

- [x] **Step 1: Write failing component tests** that settings are collapsed on mount; summary reflects mode/language/engine/speed and status; expansion exposes labeled controls; unavailable AI is disabled with an explanation; the consent disclosure is visible when AI is selected; status stays announced while collapsed; and `Listen Audio`/`Auto` remain available.
- [x] **Step 2: Run `npm test -- --runInBand src/components/workspace/ReaderAudioControls.test.tsx`** and confirm expected failures.
- [x] **Step 3: Implement the compact accessible disclosure button** with `aria-expanded` and a persistent polite live region. Keep selections in the expanded settings and clearly identify device voice when AI is unavailable.
- [x] **Step 4: Re-run the component tests** and confirm all selections and actions remain keyboard-operable and responsive.

### Task 7: Wire Reader capabilities, settings, and audio URLs

**Files:**
- Modify: `apps/web/app/page.tsx`
- Create: `apps/web/src/lib/quran/reader-audio-settings.ts`
- Test: `apps/web/src/lib/quran/reader-audio-settings.test.ts`
- Test: `apps/web/src/lib/quran/reader-audio-playback.test.ts`
- Test: `apps/web/src/components/workspace/ReaderAudioControls.test.tsx`

- [x] **Step 1: Extract and test focused integration helpers** for capability loading decisions, device default with an explicit unavailability reason, AI enablement only for an allowed selected edition, and language-to-edition mapping (`th.thai`, `en.sahih`, `id.indonesian`). Add a small page-level integration test if the current page test conventions support it without mocking away the behavior under test.
- [x] **Step 2: Run focused web tests** and confirm they fail before wiring.
- [x] **Step 3: Fetch capabilities without blocking Reader content**; provide generated audio via `apiClient`, create/revoke object URLs with explicit ownership, and pass status, mode, language, engine, rate, and callbacks through both responsive Reader surfaces. Make Alafasy and device speech honor the selected rate; pass that rate to AI synthesis once and do not apply it a second time to the generated audio.
- [x] **Step 4: Ensure mode/language/engine/rate changes and manual navigation stop old playback** before new options take effect; keep the settings disclosure collapsed after initial render.
- [x] **Step 5: Run all focused Reader tests** and check no visible duplicate recitation player is reintroduced.

## Chunk 3: Integrated verification and review loop

### Task 8: Run regression checks and independent code review

**Files:**
- Review all files changed by Tasks 1–7.

- [x] **Step 1: Run backend tests** with `pytest -q services/api/tests/test_translation_audio.py services/api/tests/test_config.py`.
- [x] **Step 2: Run the complete web Jest suite, type check, and production build** from `apps/web`: `npm test -- --runInBand`, `npm run typecheck`, and `npm run build`.
- [x] **Step 3: Inspect the complete diff and worktree**; verify no secrets, generated files, unrelated edits, or unsafe TTS default/edition settings have been added.
- [x] **Step 4: Dispatch an independent read-only code review** for the full diff, requesting concrete correctness, security, error-handling, privacy, accessibility, and test-coverage findings.
- [x] **Step 5: For every actionable finding, update this plan if scope or sequencing changes, add/adjust a regression test first, implement a focused fix, and rerun affected checks. Repeat the independent review until it reports no unresolved actionable findings; record any disputed suggestion with technical evidence rather than claiming an objective numeric perfection score.**
- [x] **Step 6: Verify the running Reader** at desktop and narrow viewport: settings start collapsed, summary/status are understandable, device voice is explicit, AI is only selectable when configured/allowed, and Listen/Auto operate without duplicate recitation controls.
