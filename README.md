# Quran AI (แพลตฟอร์มปัญญาประดิษฐ์เพื่อศึกษาอธิบายอัลกุรอาน)

> **A Source-Grounded Multi-Agent Intelligence Workspace for Quranic Exegesis (Tafsir), Linguistic Roots, and Comparative Classical Scholarship.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](#license)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14+-000000?style=flat-square&logo=nextdotjs)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-000000?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL + pgvector](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-4169e1?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Strapi CMS v4/v5](https://img.shields.io/badge/Strapi-CMS-v4%2Fv5-7c15d6?style=flat-square&logo=strapi)](https://strapi.io/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776ab?style=flat-square&logo=python)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square)](https://github.com/aminanok005/quran-ai-tafsir/actions)
[![Code Style: Ruff / Prettier](https://img.shields.io/badge/Code%20Style-Ruff%20%2F%20Prettier-ff69b4?style=flat-square)](https://docs.astral.sh/ruff/)

## Navigation Quick Links

[Overview](#executive-summary--core-philosophy) •
[Architecture](#system-architecture) •
[Key Features](#key-features--workspace-capabilities) •
[Tech Stack](#technology-stack-matrix) •
[Quick Start](#quick-start) •
[Environment Setup](#environment-setup) •
[Data Pipeline](#data-pipeline) •
[Scholarly Methodology](#scholarly-methodology--religious-integrity) •
[Contributing](#contributing) •
[License](#license)

---

## 1. Header & Project Identity

**Quran AI** (แพลตฟอร์มปัญญาประดิษฐ์เพื่อศึกษาอธิบายอัลกุรอาน) is an open-source, source-grounded intelligence workspace for the study of Quranic exegesis (Tafsir). It bridges classical Islamic scriptural scholarship with modern artificial intelligence, giving students, researchers, and teachers a verified environment in which to explore the Qur'an, its linguistic roots, and the comparative opinions of classical authorities — without sacrificing religious integrity.

---

## 2. Executive Summary & Core Philosophy

### Overview

Quran AI is an intelligent Quran study workbench. Rather than treating the Qur'an as raw text for a single generative model to interpret freely, the platform treats the Qur'an and its classical Tafsir corpus as an indexed, citation-enforced knowledge base. Every AI-generated synthesis is required to map directly to an indexed classical text, and every scholarly claim carries an evidence label so readers can distinguish verified attribution from scholarly difference.

The product surface is a three-panel studio workspace (inspired by Notion and Gemini Notebook / NotebookLM aesthetics) backed by a dual data architecture: PostgreSQL + pgvector for canonical scripture and Tafsir embeddings, and Strapi as a headless CMS for dynamic curriculum management.

### The 4 Non-Negotiable Pillars of Religious AI Ethics

| # | Pillar | Principle |
|---|--------|-----------|
| 1 | **Strict Source Grounding** | All AI-generated synthesis must directly map to indexed classical texts. No unauthorized generative text and no hallucinated attributions. |
| 2 | **Multi-Perspective Classical Scholarship** | Recognized views from classical authorities (Ibn Kathir, Al-Tabari, Al-Qurtubi, Ibn Ashur, Al-Sa'di, Al-Zuhayli) are presented side by side rather than collapsed into a single synthetic voice. |
| 3 | **Preserved Sacred Scripture** | Raw Uthmani text and translations remain unmodified, immutable, and strictly verified against authoritative datasets (Quran Foundation API). |
| 4 | **Evidence Labeling** | Full transparency through verification chips — `[VERIFIED]`, `[SCHOLARLY DIFFERENCE]`, `[SOURCE ATTRIBUTED]` — attached to every piece of AI-generated output. |

> **Zero-hallucination policy.** If a claim cannot be traced to a cited, permission-approved classical source, it is not surfaced as scholarly content.

---

## 3. Key Features & Workspace Capabilities

### 3-Panel Studio Workspace

The workspace adopts a Notion + Gemini Notebook / NotebookLM aesthetic with resizable panels.

#### Left Panel — Sources & Library
- Surah / Juz navigator for rapid canonical navigation
- Curated classical commentary checklists per scholar
- Personal notes library (browser-identity-scoped, stored in PostgreSQL)

#### Center Panel — Primary Reader & Canvas
- Uthmani script typography for the sacred text
- Word-by-word linguistic root breakdown
- Floating action bar: `[Save to Note]`, `[Explain]`, `[Audio Recitation]`

#### Right Panel — Studio Workbench & Artifacts Hub
- Multi-Agent commentary comparison across classical scholars
- **Ikhtilaf Matrix** — scholarly difference table showing where authorities disagree
- Interactive 3-choice quizzes and flashcards
- Slide-deck generation for study tracks
- Audio overview (podcast-style summary) of selected passages

### Dual Data Architecture

| Store | Purpose |
|-------|---------|
| **PostgreSQL 16 + pgvector** | Canonical scripture and Tafsir embeddings; high-performance semantic & hybrid search over ~100.7 MB of classical Arabic Tafsir texts (768-dim vectors, HNSW indexing) |
| **Strapi Headless CMS** | Dynamic Zone curriculum management — Study Tracks, Chapter Slides, Quizzes, Gamification stats |

---

## 4. System Architecture

```text
┌──────────────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER (Next.js 14)                      │
│  App Router • React 18 • TypeScript • Tailwind CSS                   │
│  TanStack Query • Lucide React • react-resizable-panels              │
│  (3-Panel Studio: Sources • Reader Canvas • Studio Workbench)        │
└──────────────┬───────────────────────────────────────────────────────┘
               │ HTTPS / API calls
┌──────────────▼───────────────────────────────────────────────────────┐
│              API GATEWAY & AI ENGINE (FastAPI, Python 3.12)          │
│  Multi-Agent Orchestrator (LangChain)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐   │
│  │ Ibn Kathir  │  │  Al-Tabari  │  │ Al-Qurtubi • Ibn Ashur      │   │
│  │   Agent     │  │    Agent    │  │ Al-Sa'di • Al-Zuhayli       │   │
│  └──────┬──────┘  └──────┬──────┘  └───────────────┬─────────────┘   │
│         └────────────────┴─────────────────────────┘                 │
│              Citation Validation • Evidence Labeling • QA Gates      │
│  LLM Providers: Google Generative AI SDK / OpenAI SDK (server-only)  │
└──────────────┬───────────────────────────────────────────────────────┘
               │ SQL / Vector queries
┌──────────────▼───────────────────────────────────────────────────────┐
│                        DATA STORES                                    │
│  PostgreSQL 16 + pgvector  — canon scripture, Tafsir embeddings      │
│                        — HNSW index, 768-dim vectors                 │
│  Strapi CMS (v4/v5)        — courses, chapters, quizzes, gamification│
│  Redis (7)                 — caching, rate limiting, sessions        │
└──────────────┬───────────────────────────────────────────────────────┘
               │ REST / OAuth
┌──────────────▼───────────────────────────────────────────────────────┐
│                   UPSTREAM INTEGRATIONS                               │
│  Quran Foundation API  — verses, audio recitation, Tafsir passages   │
│  Google AI / OpenAI      — LLM & embedding provider (server-side)    │
└──────────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

1. **Client** requests an ayah or Tafsir comparison via TanStack Query.
2. **FastAPI gateway** authenticates the request, resolves the LLM/provider configuration (server-side only; keys never reach the browser), and fans out to the appropriate scholar agents.
3. **Multi-Agent Orchestrator** retrieves source-grounded passages (from Quran Foundation API / indexed corpus), runs citation validation, and applies quality gates before composing a response.
4. **Response** is labeled with an evidence chip (`[VERIFIED]`, `[SCHOLARLY DIFFERENCE]`, `[SOURCE ATTRIBUTED]`) and returned to the client for display in the 3-panel studio.
5. **Strapi CMS** supplies curriculum content (study tracks, slides, quizzes) consumed server-side by Next.js.

---

## 5. Technology Stack Matrix

| Layer | Technology | Role |
|-------|------------|------|
| **Frontend** | Next.js 14 (App Router) | Server-rendered 3-Panel Studio Workspace |
| | React 18 / 19 | UI framework |
| | TypeScript | Type-safe frontend code |
| | Tailwind CSS | Styling |
| | Lucide React | Iconography |
| | react-resizable-panels | Resizable studio panels |
| | TanStack Query v5 | Server-state management |
| | Zustand | Client state |
| **Backend API & AI** | FastAPI | API gateway and AI engine |
| | Python 3.12 | Backend runtime |
| | Pydantic v2 | Data validation |
| | SQLAlchemy (Async) | Async ORM |
| | LangChain | Multi-agent orchestration |
| | Google Generative AI SDK / OpenAI SDK | LLM & embedding providers |
| **Vector & Database** | PostgreSQL 16 | Primary relational store |
| | pgvector (HNSW indexing) | Semantic & hybrid search over Tafsir embeddings |
| | psycopg3 | PostgreSQL driver |
| | Redis | Caching, rate limiting, sessions |
| **Content Management** | Strapi CMS (v4/v5) | Headless CMS for courses, chapters, quizzes (MCP server support) |
| **DevOps & Tooling** | Docker / Docker Compose | Containerized dev environment |
| | Pytest | Python test suite |
| | Jest / Playwright | Frontend testing |
| | Ruff | Python linting |
| | ESLint / Prettier | JS/TS linting and formatting |
| | Bun | Package manager / workspaces |

---

## 6. Repository Layout (Monorepo / Clean Directory Structure)

```text
quran-ai-tafsir/
├── apps/
│   └── web/                 # Next.js 14 3-Panel Studio Workspace
├── services/
│   └── api/                 # FastAPI RAG Backend & Multi-Agent Orchestrator
├── packages/
│   └── database/            # PostgreSQL Migrations & pgvector schemas
├── cms/
│   └── strapi/              # Strapi CMS headless backend & curricula
├── data/                    # Classical Tafsir raw datasets (~100.7 MB)
├── scripts/
│   ├── embed_and_insert_tafsir.py   # Vector ingestion pipeline
│   └── seed_quran_data.py           # Scripture seeder
├── docker-compose.yml
└── README.md
```

### Directory Purpose

- **`apps/web`** — Next.js 14 App Router frontend implementing the 3-Panel Studio (sources, reader canvas, studio workbench). Consumes the FastAPI gateway and Strapi CMS.
- **`services/api`** — FastAPI backend: multi-agent Tafsir orchestrator, citation validation, evidence labeling, reader and workspace routes. Runs server-side only; LLM/Quran Foundation credentials never ship to the browser.
- **`packages/database`** — PostgreSQL migrations (Alembic) and pgvector schemas for canonical scripture, Tafsir passages, scholars, citations, users, and governance tables.
- **`cms/strapi`** — Strapi headless backend defining Dynamic Zone curriculum content (Study Tracks, Chapter Slides, Quizzes, Gamification).
- **`data/`** — Classical Tafsir raw datasets (~100.7 MB) used for ingestion and research.
- **`scripts/`** — Ingestion and seeding entry points (`embed_and_insert_tafsir.py`, `seed_quran_data.py`).
- **`docker-compose.yml`** — Single-command local stack: PostgreSQL + pgvector, FastAPI API, Next.js web, Redis.

---

## 7. Quick Start

### Prerequisites

- **Node.js 20.x** and **Bun 1.2.0** (frontend monorepo)
- **Python 3.12+** (backend services)
- **Docker** and **Docker Compose** (recommended local stack)
- Approved **Quran Foundation API** credentials (client ID / secret) for verse, audio, and Tafsir data
- (Optional) **Google AI / OpenAI** API key for LLM and embedding generation

### One-Command Local Stack

```bash
# Clone the repository
git clone https://github.com/aminanok005/quran-ai-tafsir.git
cd quran-ai-tafsir

# Copy environment example and fill in your secrets
cp .env.example .env
cp .env.local .env.local   # optional local overrides

# Start PostgreSQL + pgvector, API, web, and Redis
docker compose up --build -d
```

### Verify the Services

| Service | URL | Description |
|---------|-----|-------------|
| Web (Next.js) | http://localhost:3000 | 3-Panel Studio Workspace |
| API (FastAPI) | http://localhost:8000 | REST gateway & AI engine |
| API Docs | http://localhost:8000/docs | Interactive OpenAPI docs |
| DB | localhost:5432 | PostgreSQL 16 + pgvector |
| Redis | localhost:6379 | Cache & rate limiting |

### Seed Canonical Scripture

```bash
# Seed all 6,236 ayahs from the Quran Foundation Content API
bun run db:seed
```

> The seeder is idempotent on `(surah_number, ayah_number)`. It must not be run against production without confirming the source license and target database. Pre-live Quran data may contain only Al-Fatihah and Al-Baqarah until production credentials are approved.

---

## 8. Environment Setup

Create a `.env` at the repository root from `.env.example`, then override sensitive values in `.env.local` (never commit real credentials).

### Required Variables

```bash
# API runtime
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# PostgreSQL + pgvector (matches docker/compose defaults)
POSTGRES_DB=quran_ai
POSTGRES_USER=quran_ai
POSTGRES_PASSWORD=quran_ai_dev
DATABASE_URL=postgresql+psycopg://quran_ai:quran_ai_dev@localhost:5432/quran_ai

# Optional Redis
REDIS_URL=redis://localhost:6379/0

# Quran Foundation Content API (keep credentials server-side)
QURAN_API_BASE_URL=https://apis.quran.foundation
QURAN_API_CLIENT_ID=REPLACE_WITH_APPROVED_CLIENT_ID
QURAN_API_CLIENT_SECRET=REPLACE_WITH_SECRET
QURAN_API_TAFSIR_SCOPE=content.tafsirs.read

# LLM / Embedding provider (server-only)
LLM_PROVIDER=openai_compatible
LLM_API_BASE_URL=http://127.0.0.1:20128/v1
LLM_MODEL=REPLACE_WITH_MODEL
LLM_API_KEY=REPLACE_WITH_SERVER_ONLY_KEY

# Security — generate unique values for any non-local deployment
SECRET_KEY=GENERATE_A_LONG_RANDOM_SECRET
JWT_SECRET=GENERATE_A_LONG_RANDOM_SECRET
```

### Frontend Variables (Next.js)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_TELEMETRY_DISABLED=true
```

### Strapi CMS (optional curriculum backend)

```bash
STRAPI_API_BASE_URL=http://localhost:1337
STRAPI_API_TOKEN=REPLACE_WITH_STRAPI_READ_ONLY_TOKEN
```

> The Strapi token is read only by the Next.js server module (`src/lib/strapi.ts`). Do **not** prefix it with `NEXT_PUBLIC_`.

### Verify Environment

```bash
bash scripts/check-env.sh
bash scripts/setup_env.sh
```

---

## 9. Data Pipeline

### Scripture Seeding (`seed_quran_data.py`)

Fetches all ayahs from the Quran Foundation Content API v4 by surah and page, validates each surah's canonical ayah count and uniqueness, then upserts them into `quran_ayahs`. Idempotent on `(surah_number, ayah_number)`.

```bash
bun run db:seed
```

### Tafsir Vector Ingestion (`embed_and_insert_tafsir.py`)

Development-only pipeline for embedding classical Tafsir texts into pgvector.

```bash
python3 scripts/ingest_tafsir_vectors.py \
  --file data-tafsir/ar-tafsir-ibn-kathir.json \
  --source-id dev-tafsir-ibn-kathir \
  --scholar-id ibn_kathir \
  --scholar-name "Ibn Kathir" \
  --book-title "Tafsir al-Qur'an al-Azim" \
  --apply-development-only
```

Requires: `ENVIRONMENT=development`, a separate embedding-provider key, and a development `DATABASE_URL`. Imported records are marked `development_only` / `unverified` and cannot be promoted to the approved production corpus automatically.

### Pipeline Guardrails

- No parser performs writes or network access without explicit flags.
- Raw source text remains unchanged; `normalized_text` is separate derived search text.
- Missing license, source URL, volume, and page stay `None` — they are never inferred.
- Development writes are hard-coded to `development_only` permission and `unverified` status.
- Existing source-rights records are never overwritten or promoted by ingestion.

---

## 10. Scholarly Methodology & Religious Integrity

### Supported Classical Scholars

| Scholar | Methodology | Focus | Status |
|---------|-------------|-------|--------|
| Ibn Kathir | Tafsir bil-Ma'thur | Qur'an, authentic Hadith, Salaf reports | Implemented |
| Al-Tabari | Early Tafsir narrations & Sahabah interpretations | Early Islamic scholarship, linguistic analysis | Planned |
| Al-Qurtubi | Ahkam al-Qur'an (legal rulings) | Fiqh analysis, madhhab comparisons | Planned |
| Ibn Ashur | Linguistic & Maqasid analysis | Arabic grammar, rhetoric, Sharia objectives | Planned |
| Al-Sa'di | Accessible Tafsir for general readers | Simplified explanations, practical lessons | Planned |
| Al-Zuhayli | Contemporary Fiqh & social applications | Modern relevance, legal & social implications | Planned |

### Evidence Labeling (Verification Chips)

Every AI-generated output carries one of the following chips:

- `[VERIFIED]` — Claim traceable to a cited, permission-approved classical source.
- `[SCHOLARLY DIFFERENCE]` — Recognized difference of opinion between classical authorities.
- `[SOURCE ATTRIBUTED]` — Content attributed to a named classical source with citation.

### Source Governance

- All religious source records must be traceable to their original source.
- Imported/local Tafsir is **not** a Reader fallback and is not used as a production corpus until rights and verification evidence are reviewed.
- The JSON importer and vector ingestion remain rights-gated; do not mark a source as approved or import it into a production database until its license, source URL, and verification evidence have been reviewed.
- The Quran seeding CLI is development-only and does not run automatically when the API starts.

---

## 11. Contributing

We welcome contributions that advance source-grounded Quran study. Because this project handles sacred scripture and classical religious texts, contributions are reviewed with extra care for accuracy, citation integrity, and source permissions.

### How to Contribute

1. **Fork** the repository and create a feature branch from `main`.
2. **Run the checks** relevant to your change:
   - Python: `ruff check .` and `pytest`
   - Frontend: `bun run lint`, `bun run typecheck`, `bun run test`
3. **Never commit secrets.** Check `.env`, `.env.local`, and any credential values before staging. Never use `git add .` blindly.
4. **Open a Pull Request** describing the change, the sources consulted, and any evidence labels affected.

### Code Style

- Python: **Ruff** (line length 100, target py312)
- JavaScript/TypeScript: **ESLint** + **Prettier** (with Tailwind plugin)
- Commit style: Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)

### Ground Rules for Religious Content

- Do not introduce unattributed generative Tafsir or synthetic scholarly opinions.
- All new classical-source references must include a verifiable citation (book, edition, volume, page, and source URL).
- Changes to verification gates, evidence labeling, or source-permission logic require maintainer review.

---

## 12. License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

> Religious-integrity disclaimer: This platform is a study aid and does not replace qualified scholarly instruction. Users should consult qualified teachers and scholars for matters of fiqh, aqeedah, and religious practice.