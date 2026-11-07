# Database

PostgreSQL is the system of record. The current schema requires pgvector for
tafsir embeddings; semantic retrieval additionally requires embedding-provider
configuration.

## Local PostgreSQL with pgvector

Start the development database from the repository root:

```bash
docker compose -f docker/docker-compose.yml up -d db
```

The Compose service uses PostgreSQL 16 with pgvector 0.8.1 and persists data in
the `postgres_data` volume. Local defaults are database `quran_ai`, user
`quran_ai`, and password `quran_ai_dev`; set `POSTGRES_DB`, `POSTGRES_USER`,
and `POSTGRES_PASSWORD` in the root `.env` to override them. These defaults are
for local development only.

The API container connects to the `db` service automatically. For host-run
migrations, use the equivalent localhost URL:

```bash
DATABASE_URL=postgresql+psycopg://quran_ai:quran_ai_dev@localhost:5432/quran_ai \
  bun run db:migrate
```

The initial migration enables the `vector` extension. Verify it after migration:

```bash
docker compose -f docker/docker-compose.yml exec db \
  psql -U quran_ai -d quran_ai -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```

## Seeding canonical Quran text

The canonical seed command fetches all 6,236 ayahs from the Quran Foundation
Content API v4 by surah and page, validates each surah's canonical ayah count
and uniqueness, then upserts them into `quran_ayahs`.

Set `QURAN_API_CLIENT_ID`, `QURAN_API_CLIENT_SECRET`, and `DATABASE_URL` in the
process environment using your local secret-management method, then run:

```bash
bun run db:seed
```

The seeder uses the idempotent `(surah_number, ayah_number)` key. It must not be
run against production without confirming the source license and target database.

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