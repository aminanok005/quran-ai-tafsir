# QURAN AI - Phase Checklist & Progress Tracker

**Last Updated:** 2026-11-06
**Current Phase:** Tafsir translation router configuration follow-up → Phase 2 database/source gates → Phase 3 data-backed validation

---

## 📊 **OVERALL PROGRESS**

| Phase | Status | Completion | Blockers |
|-------|--------|------------|----------|
| **Phase 1: Foundation & Unified Reader** | ✅ **IMPLEMENTED; READER SMOKE-TESTED** | — | QPC font coverage across all pages is not verified |
| **Phase 2: Knowledge Base & Hybrid RAG** | 🔄 **IN PROGRESS** | — | PostgreSQL target/authentication, source-rights review, and disposable-database validation pending |
| **Phase 3: Multi-Agent Tafsir Engine** | 🔄 **IMPLEMENTED; VALIDATION PENDING** | — | Data-backed integration and runtime validation pending |
| **Phase 4: Gamified Learning SaaS** | ⏸️ **PENDING** | 0% | Phase 3 completion |
| **Phase 5: AI Active Recall Suite** | ⏸️ **PENDING** | 0% | Phase 4 completion |
| **Phase 6: Billing, Security & Production** | ⏸️ **PENDING** | 0% | Phase 5 completion |

---

## ✅ **PHASE 1: Foundation & Unified Reader - IMPLEMENTED**

### Implemented Items:
- [x] Next.js 14+ project structure with App Router
- [x] Three-column responsive layout (260px | flex | 420px)
- [x] Thai-first UI with Arabic RTL support
- [x] Center Reader navigation, reading progress, Arabic font sizing, and retryable loading state
- [x] Quran API integration (Quran Foundation API)
- [x] Local `data-tafsir/qpc-v4.json` word records assembled into ordered ayah text for the Reader
- [x] Uthmani script display with proper RTL rendering
- [x] Thai translation loaded by ayah from Quran Cloud
- [x] English and Urdu translations
- [x] Word-by-word morphology and transliteration
- [x] Per-ayah Al-Afasy audio playback in the Reader
- [x] Reader smoke test: homepage and Reader return HTTP 200; all referenced CSS/JS assets return HTTP 200
- [x] Surah selector displays actual names for all 114 surahs instead of numeric-only labels
- [x] Mobile landing navigation is visible on first view; Reader menu opens the full scrollable surah list and library options
- [x] Sample Reader check: Surah 1 loads 7 QPC ayahs, Thai translation, and Al-Afasy audio data
- [x] Ayah selection check: selecting another ayah keeps the full surah Arabic and Thai text visible, updates the URL without an App Router navigation, and reuses cached Ibn Kathir content when returning to a previously loaded ayah
- [x] Thai translation fast path: deduplicate/cache successful translations in the browser during the session and cache public Quran API responses for 1 hour with stale-while-revalidate; keep audio independent
- [x] Translation readability: label Thai translations and render tafsir translation paragraphs in a spaced, highlighted reading block without changing the translated wording
- [x] Surah An-Nas translation API returns all 6 ayahs; repeated local API request returned 200 in 0.049s versus 0.419s cold
- [ ] Tafsir response/data check: live development API returned placeholder text (`114:1`) for both Arabic and Thai fields when requesting ayah 114:2; the Thai translation attempt for 114:1 also timed out. Correct/verify the development passage source and translation runtime before calling the Reader flow complete.
- [x] QUL QPC V4 font samples for pages 1, 2, and 604 return HTTP 200 and Arabic QPC glyphs render in the Reader
- [ ] Verify QPC page-font loading and rendering across the full Quran and surah/page transitions
- [x] Database models (PostgreSQL + pgvector)
- [x] API contracts defined (OpenAPI)
- [x] Configuration management
- [x] Middleware (rate limiting, caching, security)

### Files Created:
- `apps/web/` - Next.js 14 frontend
- `services/api/` - FastAPI backend
- `database/` - PostgreSQL migrations
- `packages/shared-types/` - TypeScript interfaces

---

## 🔄 **PHASE 2: Knowledge Base & Hybrid RAG - IN PROGRESS**

### Implemented Items:
- [x] PostgreSQL + pgvector schema and setup materials exist
- [x] Database model/schema design exists (table count still needs migration verification)
- [x] Shamela ingestion pipeline structure
- [x] Tafsir citation schemas
- [x] Vector search indexes (HNSW + FTS)
- [x] Hybrid RAG architecture design

### Files / Docs Available (review before execution):
- `scripts/load_tafsir_data.py` - Loads classical tafsir sources only after explicit rights approval and verification
- `scripts/seed_quran_data.py` - Seeds all 6,236 Quran verses into the canonical table
- `DATABASE_SETUP_COMMANDS.md` - Copy-paste SQL commands
- `POSTGRESQL_SETUP_GUIDE.md` - Authentication configuration

