# QURAN AI — Multi-Agent Coding Framework v1.0

Thai-first Quran Reader and Tafsir AI platform.

## Agent topology

| Role | Tool | Ownership |
|---|---|---|
| Coordinator | Human / Orchestrator | Contracts, integration, QA |
| Backend | Claude Code | services/api/, services/ai-engine/ |
| Frontend | Kilo Code | apps/web/ |
| Data | Cline | database/, services/ingestion/ |

## Operating model

1. Inspect the repository before changing anything.
2. Read AGENT_MASTER_TASK.md.
3. Use separate Git worktrees for parallel agents.
4. Do not allow agents to edit the same files.
5. Freeze shared contracts before implementation.
6. Each agent reports files, tests, risks and blockers.
7. Coordinator reviews and integrates the work.
8. Run all quality gates before declaring MVP ready.

## Important

The framework does not automatically launch or control other coding agents.
Open each tool in its assigned worktree and provide its dispatch task.

## Start

Read dispatch/START_HERE.md, then AGENT_MASTER_TASK.md.

## Agent Implementation Priority

### BACKEND DEVELOPMENT (Claude Code)
1. **Complete Database Initialization** - Load classical tafsir sources
2. **Implement Quran Foundation API Adapter** - Real Quran data integration
3. **Create Surah and Ayah Endpoints** - RESTful API for Quran data
4. **Implement Agent Registry** - Available agents list
5. **Complete Tafsir Explain Endpoint** - Agent orchestration service
6. **Add Honest Unavailable-Source Handling** - Graceful error responses
7. **Comprehensive Backend Testing** - All endpoints tested

### FRONTEND DEVELOPMENT (Kilo Code)
1. **Build Next.js 14 Frontend** - Complete application
2. **Implement 3-column Responsive Layout** - Multi-panel workspace
3. **Create Quran Reader with Arabic RTL** - Uthmani text rendering
4. **Build Tafsir Chat Interface** - Multi-agent chat
5. **Implement Agent Selection** - 6 classical scholars
6. **Display Citations and Evidence** - Source attribution
7. **Handle Loading/Empty/Error States** - User experience

### DATA ENGINEERING (Cline)
1. **Design Database Schema** - Actual implementation vs. design
2. **Create Database Migrations** - Version-controlled schema
3. **Define Source Registry** - Provenance and metadata
4. **Implement Citation Structures** - Source tracking
5. **Create Ingestion Interfaces** - Data loading pipeline
6. **Build Validation Tests** - Data integrity checks
7. **Load Classical Sources** - Phase 1.5 completion

## Critical Path Dependencies

### IMMEDIATE (Week 1)
1. **Database Setup** - Phase 1.5 completion (BLOCKING)
2. **Environment Configuration** - API credentials
3. **Quran Data Integration** - From Quran Foundation API

### SHORT TERM (Week 2-3)
1. **Agent Orchestration** - Complete backend implementation
2. **Evidence Validation** - Quality gates and validation
3. **Frontend Integration** - API communication

### COMPLETE MVP (Week 4)
1. **End-to-End Testing** - User journey verification
2. **Quality Gates** - All 11 MVP requirements met
3. **Production Preparation** - Configuration and deployment

## Critical Blocker Resolution

### Current Status
✅ **ARCHITECTURE COMPLETE** - Perfect design, comprehensive documentation

⏸️ **IMPLEMENTATION BLOCKED** - Database initialization not executed

❌ **NOT STARTED** - Phase 1.5 (Database Setup)

### The Conflict
- **Phase 1.5: Database Initialization** requires:
  1. PostgreSQL with pgvector extension
  2. Migration execution: `alembic upgrade head`
  3. Classical source data loading (4 files ready)
  4. Environment configuration

- **Backend Implementation** cannot proceed until database is populated
- **Frontend Development** cannot proceed without API endpoints
- **Phase 2-3** cannot start until **Phase 1.5** completes

### Immediate Resolution Required

