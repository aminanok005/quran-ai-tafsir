# Database

PostgreSQL is the system of record. pgvector is an optional retrieval extension.

## Schema Overview

### Quran Tables
- `surahs` - Surah metadata
- `ayahs` - Individual verses with Arabic text
- `translations` - Thai, English, and other translations
- `recitations` - Audio recitation metadata
- `word_translations` - Word-by-word breakdowns

### Knowledge Tables
- `scholars` - Scholar biographical information
- `tafsir_books` - Book metadata
- `tafsir_editions` - Specific editions with licensing
- `tafsir_passages` - Individual commentary passages
- `source_references` - Citation metadata
- `hadith_sources` - Hadith collection metadata
- `hadith_reports` - Individual hadith reports

### AI Tables
- `agents` - Agent configurations
- `agent_configs` - Runtime configurations
- `agent_runs` - Execution history
- `retrieval_results` - RAG retrieval logs
- `citations` - Citation validation records
- `verification_results` - Quality gate results

### User Tables
- `users` - User accounts
- `bookmarks` - Saved verses
- `reading_progress` - Reading position
- `study_notes` - Personal notes
- `chat_sessions` - Chat history
- `chat_messages` - Individual messages

### Governance Tables
- `source_permissions` - Licensing and rights
- `content_reviews` - Human review records
- `audit_logs` - System audit trail

## Migration Strategy

1. Initial schema creation with Quran foundation tables
2. Knowledge base tables for tafsir sources
3. AI system tables for agent orchestration
4. User and governance tables

All religious source records must be traceable to their original source.