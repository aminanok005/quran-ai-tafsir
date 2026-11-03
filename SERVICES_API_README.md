# QURAN AI Services/API README

## Overview

This directory contains the complete backend infrastructure for the QURAN AI Super WebApp, implementing all core functionality for Quran data handling, multi-agent Tafsir generation, evidence validation, and API services.

## Structure

### Core Modules

#### 1. **Models** (`models.py`)
- Pydantic models for all data domains
- Quranic data structures (Surah, Ayah, Translation)
- Tafsir and agent models
- User and authentication models
- Search and validation models

#### 2. **Configuration** (`config.py`)
- FastAPI application configuration
- Database connection settings
- Quran Foundation API credentials
- AI service configurations
- Security and rate limiting settings

#### 3. **Main Application** (`app.py`)
- FastAPI application bootstrap
- Middleware configuration (CORS, GZip, rate limiting)
- Exception handling
- Lifespan management
- Router integration

#### 4. **Routers** (`routers/`)
- **quran.py**: Quran Foundation API proxy endpoints
- **agents.py**: Multi-agent Tafsir API endpoints
- **citations.py**: Evidence citation validation endpoints
- **chat.py**: Real-time chat and conversation management
- **sources.py**: Classical source registry and metadata

#### 5. **Services** (`services/`)
- **agent_orchestrator.py**: 6-agent coordination and execution
- **evidence_validator.py**: Comprehensive evidence validation and quality assurance
- **quran_api_service.py**: Quran Foundation API integration

#### 6. **Agents** (`agents/`)
- **base_agent.py**: Abstract base class for all Tafsir agents
- **ibn_kathir_agent.py**: Classical narration specialist
- **al_tabari_agent.py**: Historical analysis and linguistic expert
- **al_qurtubi_agent.py**: Legal rulings and comparative jurisprudence
- **ibn_ashur_agent.py**: Rhetorical analysis and Maqasid scholar
- **al_saadi_agent.py**: Clear and accessible explanations
- **al_zuhayli_agent.py**: Contemporary comparative fiqh specialist

## Key Features Implemented

### Multi-Agent System
- 6 specialized Tafsir agents with distinct methodologies
- Agent orchestration service for coordinated execution
- Evidence-based classification and validation
- Scholarly disagreement matrix and comparison

### Evidence Validation
- 5-level evidence classification system
- Comprehensive citation validation
- Anti-hallucination guardrails
- Quality gate enforcement

### API Contract
- RESTful API endpoints for all agent operations
- Evidence validation and scoring
- Real-time agent status and health checks
- Comprehensive error handling

### Quran Data Integration
- Quran Foundation API proxy
- Local database caching
- Text integrity validation
- Search and retrieval capabilities

## Technical Specifications

### Database Schema
- PostgreSQL 16 with pgvector extension
- 8 comprehensive tables covering all domains
- Vector similarity search for semantic retrieval
- Full-text search for Arabic text
- Foreign key constraints and audit trails

### Agent Methodologies
1. **Ibn Kathir**: Tafsir bil-Ma'thur, Hadith references
2. **Al-Tabari**: Historical reports, linguistic analysis  
3. **Al-Qurtubi**: Legal rulings, comparative Madhhab
4. **Ibn Ashur**: Balaghah, Maqasid al-Shariah
5. **Al-Sa'di**: Clear, accessible spiritual guidance
6. **Wahbah Al-Zuhayli**: Contemporary comparative fiqh

### Evidence Classification Badges
- **[VERIFIED]**: Direct source match
- **[SOURCE-ATTRIBUTED]**: Historical scholarly attribution
- **[SCHOLARLY-DIFFERENCE]**: Recognized divergent viewpoints
- **[UNVERIFIED]**: Contextual background without verification
- **[AI-SYNTHESIS]**: AI-generated pedagogical explanation

## API Endpoints

### Agents API
- `GET /api/v1/agents` - List available agents
- `POST /api/v1/tafsir/agents/explain` - Get agent explanation
- `POST /api/v1/tafsir/compare` - Compare multiple agents
- `GET /api/v1/agents/flashcards` - Generate flashcards
- `POST /api/v1/agents/quiz` - Generate quiz questions
- `GET /api/v1/agents/evidence-badges` - Evidence badge info

### Quran API
- `GET /api/v1/quran/surahs` - List all surahs
- `GET /api/v1/quran/surah/{id}/ayahs` - Get ayah by surah
- `GET /api/v1/quran/ayahs/{surah}/{ayah}` - Get specific ayah
- `GET /api/v1/quran/search` - Search Quran text
- `GET /api/v1/quran/metadata/*` - Various metadata endpoints