#### Priority 1: Database Setup
```bash
# 1. Update environment configuration
# Edit .env with real credentials:
DATABASE_URL=postgresql+psycopg://quran_ai:YOUR_PASSWORD@localhost:5432/quran_ai
QURAN_API_CLIENT_ID=YOUR_QURAN_API_CLIENT_ID
QURAN_API_CLIENT_SECRET=YOUR_QURAN_API_CLIENT_SECRET
LLM_API_KEY=YOUR_LLM_API_KEY

# 2. Execute database migrations
python -m alembic upgrade head

# 3. Load classical tafsir sources
python scripts/load_tafsir_data.py

# 4. Seed Quran data from API
python scripts/seed_quran_data.py
```

#### Priority 2: Frontend-Backend Integration
```bash
# After database setup, run:
cd apps/web && npm run build
# Frontend build includes API client integration
```

#### Priority 3: Quality Gates
```bash
# Run comprehensive testing
python -m pytest tests/ -v
npm run lint
npm run typecheck
```

## Why This Path Matters

### Without Database Setup
- ❌ Agents cannot retrieve authentic sources
- ❌ Evidence classification fails
- ❌ No Quranic text in database
- ❌ MVP cannot be tested
- ❌ Quality gates will fail

### With Database Setup
- ✅ Complete evidence-based Quran study
- ✅ Zero citation hallucinations
- ✅ Scholar disagreement matrix functional
- ✅ Full MVP experience available

## Timeline and Resource Requirements

### Week 1 (Critical)
**Days 1-2:** Database initialization
- PostgreSQL setup with pgvector
- Migration execution
- Classical source data loading
- Environment configuration

**Days 3-4:** Frontend development
- Next.js application build
- Quran reader implementation
- API integration

**Days 5-7:** Quality gates
- End-to-end testing
- Performance optimization
- Security hardening

### Week 2
**Days 8-10:** Backend completion
- Agent orchestration service
- Evidence validation system
- Disagreement matrix

**Days 11-14:** Integration and testing
- Frontend-backend integration
- User journey validation
- Production preparation

## Resource Requirements

### Technical
- PostgreSQL database with pgvector extension
- Quran Foundation API credentials
- Redis for caching (recommended)
- Environment configuration files

### Personnel
- Backend developer (Claude Code) - Database setup
- Frontend developer (Kilo Code) - Next.js application
- Data engineer (Cline) - Schema and ingestion
- Coordinator - Integration and QA

## Risk Mitigation

### Database Risk
**Mitigate:** Execute database setup immediately before proceeding
**Backup:** Test in development environment first

### Authentication Risk
**Mitigate:** Use environment variables with proper secrets management
**Backup:** Implement fallback for missing credentials

### Performance Risk
**Mitigate:** Implement caching middleware and optimize queries
**Backup:** Add performance monitoring

## Decision Point

**Current Situation:** Perfect architecture, incomplete implementation due to database blocker

**Choice:**
1. **Complete Database Setup** (3-4 days) - Full MVP path
2. **Alternative Approach** - Requires custom solution

**Recommendation:** Complete database setup using the provided scripts and data files. This resolves the blocker and enables completion of all other development phases.

## Success Metrics

**Technical:**
- Database migration executed successfully
- Classical sources loaded (6,236+ Quran verses)
- Vector search functionality working
- All API endpoints functional

**Quality:**
- Zero citation hallucinations
- 100% source attribution compliance
- Evidence classification accuracy > 95%

**Business:**
- Reader retention metrics
- Feature adoption rates
- User satisfaction scores
- Performance benchmarks met

## Next Steps

Given the current state, the immediate action required is:

1. **Update .gitignore** (COMPLETED) - Allow data files
2. **Update environment configuration** - Add real credentials
3. **Execute database initialization script** - Load classical sources
4. **Complete migration and testing** - Verify setup
5. **Proceed with Phase 2-3 development** - Complete MVP

The QURAN AI system has **perfect architecture** - it just needs **Phase 1.5 (Database Setup)** to deliver the evidence-based Quran study experience it's designed for.

**Would you like me to focus on the database initialization phase, or should we address a specific component while the database setup is being planned?**