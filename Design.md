# SYSTEM ARCHITECTURE & UI/UX DESIGN SPECIFICATION
## QURAN AI: SUPER WEBAPP (QURAN READER, MULTI-AGENT TAFSIR & ACTIVE LEARNING)
**Version**: 2.0  
**Status**: Architecture Approved for Vibe Coding  

---

## 1. HIGH-LEVEL SYSTEM ARCHITECTURE

```text
+---------------------------------------------------------------------------------------+
|                                    CLIENT BROWSER                                     |
|                       Next.js 14+ (App Router) + Tailwind CSS + shadcn/ui             |
+-------------------------------------------+-------------------------------------------+
                                            |
                         HTTPS / SSE Stream | GraphQL / REST
                                            v
+---------------------------------------------------------------------------------------+
|                                      API GATEWAY                                      |
+-------------------------------------------+-------------------------------------------+
                     |                                              |
                     v                                              v
+-----------------------------------------+   +-----------------------------------------+
|        FASTAPI AI & RAG SERVICE         |   |         STRAPI HEADLESS CMS             |
|   (Quran & Multi-Agent Tafsir Engine)   |   |   (Courses, Chapters, Gamification)     |
+-----------------------------------------+   +-----------------------------------------+
| - Multi-Agent Orchestrator              |   | - Dynamic Content Zone Engine           |
| - Hybrid RAG (pgvector + FTS)           |   | - User Progress & Streak Tracker        |
| - Citation & Evidence Validator         |   | - Strapi MCP Server (AI Course Builder) |
| - Flashcard & Quiz Synthesizer          |   | - Cloudinary Media Connector            |
+--------------------+--------------------+   +--------------------+--------------------+
                     |                                              |
                     +----------------------+-----------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                                 DATA & STORAGE LAYER                                  |
|   PostgreSQL 16 + pgvector  |  Redis Cache  |  Cloudinary (PDFs)  |  Quran CDN (Audio)|
+---------------------------------------------------------------------------------------+
```

---

## 2. UI/UX LAYOUT SPECIFICATION: THE 3-COLUMN ADAPTIVE WORKSPACE

The Super WebApp employs a responsive 3-column workspace that adapts fluidly between **Quran Reading Mode**, **Gamified Study Mode**, and **Research/Document Mode**.

```text
+-------------------+---------------------------------------+---------------------------+
|   NAV & CURRICULA  |          CENTER STUDY CANVAS          |     TAFSIR & AI TOOLS     |
|   (Width: 260px)  |             (Flex 1 Grow)             |       (Width: 420px)      |
+-------------------+---------------------------------------+---------------------------+
| [Logo: Quran AI]  | [Surah Header: 36. Ya-Sin (Makki)]    | Tabs: [Tafsir|Quiz|Cards] |
|                   |                                       |                           |
| Navigation:       | (Ayah 13)                             | Agent Selector:           |
| - Quran Index     |  وَاضْرِبْ لَهُم مَّثَلًا أَصْحَابَ الْقَرْيَةِ   | [Ibn Kathir] [Al-Tabari]  |
| - Study Courses   |  "จงยกอุทาหรณ์แก่พวกเขาถึงชาวเมือง..." | [Al-Qurtubi] [Ibn Ashur]  |
| - Flashcard Decks |                                       |                           |
| - Quiz History    | [Audio: Recite] [Tafsir] [Add Card]   | Chat Stream:              |
| - Document PDF    |---------------------------------------| "According to Tafsir      |
|                   | (Ayah 14)                             | Ibn Kathir (Vol 6, p.565) |
| Gamification:     |  إِذْ أَرْسَلْنَا إِلَيْهِمُ اثْنَيْنِ فَكَذَّبُوهُمَا  | the town referred to is   |
| - Zap Streak: 7d  |  "เมื่อเราส่ง (รอซูล) สองคนไปยังพวกเขา" | Antioch (Antakiya)..."    |
| - Gems: 1,420     |                                       |                           |
| - Hearts: 5/5     | [Interactive Lesson Slide Overlay]    | [Evidence: VERIFIED]      |
|                   | (Theory / MCQ / Fill Blank / Match)   | [View Classical Arabic]   |
| [User / Billing]  |                                       | [Disagreement Matrix]     |
+-------------------+---------------------------------------+---------------------------+
```

