# Feature D: Expert-Lane Audio Architecture and Lightweight Parallel Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish production-ready boundaries for three specialist lanes—Frontend/Audio Expert, Backend/Go Expert, and Systems/Rust Expert—while keeping current Reader behavior lightweight, source-grounded, and safe to evolve.

**Architecture:** Current production path stays Next.js + FastAPI until replacement services prove parity. Frontend owns Reader UI, playback state, Web Audio, native fallback, IndexedDB, and cancellation. A future Go lane owns high-throughput HTTP streaming, Range handling, concurrency limits, and audio proxying. A future Rust lane owns optional async worker/codec experiments behind a process boundary; it never replaces sacred-text or Tafsir source authority. All lanes communicate through versioned contracts, test fixtures, and measurable acceptance gates.

**Tech Stack:** TypeScript, React/Next.js, Web Audio API, IndexedDB, Jest, Python/FastAPI, Go HTTP/concurrency stack, Rust async/codec stack, Quran Foundation API, existing SQLAlchemy layer.

**Spec:** `docs/superpowers/specs/2026-11-08-smart-translation-audio-design.md`; reference architecture: `arriqaaq/ilm` resource/API boundaries and evidence-linked domain objects. Reference code/data requires independent license and source-permission review.

## Global Constraints

- Preserve edition mapping: `th.thai`, `en.sahih`, `id.indonesian`, and reciter `ar.alafasy`.
- Preserve exact Quran Arabic text, translation text, Tafsir source text, attribution, evidence status, and permission gates.
- Never fabricate Quran, Tafsir, translation, citation, or audio metadata when an upstream source fails.
- No Rust/Go runtime enters production path until contract, security, performance, and parity gates pass.
- Frontend remains fully functional without Go/Rust services; FastAPI remains fallback control plane.
- Parallel loading stays bounded: current item plus at most one next-item preload per sequence.
- AI context contains selected verse text, approved Tafsir passages, user question, and citation IDs only.
- Abort stale fetch, decode, speech, worker, and playback work on Stop, navigation, settings changes, and unmount.
- Never disable browser security or use unrestricted CORS.
- Each expert lane owns tests and documentation for its boundary; integration changes require contract tests.

## Expert Lanes

### Frontend/Audio Expert — React + Web Audio API

Owns `apps/web`, Reader state, native audio fallback, Web Audio crossfade, IndexedDB, cache keys, cancellation, accessibility, and browser compatibility. Must work when Go/Rust lanes are absent.

### Backend/Go Expert — HTTP + Concurrency

Owns future same-origin audio proxy and streaming service. Must support Range requests, bounded concurrency, timeouts, host allowlisting, SSRF protection, streaming, cache headers, and safe errors. Go service remains optional until benchmark proves value over FastAPI/native playback.

### Systems/Rust Expert — Async + Audio Codec

Owns future isolated worker experiments: async pipeline, codec validation/transcoding, bounded queues, cancellation, and memory limits. Rust must not own Quran/Tafsir truth, source permissions, or unvalidated text transformation. No CPAL/native device integration in first milestone.

## Review Focus

- Cross-origin CDN without CORS uses native playback; same-origin/proxy audio uses Web Audio and cache.
- Go proxy cannot SSRF, buffer unbounded files, lose Range semantics, or leak provider data.
- Rust worker cannot block, leak buffers, ignore cancellation, or mutate source text.
- A failed next preload/worker job never stops current playback or advances Auto incorrectly.
- Tafsir upstream `401`, timeout, malformed response, and missing passage fail closed with no substitute.

---

### Task 1: Freeze Cross-Lane Contracts

**Files:**
- Create: `docs/architecture/reader-audio-contract.md`
- Create: `docs/architecture/audio-service-contract.md`
- Create: `docs/architecture/reader-event-contract.md`
- Modify: `docs/architecture/OVERVIEW.md`
- Test: `apps/web/src/lib/quran/parallel-audio-loader.test.ts`

**Interfaces:**
- Produces stable contracts for `AudioRequest`, `AudioResponse`, `Range`, `CacheStatus`, `PlaybackEvent`, `Cancellation`, and `TafsirPassageEnvelope`.
- Contract rules: JSON metadata uses explicit version; audio uses `Content-Type`, `Content-Length`, `Accept-Ranges`, `Content-Range`, `ETag`; errors use safe codes, never secrets/provider bodies.

