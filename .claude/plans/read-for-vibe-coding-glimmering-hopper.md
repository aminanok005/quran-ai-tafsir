# QURAN AI Implementation Plan

## Context
This project requires implementing an evidence-based Quran study and multi-scholar Tafsir comparison platform with strict source attribution requirements. The repository contains comprehensive architectural documentation but minimal actual code implementation.

## Current State Assessment
The project is at Phase 0 (Research & Foundation) with extensive documentation but no functional code. Critical missing components include:
- Quran Reader UI (apps/web)
- AI Agent implementations (services/ai-engine)  
- Database schema and migrations (database/)
- API endpoints beyond health check (services/api/)
- Source ingestion pipeline (services/ingestion)

## Immediate Implementation Priority
**Start with the core Quran Reader and Ibn Kathir Agent** as specified in the MVP requirements (PRD.md section 8).

## Critical Files to Implement

### 1. Shared Types (/home/nisreen/Videos/yt-project/quran-intelligent-tafsir/packages/shared-types)
- **Create**: `types/` directory with:
  - `quran.d.ts` - Quran API response types
  - `tafsir.d.ts` - Tafsir agent data structures
  - `citation.d.ts` - Evidence citation system
  - `search.d.ts` - RAG search types
  - `agent.d.ts` - Agent orchestration types

### 2. API Service (/home/nisreen/Videos/yt-project/quran-intelligent-tafsir/services/api)
- **Expand**: `main.py` to implement:
  - Quran Foundation API proxy endpoints
  - Agent orchestration endpoints
  - Citation validation endpoints
  - Health and status monitoring

### 3. Ibn Kathir Agent (/home/nisreen/Videos/yt-project/quran-intelligent-tafsir/services/ai-engine/agents)
- **Create**: `ibn-kathir/` directory with:
  - `agent.py` - Main agent implementation
  - `source-retrieval.py` - Source lookup logic
  - `citation-validator.py` - Evidence validation
  - `response-formatter.py` - Thai explanation generation

### 4. Quran Reader Frontend (/home/nisreen/Videos/yt-project/quran-intelligent-tafsir/apps/web)
- **Create**: `src/` with:
  - `components/quran-reader/` - Main UI components
  - `hooks/use-quran-api.ts` - Quran API integration
  - `pages/` - Surah navigation and Ayah display
  - `components/tafsir-chat/` - Multi-agent chat interface

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-2)
1. Set up shared types package with comprehensive type definitions
2. Implement QUL JSON/SQLite ingestion for an approved Quran resource; add Quran Foundation API only for a verified runtime need
3. Create basic database schema and migrations
4. Add Redis/vector infrastructure only when an MVP workload demonstrates the need

### Phase 2: Core MVP (Weeks 3-6)
1. Implement Quran Reader UI with Thai/Arabic/English support
2. Build Ibn Kathir Agent with source-grounded explanations
3. Implement basic citation validation system
4. Create Tafsir chat interface with multi-agent integration

### Phase 3: Validation (Weeks 7-8)
1. Implement quality gates and testing
2. Add source validation for all agents
3. Build error handling and edge case management
4. Create comprehensive test coverage

## Key Technical Requirements

### 1. Quran Data Pipeline
- Start with reviewed QUL downloads (JSON for inspection, SQLite for larger resources)
- Keep Quran Foundation API as an optional backend adapter; store credentials server-side
- Implement Arabic text preservation
- Support Thai/English translations
- Audio recitation integration
- Word-by-word breakdown
- Verify resource rights, versions, Arabic integrity, and ayah mappings before publication

### 2. Agent Architecture
- Source-grounded AI (no fabricated references)
- 6 distinct agents with different methodologies
- Evidence citation system with VERIFIED/SOURCE-ATTRIBUTED labels
- Scholarly disagreement detection and display

### 3. Search and Retrieval
- Hybrid search: exact Ayah + Arabic full-text + semantic vector search
- PostgreSQL + pgvector integration
- Thai and Arabic language support
- Caching layer for performance

### 4. Quality Gates
- Source Availability Test
- Arabic Text Integrity Test
- Ayah Mapping Test
- Citation Accuracy Test
- Thai Translation Quality Test
- Scholarly Attribution Test

## Verification Steps

1. **Manual Testing**:
   - Test Quran verse retrieval and display
   - Verify Ibn Kathir agent explanations
   - Test agent comparison functionality
   - Validate source citations

2. **Automated Testing**:
   - Unit tests for all agents
   - Integration tests for API endpoints
   - End-to-end tests for Quran Reader
   - Security validation for religious content

3. **Performance Testing**:
   - API response times
   - Search functionality
   - Memory usage for RAG system
   - Concurrent agent processing

## Dependencies
- PostgreSQL; pgvector when semantic candidate discovery is needed
- Approved QUL resource downloads for the initial Quran/translation/tafsir corpus
- Quran Foundation API access only if an approved runtime use case requires it
- LLM provider (OpenAI/Anthropic/Gemini)
- Shamela or other providers only as optional adapters after access and rights review

## Timeline
- **Week 1-2**: Foundation and API integration
- **Week 3-4**: Quran Reader and Ibn Kathir Agent
- **Week 5-6**: Al-Tabari and Al-Sa'di Agents
- **Week 7-8**: Testing, validation, and documentation

## Risk Mitigation
1. **Data Quality**: Implement strict source validation before agent deployment
2. **Performance**: Start with single agent, scale gradually
3. **Content Accuracy**: Human review for high-risk religious content
4. **Dependencies**: Create fallback mechanisms for external APIs

This plan focuses on delivering the MVP requirements while maintaining the strict evidence-based approach required for religious content.