### 2.1 Center Study Canvas Modes
1. **Quran Reader Canvas**:
   - Arabic verse text rendered in large Uthmani script (`text-2xl md:text-3xl font-arabic leading-[2.2]`).
   - Clean alignment with Thai translation directly below in readable sans-serif (`text-base text-slate-700`).
   - Interactive quick-action bar on Ayah hover: `[Listen Audio]`, `[Open Tafsir]`, `[Create Flashcard]`, `[Bookmark]`.
2. **Interactive Lesson Canvas (SkillPet Mode)**:
   - Fullscreen focused learning slide with progress bar at top.
   - Dynamic slide blocks:
     - **Theory Block**: Rich markdown with Quranic calligraphy and translation.
     - **MCQ Block**: Card selection with instant green/red validation and explanatory feedback.
     - **Fill-in-the-Blank Block**: Arabic root drag/drop with hint toggle.
     - **Matching Block**: Dual-column interactive connector for terms and definitions.
3. **Document Research Canvas (MERN Assistant Mode)**:
   - Split-screen PDF viewer with page navigation, zoom, search, and text-selection AI lookup.

---

## 3. DESIGN SYSTEM & VISUAL TOKENS

### 3.1 Color Palette
- **Primary (Deep Quranic Emerald)**:
  - `primary-900`: `#073B32` (Headers, brand borders)
  - `primary-800`: `#0E5E4F` (Primary brand color, buttons, active tabs)
  - `primary-700`: `#147B68`
  - `primary-100`: `#E6F4F1` (Light backgrounds, selected cards)
- **Accent (Imperial Gold)**:
  - `accent-500`: `#C9A227` (Ayah numbers, bookmark stars, streak badges, gems)
  - `accent-100`: `#FEF9E7` (Highlight tints)
- **Neutrals**:
  - `surface-light`: `#F5F7F6` (App background)
  - `surface-card`: `#FFFFFF` (Card surfaces with subtle border `border-slate-200/80`)
  - `text-main`: `#1E293B` (Body text)
  - `text-muted`: `#64748B` (Secondary text, metadata)
- **Status & Badges**:
  - `verified`: `#15803D` (Green badge)
  - `disagreement`: `#B45309` (Amber badge)
  - `unverified`: `#DC2626` (Red badge)
  - `ai-synthesis`: `#6366F1` (Indigo badge)

### 3.2 Typography
- **Arabic Quranic Text**: `Amiri Quran`, `Noto Naskh Arabic`, `Scheherazade New` (`font-arabic`, `dir="rtl"`).
- **Thai Body Text**: `Noto Sans Thai`, `Sarabun` (`font-thai`).
- **UI & English Text**: `Inter`, `system-ui` (`font-sans`).

---

## 4. DATABASE SCHEMAS & DATA STRUCTURES

### 4.1 PostgreSQL (Core Quran & Tafsir Knowledge Base)
```sql
-- Quranic Verses
CREATE TABLE quran_ayahs (
    id SERIAL PRIMARY KEY,
    surah_number INT NOT NULL,
    ayah_number INT NOT NULL,
    text_uthmani TEXT NOT NULL,
    text_clean TEXT NOT NULL,
    juz_number INT NOT NULL,
    hizb_quarter INT NOT NULL,
    sajdah BOOLEAN DEFAULT FALSE,
    UNIQUE (surah_number, ayah_number)
);

-- Verified Classical Tafsir Passages
CREATE TABLE tafsir_passages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id VARCHAR(50) NOT NULL, -- 'ibn_kathir', 'tabari', 'qurtubi', 'ibn_ashur', 'sadi', 'zuhayli'
    scholar_name_ar VARCHAR(100) NOT NULL,
    scholar_name_en VARCHAR(100) NOT NULL,
    surah_number INT NOT NULL,
    ayah_start INT NOT NULL,
    ayah_end INT NOT NULL,
    arabic_text TEXT NOT NULL,
    translation_th TEXT,
    translation_en TEXT,
    volume INT,
    page INT,
    edition VARCHAR(100),
    source_url TEXT,
    embedding vector(1536), -- pgvector embedding for semantic retrieval
    verification_status VARCHAR(20) DEFAULT 'VERIFIED'
);

-- Vector Search Index
CREATE INDEX ON tafsir_passages USING hnsw (embedding vector_cosine_ops);
```

