# AI Engine

Owns agent orchestration, retrieval, evidence validation and response formatting.

## Overview

This package contains the core AI components for QURAN AI:
- Tafsir agents (Ibn Kathir, Al-Tabari, Al-Qurtubi, Ibn Ashur, Al-Sa'di, Al-Zuhayli)
- Source retrieval systems for each agent's scholarly collection
- Citation validation and evidence verification
- Response formatting and quality assurance
- Agent orchestration and execution management

## Subpackages

### agents/

Specialized agents for each scholar's methodology:

#### Source-bound assistants

- **Available books**: Ibn Kathir, Al-Tabari, Al-Qurtubi, and Al-Sa'di
- **Retrieval**: Exact ayah/group mapping from each book's QUL SQLite corpus
- **Output**: Original source excerpt and AI-generated Thai explanation are
  separate and individually attributed
- **Status**: Source retrieval and chat API implemented; public display and
  model processing remain blocked until source rights are approved
- **Important**: These are AI study assistants over selected books, not
  simulations or impersonations of the named scholars

#### Al-Tabari Agent

- **Status**: Source-bound assistant available for the supplied corpus; source
  scholarly review is pending

#### Al-Qurtubi Agent

- **Status**: Source-bound assistant available for the supplied corpus; source
  scholarly review is pending

#### Ibn Ashur Agent
- **Methodology**: Linguistic and Maqasid analysis
- **Focus**: Arabic grammar, rhetoric, objectives of Sharia
- **Status**: Planned (Phase 3)

#### Al-Sa'di Agent

- **Status**: Source-bound assistant available in Arabic and Indonesian; the
  Indonesian source is never represented as Thai or Arabic

#### Al-Zuhayli Agent
- **Methodology**: Contemporary Fiqh and social applications
- **Focus**: Modern relevance, legal and social implications
- **Status**: Planned (Phase 3)

### source-retrieval/

Specialized source retrieval for each agent's scholarly collection:
- **Integration**: Shamela library, Quran Foundation API, Hadith databases
- **Quality**: Verification and licensing validation
- **Metadata**: Book, author, and scholarly information

### citations/

Evidence validation and citation management:
- **Validation**: Source authenticity and reliability checking
- **Citation Formatting**: Proper scholarly attribution
- **Quality Gates**: Evidence level determination (VERIFIED, SOURCE-ATTRIBUTED, etc.)

## Architecture

### Agent Execution Flow

1. **Context Processing**
   - Parse Ayah context (surah, ayah, Arabic text)
   - Identify scholarly methodology requirements
   - Prepare source retrieval parameters

2. **Source Retrieval**
   - Query specialized source collections
   - Apply relevance filtering
   - Prioritize authentic sources

3. **Citation Validation**
   - Verify source authenticity
   - Validate citation completeness
   - Apply scholarly gates

4. **Explanation Generation**
   - Generate source-grounded explanations
   - Apply quality gates
   - Format according to QURAN AI standards

5. **Response Formatting**
   - Apply evidence level labeling
   - Format citations for scholarly attribution
   - Identify scholarly disagreements

### Quality Gates

Each agent enforces strict quality gates:

#### Ibn Kathir Agent
- **Citation Accuracy**: 95% minimum source attribution
- **Content Authenticity**: 98% minimum authenticity
- **Thai Translation Quality**: Natural flow and accuracy
- **Scholarly Attribution**: Clear distinction between AI and scholarly content

#### All Agents
- **No Fabricated References**: All claims must be traceable
- **Evidence Level Classification**: VERIFIED, SOURCE-ATTRIBUTED, UNVERIFIED, AI SYNTHESIS
- **Scholarly Disagreement Detection**: Identify and display differences of opinion
- **Source Grounding**: Every claim must reference authentic sources

## Security and Integrity

### Religious Accuracy Rules

1. **Never fabricate Quranic verses** - All Quran text must come from authoritative sources
2. **Never invent Hadith references** - All Hadith must be from authenticated collections
3. **Never invent quotations from scholars** - All scholarly content must be traceable
4. **Never confuse AI analysis with scholarly quotations** - Clear distinction required
5. **Never hide recognized differences of opinion** - Scholarly disagreements must be displayed
6. **Never classify Hadith without supporting grading** - Only use authenticated grading
7. **Distinguish Tafsir from personal reflection** - Clear source attribution
8. **Abstain when reliable evidence is unavailable** - Error on the side of caution
9. **Preserve original Arabic text** - No corruption of canonical text
10. **Require human review for high-risk conclusions** - Complex theological matters need human oversight

### Data Protection

- **Access Control**: Role-based access for different user types
- **Audit Logging**: Full traceability of all AI operations
- **Source Version Tracking**: Track changes in source materials
- **Copyright and Licensing**: Validate usage permissions
- **Rate Limiting**: Protect against abuse and ensure fair resource usage

## Integration Points

### With Quran Reader Frontend

- **Ayah Selection**: Receive Ayah context from frontend
- **Agent Orchestration**: Execute appropriate agents
- **Response Display**: Format and display scholarly explanations
- **Citation Display**: Show source attribution and references

### With Backend API

- **REST Endpoints**: HTTP APIs for agent execution
- **WebSocket Support**: Real-time agent communication
- **Caching**: Redis-based response caching
- **Monitoring**: Metrics and health checks

### With Database

- **Source Storage**: Store retrieved tafsir sources
- **Citation History**: Track source validation and usage
- **User Progress**: Store reading progress and bookmarks
- **Agent Execution Logs**: Monitor and analyze agent performance

## Deployment Considerations

### Resource Requirements

- **Memory**: Minimum 8GB for agent orchestration and LLM processing
- **CPU**: Multi-core for parallel agent execution
- **Storage**: 100GB+ for source databases and vector indexes
- **Network**: Reliable internet connection for external API calls

### Scaling Strategy

1. **Start Small**: Single agent deployment for MVP
2. **Horizontal Scaling**: Add more agents as needed
3. **Load Balancing**: Distribute requests across multiple instances
4. **Cache Layer**: Redis for frequently accessed data
5. **Database Optimization**: Partition by scholar and surah

### Monitoring and Maintenance

- **Health Checks**: Agent status and performance monitoring
- **Error Tracking**: Comprehensive error logging and alerting
- **Source Validation**: Regular updates and quality checks
- **Performance Metrics**: Response times, cache hit rates, accuracy
- **Security Audits**: Regular security assessments and compliance checks

## Development Guidelines

### Code Quality

- **Documentation**: Comprehensive docstrings and comments
- **Testing**: Unit tests for all agents and components
- **Code Review**: Peer review for all changes to agent logic
- **Version Control**: Track all source materials and configurations

### Development Process

1. **Source Validation**: Verify all sources before agent deployment
2. **Quality Assurance**: Run all quality gates before release
3. **Testing**: Comprehensive testing with authentic and edge cases
4. **Validation**: Human review for high-risk religious conclusions
5. **Deployment**: Gradual rollout with monitoring and rollback capability

### Future Enhancements

1. **Additional Scholars**: Expand agent portfolio beyond the 6 core scholars
2. **Advanced Search**: Natural language query support
3. **Personalization**: User-specific study goals and recommendations
4. **Multi-language Support**: Additional languages beyond Thai/Arabic/English
5. **Mobile Optimization**: Lightweight versions for mobile devices
6. **Offline Mode**: Cached content for offline reading

## References

- **Quran Foundation API**: https://api-docs.quran.com/docs/api-reference/
- **Shamela Library**: https://github.com/ragaeeb/shamela
- **Islamic Studies Standards**: Classical Islamic scholarship methodologies
- **Source Governance**: Source registry and validation protocols

The AI Engine implements QURAN AI's core mission: evidence-based Quran study through authentic scholarly sources, maintained with the highest standards of religious accuracy and academic integrity.