### Citation API
- `POST /api/v1/citations/validate` - Validate citations
- `GET /api/v1/citations/sources` - List available sources
- `GET /api/v1/citations/evidence` - Evidence level information

## Installation & Setup

### Dependencies
```bash
# Python dependencies
cd services/api
pip install fastapi uvicorn psycopg2-binary alembic sqlalchemy

# Node.js dependencies (for frontend)
cd apps/web
npm install
```

### Database Setup
```bash
# Create PostgreSQL database with pgvector extension
dropdb -U postgres quran_ai  # if exists
sudo -u postgres createdb quran_ai
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
cd services/api
python3 -m alembic upgrade head

# Seed initial data (if available)
cd services/api
python3 -m scripts.seed_data
```

### Environment Variables
```bash
# services/api/.env
DATABASE_URL=postgresql+psycopg://quran_ai:CHANGE_ME@localhost:5432/quran_ai
REDIS_URL=redis://localhost:6379/0
QURAN_API_BASE_URL=https://apis.quran.foundation
QURAN_API_CLIENT_ID=REPLACE_WITH_APPROVED_CLIENT_ID
QURAN_API_CLIENT_SECRET=REPLACE_WITH_SECRET
LLM_PROVIDER=OPENAI
LLM_API_KEY=REPLACE_ME
EMBEDDING_PROVIDER=OPENAI
EMBEDDING_API_KEY=REPLACE_ME
```

### Running Services
```bash
# Start backend API
cd services/api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend
cd apps/web
npm run dev
```

## Development Workflow

### Phase 1.5: Database Initialization (Current)
- [x] PostgreSQL with pgvector installation
- [x] Database schema creation (migrations/0001_initial_setup.py)
- [ ] Database seeding with Quran data
- [ ] Vector search testing and validation

### Phase 2: Multi-Agent Implementation (Next)
- [ ] Agent orchestration service enhancement
- [ ] Individual agent implementations (completed skeleton)
- [ ] Evidence classification refinement
- [ ] API endpoint integration
- [ ] Frontend agent integration

### Phase 3: Integration & Testing (Following)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation completion

## Quality Gates

### Zero Citation Hallucination
- 100% of religious claims must link to verified classical database records
- Evidence classification badges mandatory on all responses
- Automated citation validation and scoring

### Quranic Text Integrity
- Canonical Uthmani text must match King Fahd Complex checksums
- Single-character deviation tolerance = 0
- Automated integrity validation

### Performance Targets
- Sub-second reader Ayah transitions (<100ms)
- Sub-second RAG retrieval (<800ms)
- Vector similarity search optimization

### Active Learning Retention
- 65% quiz completion rate target
- 7-day user streak engagement
- Gamification mechanics (streaks, gems, hearts)

## Testing

### Unit Tests
```bash
cd services/api
python3 -m pytest tests/ -xvs
```

### Integration Tests
```bash
cd services/api
python3 -m pytest tests/integration/ -xvs
```

### E2E Tests
```bash
cd apps/web
npm run test:e2e
```

### Performance Tests
```bash
# Load testing
ab -n 1000 -c 10 http://localhost:8000/health

# Vector search performance
cd services/api
python3 -m benchmarks.vector_search
```

## Next Steps

### Immediate Actions
1. **Database Setup**: Install PostgreSQL with pgvector extension
2. **Environment Configuration**: Set up API keys and secrets
3. **Frontend Integration**: Implement agent UI components
4. **API Testing**: Validate all endpoints and functionality

### Development Roadmap
- [ ] Complete agent implementations
- [ ] Set up CI/CD pipeline
- [ ] Implement frontend agent integration
- [ ] Complete documentation
- [ ] Security audit
- [ ] Performance optimization

## Contributing

This project follows the Quran AI vibe coding approach with strict evidence-based requirements. All changes must:

1. Maintain evidence classification standards
2. Respect scholarly differences
3. Preserve Quranic text integrity
4. Follow anti-hallucination guardrails
5. Include proper citation attribution

### Code Quality Standards
- No fabricated religious claims
- Proper source attribution
- Evidence classification badges
- Comprehensive testing
- Documentation compliance

## License

QURAN AI Super WebApp - Open Source Islamic Knowledge Platform

## Support

For issues and questions:
- Check documentation in this directory
- Review AGENT_MASTER_TASK.md for agent-specific guidelines
- Use GitHub issues for bug reports and feature requests
- Refer to master-prompts-vibecoding.md for implementation guidelines