### 4.2 Strapi CMS Content Types (Gamified Curricula & Users)
1. **Course**:
   - `title`: String
   - `slug`: UID
   - `description`: Text
   - `difficulty`: Enum (`beginner`, `intermediate`, `advanced`)
   - `access_type`: Enum (`free`, `premium`)
   - `banner`: Media (Cloudinary)
   - `chapters`: Relation (Has Many Chapters)
2. **Chapter**:
   - `title`: String
   - `slug`: UID
   - `sort_order`: Integer
   - `emoji`: String
   - `estimated_minutes`: Integer
   - `content_blocks`: Dynamic Zone:
     - `learning.theory-block` (`title`, `content_markdown`, `quran_ref`)
     - `learning.mcq-block` (`question`, `options`: Component, `explanation`)
     - `learning.fill-blank-block` (`sentence`, `correct_words`, `distractors`)
     - `learning.matching-block` (`pairs`: Component)
3. **AppUser & Progress**:
   - `email`: String (Unique)
   - `streak_count`: Integer
   - `last_active_date`: Date
   - `gems_wallet`: Integer
   - `hearts_count`: Integer
   - `stripe_subscription_status`: Enum (`none`, `active`, `past_due`)
   - `completed_chapters`: Relation

### 4.3 AI Study Assistant Entities (MongoDB / PostgreSQL)
1. **Flashcard Deck**:
   - `id`: UUID
   - `user_id`: UUID
   - `surah_number`: Integer
   - `ayah_number`: Integer
   - `front_text_ar`: Text
   - `back_translation`: Text
   - `root_word`: String
   - `key_tafsir_note`: Text
   - `is_favorite`: Boolean
2. **Quiz Session**:
   - `id`: UUID
   - `user_id`: UUID
   - `surah_number`: Integer
   - `total_questions`: Integer
   - `score`: Integer
   - `time_spent_seconds`: Integer
   - `question_breakdown`: JSONB (Question, User Answer, Correct Answer, Classical Rationale)

---

## 5. API CONTRACTS & REAL-TIME FLOWS

### 5.1 FastAPI RAG Endpoints
- `GET /api/v1/quran/surahs`: List of 114 Surahs with metadata.
- `GET /api/v1/quran/surah/{id}/ayahs`: Complete Arabic, translation, and audio URLs.
- `POST /api/v1/tafsir/agents/explain`:
  - Request: `{ "surah": 36, "ayah": 13, "agent_ids": ["ibn_kathir", "qurtubi"], "language": "th" }`
  - Response: Server-Sent Events (SSE) streaming Markdown with structured citation blocks.
- `POST /api/v1/tafsir/compare`:
  - Request: `{ "surah": 36, "ayah": 13 }`
  - Response: JSON Matrix comparing views of Tabari, Ibn Kathir, Qurtubi, and Ibn Ashur.
- `POST /api/v1/study/generate-flashcards`:
  - Request: `{ "surah": 36, "ayah_range": [1, 12], "card_count": 10 }`
  - Response: JSON Array of structured flashcards.
- `POST /api/v1/study/generate-quiz`:
  - Request: `{ "surah": 36, "question_count": 5, "difficulty": "intermediate" }`
  - Response: Interactive quiz package with answers and source justifications.

### 5.2 Strapi CMS MCP Endpoints (For Tracer / AI Coding)
- `POST /mcp/content/generate-course`: AI automated course curriculum builder.
- `POST /mcp/content/publish-chapter`: Publishes verified exercise blocks.

---

## 6. SECURITY, CITATION & RELIGIOUS AUDIT POLICY

1. **Anti-Hallucination Guardrails**:
   - Every agent prompt injects strict system boundary directives forbidding ungrounded commentary.
   - If an embedding search yields a cosine similarity score `< 0.72`, the agent responds with a standardized missing-evidence notice.
2. **Content Protection & Licensing**:
   - Canonical text is locked in read-only tables verified by SHA-256 checksums.
   - Only authorized editions of classical Tafsir works from authenticated partners (Maktabah Shamela open access, King Fahd Complex) are stored and queried.\n