- [ ] **Step 1: Write contract fixtures**
  - Define valid current audio response, `206` response, cancellation event, cache hit/miss event, and source-attributed Tafsir envelope.
- [ ] **Step 2: Add contract assertions**
  - Assert required fields, version, source IDs, evidence status, and safe error shape.
- [ ] **Step 3: Document ownership and compatibility**
  - Mark Frontend as current producer/consumer; Go/Rust as future producers behind adapters.
- [ ] **Step 4: Run checks**
  - Run: `cd apps/web && npm test -- --runInBand src/lib/quran/parallel-audio-loader.test.ts`
  - Expected: PASS.
- [ ] **Step 5: Commit**
  - Run: `git add docs/architecture/reader-audio-contract.md docs/architecture/audio-service-contract.md docs/architecture/reader-event-contract.md docs/architecture/OVERVIEW.md apps/web/src/lib/quran/parallel-audio-loader.test.ts && git commit -m "docs: freeze reader audio service contracts"`

### Task 2: Frontend/Audio Expert Lane

**Files:**
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/src/lib/quran/reader-audio-playback.ts`
- Modify: `apps/web/src/lib/quran/web-audio-engine.ts`
- Modify: `apps/web/src/lib/quran/parallel-audio-loader.ts`
- Modify: `apps/web/src/lib/quran/audio-idb-cache.ts`
- Test: `apps/web/src/lib/quran/reader-audio-playback.test.ts`
- Test: `apps/web/src/lib/quran/web-audio-engine.test.ts`
- Test: `apps/web/app/page.test.tsx`

**Interfaces:**
- Consumes: Task 1 contracts and per-ayah Quran Cloud audio metadata.
- Produces: browser-only Reader that works without Go/Rust, routes cross-origin CDN to native audio, routes same-origin/proxy audio to Web Audio/cache, and bounds preload to one next ayah.

- [ ] **Step 1: Write failing browser tests**
  - Cover CDN native path, same-origin Web Audio path, cache hit/miss, one-next preload, stop/navigation/unmount cancellation, offline cached playback, and stale callback suppression.
- [ ] **Step 2: Run focused tests to verify failure**
  - Run: `cd apps/web && npm test -- --runInBand src/lib/quran/reader-audio-playback.test.ts src/lib/quran/web-audio-engine.test.ts app/page.test.tsx`
- [ ] **Step 3: Implement minimal frontend path**
  - Keep current UI and API compatibility; no Go/Rust hard dependency.
  - Preserve native audio fallback and exact ayah numbering.
  - Emit status for native, cached, generated, offline, and failed playback.
- [ ] **Step 4: Run focused tests**
  - Expected: PASS.
- [ ] **Step 5: Commit**
  - Run: `git add apps/web/app/page.tsx apps/web/src/lib/quran/reader-audio-playback.ts apps/web/src/lib/quran/web-audio-engine.ts apps/web/src/lib/quran/parallel-audio-loader.ts apps/web/src/lib/quran/audio-idb-cache.ts apps/web/src/lib/quran/reader-audio-playback.test.ts apps/web/src/lib/quran/web-audio-engine.test.ts apps/web/app/page.test.tsx && git commit -m "feat: harden frontend audio lane"`

### Task 3: Backend/Go Expert Lane — Isolated Streaming Proxy Spike

**Files:**
- Create: `services/audio-gateway-go/README.md`
- Create: `services/audio-gateway-go/go.mod`
- Create: `services/audio-gateway-go/cmd/server/main.go`
- Create: `services/audio-gateway-go/internal/httpaudio/handler.go`
- Create: `services/audio-gateway-go/internal/httpaudio/handler_test.go`
- Create: `services/audio-gateway-go/contracts/audio-response.json`

**Interfaces:**
- Consumes: structured audio request `{reciter, surah, ayah}`; never arbitrary user URL.
- Produces: `200`/`206` streamed audio matching Task 1 headers and safe error codes.

- [ ] **Step 1: Write failing Go tests**
  - Test allowlisted reciter/path, SSRF rejection, Range parsing, `206` headers, invalid Range, upstream timeout, response-size bound, concurrency limit, and cancellation.
- [ ] **Step 2: Run tests to verify failure**
  - Run: `cd services/audio-gateway-go && go test ./...`
  - Expected: FAIL before implementation.
- [ ] **Step 3: Implement isolated handler**
  - Use standard `net/http`; stream with `io.Copy`, bounded transport/client, semaphore, context cancellation, and allowlisted source builder.
  - Do not add database access, Quran/Tafsir logic, text processing, or provider credentials.
- [ ] **Step 4: Run tests and benchmarks**
  - Run: `cd services/audio-gateway-go && go test ./... && go test -race ./...`
  - Run: `go test -bench . ./internal/httpaudio`
  - Expected: PASS; record latency, memory, and concurrency results.
- [ ] **Step 5: Integration gate**
  - Keep service disabled unless native playback fails a documented product requirement and benchmark shows proxy benefit.
- [ ] **Step 6: Commit**
  - Run: `git add services/audio-gateway-go && git commit -m "spike: isolate bounded Quran audio gateway"`

### Task 4: Systems/Rust Expert Lane — Isolated Async Codec Spike

**Files:**
- Create: `services/audio-worker-rs/README.md`
- Create: `services/audio-worker-rs/Cargo.toml`
- Create: `services/audio-worker-rs/src/main.rs`
- Create: `services/audio-worker-rs/src/protocol.rs`
- Create: `services/audio-worker-rs/src/worker.rs`
- Create: `services/audio-worker-rs/tests/cancellation.rs`

**Interfaces:**
- Consumes: versioned audio job `{job_id, source_format, target_format, bytes_limit}` through stdin/HTTP adapter.
- Produces: versioned `{job_id, status, output_format, byte_length, error_code}`; never alters Quran/Tafsir text or source attribution.

- [ ] **Step 1: Write failing Rust tests**
  - Cover bounded queue, cancellation, malformed job, codec rejection, output-size bound, worker timeout, and graceful shutdown.
- [ ] **Step 2: Run tests to verify failure**
  - Run: `cd services/audio-worker-rs && cargo test`
  - Expected: FAIL before implementation.
- [ ] **Step 3: Implement minimal async worker**
  - Use bounded channels, cancellation tokens, explicit byte limits, and deterministic error codes.
  - No CPAL, device playback, database, Quran text, Tafsir, or AI provider calls.
- [ ] **Step 4: Run tests and checks**
  - Run: `cd services/audio-worker-rs && cargo fmt --check && cargo test && cargo clippy --all-targets --all-features`
  - Expected: PASS.
- [ ] **Step 5: Integration gate**
  - Keep worker disconnected from production until codec need, licensing, benchmark, and deployment ownership are approved.
- [ ] **Step 6: Commit**
  - Run: `git add services/audio-worker-rs && git commit -m "spike: isolate bounded async audio worker"`

### Task 5: FastAPI/Go/Rust Adapter and Fallback Gate

**Files:**
- Modify: `services/api/app.py` only when Go adapter is enabled
- Create: `services/api/services/audio_gateway_adapter.py` only when Go adapter is enabled
- Modify: `apps/web/src/lib/quran/parallel-audio-loader.ts`
- Test: `services/api/tests/test_audio_gateway_adapter.py` only when enabled
- Test: `apps/web/src/lib/quran/parallel-audio-loader.test.ts`

**Interfaces:**
- Consumes: Task 1 contract and optional Go/Rust service endpoints.
- Produces: fallback order `native CDN -> Go proxy -> Rust worker` only when each capability is explicitly enabled and healthy; no silent provider substitution.

- [ ] **Step 1: Write failing adapter tests**
  - Verify disabled services never receive requests, unhealthy services fall back safely, and capability errors remain visible.
- [ ] **Step 2: Implement capability-gated adapter**
  - Add explicit health/capability checks and timeouts; preserve FastAPI/native operation when adapters are absent.
- [ ] **Step 3: Run tests**
  - Run focused frontend/backend adapter tests.
  - Expected: PASS.
- [ ] **Step 4: Commit only after gate approval**
  - Record benchmark, security review, license review, and deployment owner before enabling any adapter.

### Task 6: Source-Grounded Tafsir and Compact AI Lane

**Files:**
- Modify: `services/api/services/quran_foundation_tafsir.py`
- Modify: `services/api/routers/tafsir.py`
- Modify: `services/api/services/agent_orchestrator.py`
- Modify: `services/api/routers/agents.py`
- Test: `services/api/tests/test_quran_foundation_tafsir.py`
- Test: `services/api/tests/test_tafsir_translation.py`
- Test: `services/api/tests/test_agent_orchestrator.py`

**Interfaces:**
- Consumes: approved source passages and selected ayah/question.
- Produces: source-attributed Tafsir envelope and compact AI context with token/character budget; no fallback Tafsir.

- [ ] **Step 1: Write failing tests**
  - Cover Surah 1 Ayahs 1–7, OAuth `401/403`, timeout, malformed passage, missing records, database unavailable, duplicate context, unapproved sources, and context budget.
- [ ] **Step 2: Run backend tests**
  - Run: `.venv/bin/python -m pytest -q services/api/tests/test_quran_foundation_tafsir.py services/api/tests/test_tafsir_translation.py services/api/tests/test_agent_orchestrator.py`
- [ ] **Step 3: Implement safe classification and compact context**
  - Preserve strict resource/source checks, permission gates, citation IDs, and fail-closed errors.
  - Deduplicate passages and cap context; never send full corpus/surah by default.
- [ ] **Step 4: Run tests**
  - Expected: PASS.
- [ ] **Step 5: Commit**
  - Run: `git add services/api/services/quran_foundation_tafsir.py services/api/routers/tafsir.py services/api/services/agent_orchestrator.py services/api/routers/agents.py services/api/tests && git commit -m "feat: bound source-grounded tafsir and ai context"`

### Task 7: Full Validation, Benchmarks, and Documentation

**Files:**
- Create: `docs/architecture/reader-expert-lanes.md`
- Create: `docs/architecture/audio-cross-lane-benchmarks.md`
- Modify: `docs/architecture/OVERVIEW.md`
- Modify: `README.md` only if feature status is stale

**Interfaces:**
- Consumes: completed expert lanes and contracts.
- Produces: integration decision record, benchmark results, ownership boundaries, and rollback/fallback procedure.

- [ ] **Step 1: Frontend validation**
  - Run: `cd apps/web && npm test -- --runInBand && npm run typecheck && npm run build`
- [ ] **Step 2: Backend validation**
  - Run: `.venv/bin/python -m pytest -q services/api/tests/test_config.py services/api/tests/test_quran_foundation_tafsir.py services/api/tests/test_tafsir_translation.py services/api/tests/test_agent_orchestrator.py`
- [ ] **Step 3: Go/Rust validation when lanes exist**
  - Run Go tests/race/benchmarks and Rust format/test/clippy checks.
- [ ] **Step 4: Manual regression**
  - Verify Arabic RTL, Thai translation, Surah 1 Ayahs 1–7, navigation, Auto, Stop, native CDN audio, same-origin cache, Tafsir error state, agent selection, and stale cancellation.
- [ ] **Step 5: Document decisions**
  - Record why `ilm` is reference-only, why native audio is default, when Go proxy is enabled, when Rust worker is enabled, license/data review, and low-token policy.
- [ ] **Step 6: Commit**
  - Run: `git add docs/architecture/reader-expert-lanes.md docs/architecture/audio-cross-lane-benchmarks.md docs/architecture/OVERVIEW.md README.md && git commit -m "docs: define expert audio architecture and gates"`

---

## Completion Criteria

- [ ] Three expert lanes have explicit ownership, contracts, tests, and integration gates.
- [ ] Frontend works without Go/Rust services.
- [ ] Cross-origin CDN audio produces no CORS Blob-fetch error.
- [ ] Go spike proves safe streaming/concurrency before optional enablement.
- [ ] Rust spike proves bounded async/cancellation before optional enablement.
- [ ] At most one next audio item preloads per sequence.
- [ ] Tafsir failures stay explicit and fail closed; no fabricated content appears.
- [ ] AI context stays within configured token/character budget and retains citation IDs.
- [ ] Frontend, backend, Go, Rust, benchmark, and manual regression gates pass before production integration.