### Blockers
- Tafsir sources are deliberately marked pending/unverified until their rights and provenance are reviewed; the loader refuses them by default.
- A prior read-only audit found that the API could not authenticate to its configured PostgreSQL target. The intended instance and supported authentication path still need confirmation; do not change credentials, database configuration, or infrastructure as part of this checklist.
- Migration and data loading have not been run against a live database. After the target is confirmed and the user authorizes it, validate only against a disposable development database.

---

## 🎯 **PHASE 3: Multi-Agent Tafsir Engine - IMPLEMENTED; VALIDATION PENDING**

### Implemented Items:
- [x] 6 Tafsir Agent implementations:
  - [x] **Ibn Kathir Agent** - Tafsir bil-Ma'thur, Hadith references
  - [x] **Al-Tabari Agent** - Historical reports, linguistic analysis
  - [x] **Al-Qurtubi Agent** - Legal rulings (Ahkam), Madhhab comparison
  - [x] **Ibn Ashur Agent** - Arabic rhetoric (Balaghah), Maqasid
  - [x] **Al-Sa'di Agent** - Clear, accessible explanations
  - [x] **Al-Zuhayli Agent** - Contemporary comparative fiqh
- [x] Evidence classification system (5 badges)
- [x] Agent orchestration, evidence-validation, and API modules exist
- [x] Development Reader reads a selected tafsir passage from local JSON and translates it on demand without database access or writes; 

### Remaining Validation / Implementation:
- [ ] Confirm orchestration behavior and parallel execution
- [ ] Complete evidence validation against populated source data
- [ ] Disagreement matrix UI
- [ ] Agent response streaming (SSE)
- [ ] Measure and optimize RAG latency (< 800ms target)
- [x] Add rights-filtered pgvector retrieval endpoint against the canonical 1536-dimension schema
- [x] Add explicit development-only JSON-to-pgvector ingestion with dry-run default and stable IDs
- [x] Add server-side Strapi course/chapter loading and Dynamic Zone lesson rendering
- [ ] Configure a dedicated embedding provider and validate semantic search against a disposable database
- [ ] Obtain source-rights approval before any production tafsir ingestion
- [ ] Configure Strapi API base URL/read-only token and validate course publishing end to end
- [ ] Add persistent course progress/scoring only after the project authentication/user model is ready

Development JSON translation is covered by targeted API tests. A live OpenAI
request returned HTTP 429 (`insufficient_quota` / credit balance exhausted) at
the last recorded attempt. The account/project quota must be resolved by its
owner before retrying. Production database integration has not been run.
Latest runtime inspection found API 8011 is configured to use the local
OpenAI-compatible endpoint on port 20128, but its process has `OPENAI_API_KEY`
and no `LLM_API_KEY`. The local router needs its own API token, not the OpenAI
account key. The API now uses `LLM_API_KEY` for custom endpoints, reserves
`OPENAI_API_KEY` for `api.openai.com`, and supports the Responses API via
`LLM_API_WIRE_API=responses`. API 8011 was restarted with the provided local
router token and Responses protocol, but a real translation request returned
HTTP 401 `invalid_api_key`; the configured router token is not accepted by the
active local endpoint (or its upstream). API health remains 6/6 and 9Router
was not modified. Translation remains blocked until its valid inbound/upstream
credential is configured in the API environment. The suggested legacy
translation URL on port 8000 returned 404; the active Quran translation route
is served by Next.js at `/api/quran/surahs/114/?edition=th.thai`.
In the latest browser check, the tafsir passage endpoint returned HTTP 200, but
the selected-ayah response contained placeholder text and the client reported
`Thai translation timed out; please try again`. The Reader keeps ayah navigation
stable and caches passage results; source accuracy and successful translation
remain separate validation blockers.
Thai Quran translation data now has in-session request deduplication and a
browser cache policy; this improves repeat navigation/reloads but cannot remove
latency on a cold fetch if Quran Cloud is slow. AI tafsir translation continues
to depend on the API/provider and has timed out in live validation.

### Agent Files Location:
- `services/api/agents/ibn_kathir_agent.py`
- `services/api/agents/al_tabari_agent.py`
- `services/api/agents/al_qurtubi_agent.py`
- `services/api/agents/ibn_ashur_agent.py`
- `services/api/agents/al_saadi_agent.py`
- `services/api/agents/al_zuhayli_agent.py`
- `services/api/services/agent_orchestrator.py`
- `services/api/services/evidence_validator.py`

---

## ⏸️ **PHASE 4: Gamified Learning SaaS - PENDING**

### To Implement:
- [ ] Strapi CMS + MCP setup
- [ ] Dynamic exercise blocks:
  - [ ] Theory blocks (Arabic + translation + tafsir)
  - [ ] MCQ blocks (4-option with instant feedback)
  - [ ] Fill-in-the-blank (Arabic root words)
  - [ ] Matching blocks (terms ↔ definitions)
