# Implementation Plan

## [Overview]

Implement the immediate next steps for the QURAN AI Super WebApp as defined in PHASE_CHECKLIST.md, focusing on unblocking Phase 2 (Knowledge Base & Hybrid RAG) database/source gates, validating Phase 3 (Multi-Agent Tafsir Engine) with approved data, and integrating the pending reader audio + translation audio feature work already in the worktree. The plan covers frontend (Next.js), backend (FastAPI), ingestion pipeline, database migrations/seeds, and shared types.

## [Types]

No new TypeScript or Python type system changes are required beyond what already exists. Existing types to leverage:

- `packages/shared-types/src/types/quran.d.ts` — `Surah`, `Ayah`, `Word`, `Translation`, `QuranSearchResponse`
- `packages/shared-types/src/types/tafsir.d.ts` — `TafsirSource`, `TafsirPassage`, `HadithReference`, `EvidenceGrade`, `TafsirExplanation`, `EvidenceLevel`, `CrossReference`, `ScholarlyComparison`, `Disagreement`, `Citation`
- `packages/shared-types/src/types/citation.d.ts` — `SourcePermission`, `CitationValidationResult`, `ValidationIssue`, `SourceQualityReport`, `SourceVerification`, `TafsirMetadata`, `AyahMapping`, `CitationStats`
- `packages/shared-types/src/types/agent.d.ts` — `AgentType`, `AgentConfig`, `AgentMethodology`, `RetrievalConfig`, `OutputSchema`, `QualityGate`, `AgentExecution`, `AgentContext`, `RetrievedSource`, `AgentOutput`, `CitationReference`, `ExecutionMetadata`, `TokenUsage`, `AgentStatus`, `AgentOrchestrationRequest`, `AgentOrchestrationResult`, `OrchestrationMetadata`, `AgentHealthCheck`, `HealthIssue`
- `services/api/models.py` — Pydantic models: `SurahModel`, `AyahModel`, `TranslationModel`, `EvidenceLevel`, `AgentType`, `UserRole`, `SearchRequestModel`, `ExecuteAgentRequest`, `CreateTafsirRequest`, etc.

## [Files]

### New files to create

1. `services/api/migrations/versions/0002_source_permissions.py` — Alembic migration creating `source_permissions` table (id, source_id, source_url, license, permission_status, verification_status, verification_evidence, created_at, updated_at).
2. `services/api/migrations/versions/0003_quran_seed_tables.py` — Alembic migration creating `surahs`, `ayahs`, `translations` seed tables if not already present.
3. `services/api/tests/test_source_permissions.py` — Unit tests for source permission CRUD and validation logic.
4. `scripts/test_database_seeding.py` — Disposable-database test that runs migrations + seeder and verifies all 6,236 ayahs.
5. `docs/superpowers/specs/2026-11-08-database-source-gates.md` — Design spec for Phase 2 database/source gates.
6. `docs/superpowers/plans/2026-11-08-phase2-database-validation.md` — Implementation plan for Phase 2 database validation.
7. `docs/superpowers/plans/2026-11-08-phase3-tafsir-validation.md` — Implementation plan for Phase 3 tafsir validation with approved sources.

### Existing files to modify

1. `services/api/config.py` — Add `source_permissions` table configuration if needed; ensure `DATABASE_URL` is required and validated.
2. `services/api/routers/agents.py` — Already imports `_get_api_source_permission`, `_translation_is_allowed`, `get_engine`, `get_qf_tafsir_client` from `tafsir.py`; verify agent endpoint uses approved sources only.
3. `services/api/routers/tafsir.py` — Already has `_translation_is_allowed` and `_get_api_source_permission`; verify translation endpoints enforce source rights.
4. `services/api/app.py` — Verify lifespan initializes database connection pool.
5. `apps/web/app/page.tsx` — Pending reader UX changes are already in the worktree (do not overwrite); integrate reader-audio-playback and ReaderAudioControls as specified in docs/superpowers/plans/2026-11-08-reader-audio-autoplay.md.
6. `apps/web/src/lib/api/client.ts` — Already has `getTafsirPassage`, `translateApiTafsirPassage`, `getAgentExplanation`, `compareAgents`, `generateFlashcards`, `generateQuiz`; verify types match backend responses.
7. `.env.example` — Already has `DATABASE_URL`, `QURAN_TAFSIR_RESOURCE_MAP`, `QURAN_API_*` settings; verify `source_permissions`-related env vars documented.

### Files already present in worktree (do not modify unless validation finds defects)

- `apps/web/app/api/quran/surahs/[surah]/route.ts` — Modified, allows th.thai, ar.alafasy, en.sahih, id.indonesian editions
- `apps/web/src/components/workspace/ReaderAudioControls.tsx` — New, shared audio controls
- `apps/web/src/lib/quran/reader-audio-playback.ts` — New, playback coordinator
- `services/api/routers/translation_audio.py` — New, TTS API endpoints
- `services/api/services/translation_audio.py` — New, TTS service
- `services/api/tests/test_translation_audio.py` — New, TTS tests

