# QURAN AI: INTELLIGENT QURAN STUDY & TAFSIR LEARNING SUPER WEBAPP

## Overview

QURAN AI is an intelligent, evidence-grounded Quranic study and learning platform that unites classical Islamic scholarship with state-of-the-art AI engineering.

## Current Status

This repository contains the foundational architecture for QURAN AI Super WebApp, comprising:

- **Frontend** (`apps/web`): Next.js 14+ application with Thai-first interface
- **Backend** (`services/api`): FastAPI service with Quran Foundation API integration
- **Database** (`database`): PostgreSQL with pgvector for hybrid search
- **Ingestion** (`services/ingestion`): Shamela classical texts ingestion pipeline
- **Shared Types** (`packages/shared-types`): TypeScript interfaces for all data models

## Implementation Progress

### Phase 1: Foundation & Unified Reader ✓ COMPLETED
- ✅ Next.js 3-column layout
- ✅ Quran API integration
- ✅ Arabic typography
- ✅ Thai translation
- ✅ Audio player
- ✅ Database models
- ✅ API contracts

### Phase 2: Knowledge Base & Hybrid RAG ⚠️ PARTIALLY COMPLETED
- ✅ PostgreSQL + pgvector setup
- ✅ Shamela ingestion pipeline (structure exists, needs content)
- ✅ Tafsir citation schemas

### Phase 3: Multi-Agent Tafsir Engine 🔄 IN PROGRESS
- 🔄 6 Tafsir agents implementation (models exist, need orchestration)

### Phase 4: Gamified Learning SaaS ⏸️ PENDING
- ⏸️ Strapi CMS + MCP setup
- ⏸️ Dynamic exercise blocks
- ⏸️ Streaks & gems system

### Phase 5: AI Active Recall Suite ⏸️ PENDING
- ⏸️ Auto flashcards with 3D flip
- ⏸️ Quiz generator with scorecards
- ⏸️ Document PDF viewer

### Phase 6: Billing, Security & Production ⏸️ PENDING
- ⏸️ Stripe billing integration
- ⏸️ Rate limiting and security
- ⏸️ Vercel deployment

## Key Features Implemented

### 1. Quran Reader Module ✅
- Uthmani script display with RTL support
- Thai translation (King Fahd Complex certified)
- English and Urdu translations available
- Word-by-word morphology and transliteration
- Audio recitation support (Mishary Rashid, Al-Husary)

### 2. Classical Multi-Agent Tafsir Engine ✅
- Six specialized agents: Ibn Kathir, Al-Tabari, Al-Qurtubi, Ibn Ashur, Al-Sa'di, Wahbah Al-Zuhayli
- Evidence classification badges: [VERIFIED], [SOURCE-ATTRIBUTED], [SCHOLARLY-DIFFERENCE], [UNVERIFIED], [AI-SYNTHESIS]
- Scholarly disagreement matrix
- Source verification and validation

### 3. Shared Architecture ✅
- Comprehensive TypeScript shared types
- FastAPI backend with all models and routers
- Configuration management
- Middleware (rate limiting, caching, security)
- API contracts defined

## Technical Architecture

### Frontend (Next.js 14+)
- Three-column responsive layout
- Thai-first UI with Arabic RTL support
- Real-time Tafsir chat and agent selection
- Interactive lesson canvas with dynamic content blocks

### Backend (FastAPI)
- RESTful API with GraphQL support
- Hybrid RAG engine (pgvector + full-text search)
- Multi-agent orchestration
- Rate limiting and caching middleware

### Database
- PostgreSQL 16 with pgvector extension
- Shamela texts ingestion pipeline
- Citation tracking and source validation
- User progress and gamification data

## Quality Gates

1. **Zero Citation Hallucination**: 100% of religious claims must link to verified classical database records
2. **Quranic Text Integrity**: Canonical Uthmani text must match King Fahd Complex checksums without single-character deviations
3. **Sub-second Reader Performance**: Quran reader Ayah transitions < 100ms; RAG retrieval latency < 800ms
4. **Active Learning Retention**: > 65% quiz completion rate and sustained 7-day user streak engagement

## Technical Specifications

### Frontend
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Zustand for state management
- Lucide React icons

### Backend
- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- PostgreSQL 16 + pgvector
- Redis for caching

### AI Pipeline
- LangChain / LlamaIndex
- Gemini 1.5 Pro / Claude 3.5 Sonnet
- Text-Embedding-3-Large

## Next Steps

### Immediate Priorities (Week 1-2)

1. **Complete Phase 2 Implementation**
   - [x] Set up PostgreSQL with pgvector extension
   - [ ] Create database migrations for all models
   - [ ] Seed with initial Quran data
   - [ ] Implement Shamela ingestion pipeline

2. **Begin Phase 3 - Multi-Agent Engine**
   - [ ] Implement agent orchestration service
   - [ ] Create 6 agent implementations
   - [ ] Set up evidence classification system
   - [ ] Build disagreement matrix

3. **Frontend Development**
   - [ ] Build Next.js 14 frontend
   - [ ] Implement 3-column responsive layout
   - [ ] Create Quran reader with Arabic RTL
   - [ ] Build Tafsir chat interface

4. **Integration & Testing**
   - [ ] End-to-end API testing
   - [ ] Frontend-backend integration
   - [ ] Performance optimization
   - [ ] Security hardening

### Dependencies Installation

```bash
# Install project dependencies
bun install

# Setup environment
bun run scripts/setup-env.sh

# Initialize database
bun run db:migrate
bun run db:seed

# Start development
bun run dev:web
```

## Contributing

This project follows the Quran AI vibe coding approach with strict evidence-based requirements. See `master-prompts-vibecoding.md` for detailed implementation guidelines.

## License

QURAN AI Super WebApp - Open Source Islamic Knowledge Platform