- [ ] Gamification mechanics:
  - [ ] Daily Zap Streak
  - [ ] Gems system
  - [ ] Hearts/Lives for hints
  - [ ] Leaderboards
- [ ] Strapi MCP Server for AI course authoring
- [ ] Course structure: Surah-based chapters (5-10 min each)

---

## ⏸️ **PHASE 5: AI Active Recall Suite - PENDING**

### To Implement:
- [ ] Auto-generated Flashcards:
  - [ ] 3D flip animation
  - [ ] Arabic front / Thai+English back
  - [ ] Root word + tafsir context
  - [ ] Favorites & spaced repetition
- [ ] Custom AI Quiz Generator:
  - [ ] Configurable (5/10/20 questions)
  - [ ] Difficulty levels (Beginner/Intermediate/Advanced)
  - [ ] Score analytics & review
  - [ ] Source-linked explanations
- [ ] 1-Click Surah/Ayah Summarizer
- [ ] Quranic Arabic Concept Explainer
- [ ] Document PDF Viewer with AI chat

---

## ⏸️ **PHASE 6: Billing, Security & Production - PENDING**

### To Implement:
- [ ] Stripe Billing Integration:
  - [ ] Free tier (basic reader, Al-Sa'di, 3 flashcard sets/day)
  - [ ] Premium Scholar Plan ($5.99/mo | $49.99/yr)
  - [ ] Unlimited agents, all 6 scholars, matrix, unlimited flashcards
- [ ] Authentication: JWT + OAuth2 (Google, Email/Password)
- [ ] Rate limiting & security hardening
- [ ] Vercel deployment (frontend)
- [ ] Cloud deployment (backend + database)
- [ ] CI/CD pipeline

---

## 📋 **NEXT STEPS (ORDERED, WITH GATES)**

1. **Finish Reader/QPC validation:** exercise page-font loading across all Quran pages and representative surah/page transitions; record any CDN, CORS, or glyph-rendering failures. Do not mark the QPC task complete based only on the sampled pages.
2. **Unblock database work safely:** confirm which local PostgreSQL instance is intended and how the development API is expected to authenticate. Keep the audit read-only until the user explicitly authorizes a specific change; do not alter credentials, `.env`, shell configuration, or PostgreSQL settings.
3. **Validate schema and Quran seed in disposable development data:** after step 2 and explicit authorization, run the reviewed migrations and seeder against a disposable database; verify schema state and all 6,236 ayahs. Do not run these against production.
4. **Review tafsir source rights and provenance:** approve specific sources before ingestion, or keep them explicitly development-only. Then validate loader behavior and provenance/evidence fields in the disposable database.
5. **Complete Phase 3 validation:** test API-to-Reader retrieval, evidence/citation handling, and orchestration using approved data; use mocked/offline provider tests while the recorded OpenAI quota error remains unresolved.
6. **Continue Phase 3 product work:** implement the disagreement matrix and streaming only after the data-backed response contract and evidence behavior are validated; measure RAG latency against the <800 ms target.
7. **Defer Phases 4–6:** start gamification, active recall, billing, and deployment only after Phase 2/3 validation and separate scope approval.

### Validation already recorded
- [x] Ingestion policy unit tests: 6 passed (`python3 -m unittest -v` in `services/ingestion`)
- [x] Quran seeder unit tests: 3 passed (`python3 -m unittest -v scripts.test_seed_quran_data`)
- [x] Frontend typecheck passed after Reader changes
- [x] Frontend development smoke test: homepage and Reader returned HTTP 200; 2 CSS and 5 JavaScript assets returned HTTP 200 after the Next.js cache rebuild
- [ ] Re-run production build after the final Next.js configuration cleanup
- [x] Python compile check: seeder, tafsir loader, and migration compile successfully

---

## 📁 **KEY FILES SUMMARY**

| File | Purpose | Status |
|------|---------|--------|
| `DATABASE_SETUP_COMMANDS.md` | Database setup reference | Available; not validated against current migration |
| `POSTGRESQL_SETUP_GUIDE.md` | Auth configuration | Available |
| `MANUAL_DATABASE_SETUP.md` | Step-by-step manual | Available |
| `EXECUTE_NOW.sh` | Database setup script | Needs review before execution |
| `scripts/load_tafsir_data.py` | Load classical sources | Schema-aligned; source approval and DB runtime validation pending |
| `scripts/seed_quran_data.py` | Seed Quran data | Canonical schema mapping; unit tests pass; API/DB runtime pending |
| `services/api/agents/*.py` | 6 agent implementations | Source files present; runtime validation pending |
| `services/api/services/agent_orchestrator.py` | Agent orchestration | Source file present; runtime validation pending |
| `services/api/services/evidence_validator.py` | Evidence validation | Source file present; data-backed validation pending |
| `apps/web/` | Next.js 14 frontend | Typecheck and development smoke test pass; production build after final config cleanup pending |

---