## [Functions]

### New functions

1. `validate_source_permission(engine, source_id)` in `services/api/routers/tafsir.py` — Returns bool whether a source is approved and verified for AI use. Reuses `_translation_is_allowed`.
2. `run_database_validation()` in `scripts/test_database_seeding.py` — Runs migrations + seeder against disposable DB, asserts 6,236 ayahs seeded.
3. `validate_phase3_tafsir(agent_type, surah, ayah)` in `services/api/tests/test_phase3_validation.py` — Tests agent execution with approved source passages only.

### Modified functions

1. `AgentOrchestratorService.execute_agent_analysis` in `services/api/services/agent_orchestrator.py` — Already requires `source_passages`; ensure it raises `ValueError` when no approved sources available (already implemented).
2. `_approved_source_passages` in `services/api/routers/agents.py` — Already filters by `settings.quran_tafsir_resource_map` and `_translation_is_allowed`; verify it returns empty list when no sources approved.

### Removed functions

None. No functions should be removed.

## [Classes]

### New classes

None required. Existing classes cover all needs.

### Modified classes

None required. Existing classes cover all needs.

### Removed classes

None.

## [Dependencies]

No new dependencies required. Existing dependencies:

**Frontend (bun):** Next.js 14+, React, TypeScript, Tailwind CSS, shadcn/ui, Zustand, Lucide React, @tanstack/react-query, react-resizable-panels, clsx, tailwind-merge
**Backend (pip/uv):** FastAPI, uvicorn, SQLAlchemy 2.0, pgvector, psycopg, pydantic, pydantic-settings, redis, httpx, alembic, openai, python-dotenv
**Ingestion (bun):** Shamela classical texts ingestion pipeline

No `pip install`, `bun install`, or `npm install` operations are required for this plan.

## [Testing]

### Test files to create

1. `services/api/tests/test_source_permissions.py` — Test `_translation_is_allowed` logic, source permission approval/rejection, and `source_permissions` table queries.
2. `scripts/test_database_seeding.py` — Disposable DB test: run `alembic upgrade head`, run `seed_quran_data.py`, assert 114 surahs and 6,236 ayahs.
3. `services/api/tests/test_phase3_validation.py` — Test that agent execution fails when no approved sources, succeeds with approved sources.

### Existing tests to run

- `services/ingestion/test_policy.py` — 6 ingestion policy unit tests (already passing)
- `scripts/test_seed_quran_data.py` — 3 Quran seeder unit tests (already passing)
- `apps/web/app/page.test.tsx` — Reader page integration tests
- `apps/web/src/components/workspace/ReaderAudioControls.test.tsx` — Audio controls tests
- `apps/web/src/lib/quran/reader-audio-playback.test.ts` — Playback coordinator tests
- `apps/web/app/api/quran/surahs/[surah]/route.test.ts` — Route edition allowlist tests
- `services/api/tests/test_config.py` — Backend config tests
- `services/api/tests/test_translation_audio.py` — TTS service tests

### Validation strategy

- Do NOT run migrations/seeds against production database; use disposable development data only
- Do NOT modify `.env`, `.env.local`, credentials, or PostgreSQL settings without explicit authorization
- Use mocked/offline LLM providers for Phase 3 validation while OpenAI quota error remains unresolved
- Frontend: `cd apps/web && bun run test -- --runInBand` then `bun run typecheck` then `bun run build`
- Backend: `pytest -q services/api/tests/` then Python compile check

## [Implementation Order]

1. **Create database migration for `source_permissions` table** — `services/api/migrations/versions/0002_source_permissions.py`
2. **Create database migration for Quran seed tables** — `services/api/migrations/versions/0003_quran_seed_tables.py`
3. **Create source permission validation tests** — `services/api/tests/test_source_permissions.py`
4. **Create disposable database seeding test** — `scripts/test_database_seeding.py`
5. **Create Phase 3 tafsir validation tests** — `services/api/tests/test_phase3_validation.py`
6. **Create Phase 2 database source gates design spec** — `docs/superpowers/specs/2026-11-08-database-source-gates.md`
7. **Create Phase 2 database validation plan** — `docs/superpowers/plans/2026-11-08-phase2-database-validation.md`
8. **Create Phase 3 tafsir validation plan** — `docs/superpowers/plans/2026-11-08-phase3-tafsir-validation.md`
9. **Run backend tests** — `pytest -q services/api/tests/test_source_permissions.py services/api/tests/test_config.py services/api/tests/test_translation_audio.py`
10. **Run frontend tests** — `cd apps/web && bun run test -- --runInBand`
11. **Run frontend typecheck** — `cd apps/web && bun run typecheck`
12. **Run frontend production build** — `cd apps/web && bun run build`
13. **Verify worktree diff** — `git diff --check && git status --short`; inspect for secrets, generated files, unrelated edits
14. **Request independent code review** — Use `superpowers:requesting-code-review` for full diff review
