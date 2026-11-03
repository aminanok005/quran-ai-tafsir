# QURAN AI Super WebApp - Tarteel QUL Integration Plan

## Overview
Integration of Tarteel Quranic Universal Library (QUL) as the primary data source for the QURAN AI Super WebApp.

## QUL Resources Available

### 1. Data Dumps
- **Primary Data**: `mini_quran_dev.sql.zip` (https://static-cdn.tarteel.ai/qul/mini-dumps/mini_quran_dev.sql.zip)
- **Full Dataset**: Available at https://qul.tarteel.ai/resources
- **Formats**: JSON (prototypes) and SQLite (production)

### 2. Data Model
- **Verses**: surah_id, ayah_number, text_uthmani, text_simple, juz, hizb, page
- **Words**: surah_id, ayah_number, word_position, text, translation, transliteration, root
- **Translations**: Multiple languages (Arabic, Thai, English, Urdu)
- **Tafsirs**: Multiple classical sources
- **Audio**: Gapless and ayah-by-ayah recitations
- **Morphology**: Root words, grammatical analysis
- **Mushaf Layouts**: Different page layouts

### 3. Integration Benefits
- ✅ **Single authoritative source** for all Quranic content
- ✅ **Verified translations** from King Fahd Complex
- ✅ **Classical tafsir sources** aligned with our 6 agents
- ✅ **Audio recitations** from Tarteel's verified reciters
- ✅ **Word-by-word morphology** for flashcards and study tools
- ✅ **Standardized identifiers** for reliable joins

## Implementation Strategy

### Phase 1: Data Download & Schema Alignment
1. Download QUL data dump
2. Map QUL schema to QURAN AI database models
3. Create import scripts for PostgreSQL + pgvector

### Phase 2: Agent Knowledge Base Population
1. Seed tafsir_passages table with QUL tafsir data
2. Create embeddings for vector search
3. Build full-text search indexes

### Phase 3: API Integration
1. Replace Quran Foundation API with QUL data where appropriate
2. Keep Quran Foundation API for specific features
3. Hybrid approach for maximum coverage

## Technical Implementation

### 1. Data Download Script
```bash
# Download QUL data dump
curl -L -o mini_quran_dev.sql.zip https://static-cdn.tarteel.ai/qul/mini-dumps/mini_quran_dev.sql.zip
unzip mini_quran_dev.sql.zip
```

### 2. Database Import
```sql
-- Import into PostgreSQL
psql -d quran_ai -f mini_quran_dev.sql
```

### 3. Schema Mapping
Map QUL tables to QURAN AI models:
- `verses` → `quran_ayahs`
- `words` → `word_translations`
- `translations` → `translations`
- `tafsirs` → `tafsir_passages`
- `audio_files` → Audio URLs in ayah model
- `roots` → Root word data for flashcards

## Configuration

Add to `.env.example`:
```env
# QUL Data Source
QUL_DATA_DUMP_URL=https://static-cdn.tarteel.ai/qul/mini-dumps/mini_quran_dev.sql.zip
QUL_RESOURCES_BASE_URL=https://qul.tarteel.ai/resources
QUL_API_BASE_URL=https://qul.tarteel.ai/api (coming soon)
```

## License & Usage
- QUL uses MIT license
- Verify dataset-specific licensing before production
- Commercial use requires checking individual resource licenses

## Next Steps
1. Execute data download and import
2. Run schema alignment migration
3. Test agent retrieval with real data
4. Build embeddings for RAG system