# PROJECT: QURAN AI — Intelligent Tafsir & Quran Study Platform
### แพลตฟอร์มอ่านอัลกุรอาน พร้อม AI Agents ที่อ้างอิงตำราตัฟซีรของอุละมาอ์

ผมมองว่าโปรเจกต์นี้สามารถพัฒนาเป็นแพลตฟอร์มศึกษากุรอานที่มีคุณค่ามากกว่าแอปอ่านอัลกุรอานทั่วไป เพราะจุดเด่นคือ **เมื่อผู้ใช้อ่านถึงอายะฮ์ใด ระบบจะเปิดพื้นที่สนทนาเพื่ออธิบายอายะฮ์นั้น โดยมี AI Agents แยกตามตำราตัฟซีรและความเชี่ยวชาญของนักวิชาการ**

แนวคิดสำคัญคือ ผู้ใช้ไม่จำเป็นต้องค้นหาตัฟซีรจากหลายเว็บไซต์เอง ระบบจะรวบรวมแหล่งอ้างอิงและนำเสนอให้ศึกษาในหน้าจอเดียว

ผมเสนอให้ใช้ชื่อโครงการเบื้องต้นว่า

**QURAN AI — The Intelligent Quran Study Companion**

คำขวัญ:

*Read the Quran. Understand the Meaning. Explore the Tafsir. Follow the Evidence.*

## 1. Product Vision

สร้างแพลตฟอร์มศึกษากุรอานที่ผสาน 3 องค์ประกอบเข้าด้วยกัน

1. **Quran Reader:** อ่านอัลกุรอานจาก API พร้อมภาษาอาหรับ คำอ่าน และคำแปล
2. **Tafsir Intelligence:** วิเคราะห์อายะฮ์ผ่าน AI Agents ที่อ้างอิงตำราตัฟซีรจริง
3. **Interactive Islamic Knowledge:** สนทนา ตั้งคำถาม เปรียบเทียบคำอธิบาย และตรวจสอบหลักฐานจากอัลกุรอาน หะดีษ และตำราของอุละมาอ์

### หลักการสำคัญที่สุด

AI ต้องไม่สร้างคำพูดขึ้นมาแล้วอ้างว่าเป็นคำพูดของอิมามอิบนุกะษีรหรืออุละมาอ์ท่านอื่น

เราจะใช้แนวคิด:

**Source-Grounded Tafsir AI**

หมายถึง AI ต้องค้นหาและอ้างอิงข้อความจากตำราจริงก่อนตอบ พร้อมแสดงชื่อหนังสือ เล่ม หน้า หรือเลขอายะฮ์ตามข้อมูลที่มี

ต้องแยกให้ชัดเจนระหว่าง:
- ข้อความจากอัลกุรอาน
- คำอธิบายจากนักตัฟซีร
- หะดีษและรายงานจากสะละฟุศศอลิห์
- การวิเคราะห์ของ AI
- ประเด็นที่นักวิชาการมีความเห็นแตกต่างกัน

---

## 2. Data Sources & Knowledge Architecture

ส่วนนี้เป็นหัวใจของโปรเจกต์ เพราะความน่าเชื่อถือของระบบขึ้นอยู่กับแหล่งข้อมูลมากกว่าโมเดล AI

เริ่มจาก **Quranic Universal Library (QUL)** เป็นแหล่งดาวน์โหลดหลักสำหรับ
การนำเข้าข้อมูลอัลกุรอานและทรัพยากรที่เกี่ยวข้อง แล้วเก็บ Resource ที่ผ่านการ
ตรวจสอบไว้ในฐานข้อมูลของเราเอง

### 2.1 QUL — Quran data and resource downloads

QUL รวม Resource หลายหมวด เช่น Quran scripts, translations, tafsir,
recitations, morphology, topics, surah information และ structural metadata
มีไฟล์ดาวน์โหลด JSON และ SQLite เหมาะกับการนำเข้าแบบ batch

**ข้อควรรู้:** [QUL API docs](https://qul.tarteel.ai/docs/api) ระบุว่า Public
REST API ยังอยู่ระหว่างออกแบบ จึงใช้ไฟล์ Resource จากหน้าเว็บ ไม่เรียก
`/api/v1` ใน production จนกว่าจะเปิดให้บริการจริง ตรวจสอบผู้แต่ง ฉบับพิมพ์
สิทธิ์การใช้ และ mapping ของ Resource แต่ละรายการก่อนนำเข้า

### 2.2 Quran Foundation API — optional runtime source

ใช้ [Quran Foundation API](https://api-docs.quran.com/docs/api-reference/)
เป็น adapter เสริมเมื่อจำเป็นต้องเรียกข้อมูลสด ไม่ใช่ source หลักสำหรับ QUL
import ต้องตรวจสอบ credential, terms, Thai translation และความซ้ำซ้อนของข้อมูล
ก่อนใช้งาน โดยเก็บ credentials ไว้ฝั่ง Backend เท่านั้น

### 2.3 Tafsir and Hadith sources

เริ่มจาก tafsir Resource ของ QUL ที่มีอยู่จริงและได้รับอนุญาต เปิดใช้ทีละ
หนังสือ/ฉบับพิมพ์ Shamela หรือ provider อื่นเป็น adapter เพิ่มเติมเมื่อ
ตรวจสอบสิทธิ์แล้ว ส่วน hadith corpus และ grading ต้องเลือกแหล่งตรวจสอบต่างหาก
เพราะ QUL docs ไม่ได้ระบุบริการ hadith verification ที่ครบถ้วน

ไฟล์ QUL SQLite สำหรับ Ibn Kathir, Tabari, Qurtubi และ As-Saadi (Arabic /
Indonesian) อยู่ใน `data-tafsir/` และตัวดึงข้อมูล Ibn Kathir อ่านฐานข้อมูลนี้
โดยตรงได้แล้ว ใช้ `QURAN_TAFSIR_DB_PATH` หรือ config `source_path` เลือกไฟล์
อื่น; การเลือก DB ไม่ได้เปลี่ยนตัวตนหรือ methodology ของ Agent และทุกชุดยังมี
สถานะ rights/verification เป็น unknown จนกว่าจะ review

Agent ต้องค้นจากข้อมูลที่นำเข้าและตรวจสอบแล้ว ไม่เรียกฐานข้อมูลภายนอกในทุกคำถาม
และห้ามระบุเล่ม หน้า ฉบับพิมพ์ หรือระดับหะดีษที่ไม่มีในข้อมูลต้นทาง
อ่านข้อกำหนดและ workflow ได้ที่ [Data Integration Guide](docs/sources/README.md).
QUL tafsir IDs ที่ให้มาและสถานะสิทธิ์/ภาษาสรุปไว้ในคู่มือเดียวกัน โดยยังต้อง
ตรวจสอบไฟล์จริงก่อนนำเข้าและเปิดใช้ Agent.

---

# 3. Production PRD.md — Founder / VC / Engineer Ready

ด้านล่างเป็นเอกสารตั้งต้นสำหรับนำไปใช้กับ Cursor, Kilo Code, Claude Code หรือ AI Coding Agent

# QURAN AI
## Intelligent Quran Study & Tafsir Platform
### Production PRD — Founder / VC / Engineer Ready

Version: 1.0  
Status: Proposed / Pre-Implementation  
Product Type: AI-Powered Islamic Knowledge Platform

---

# 1. PRODUCT VISION

Build an intelligent Quran study platform that combines authentic Quranic text, classical Tafsir literature, Hadith references, and AI-powered scholarly research.

Users can read the Quran verse by verse. When selecting an Ayah, multiple specialized Tafsir Agents automatically retrieve and explain the verse using recognized scholarly sources.

The platform must prioritize authenticity, source traceability, scholarly differences, and transparency.

### Core Philosophy

- Quran First
- Authentic Sources First
- Evidence Before Interpretation
- Classical Scholarship + Modern Technology
- No Fabricated Religious References
- Respect Scholarly Differences

### Product Promise

Every explanation must be traceable to its original source whenever a source is available.

AI is a research and learning assistant, NOT a replacement for qualified Islamic scholars.

---

# 2. CORE ACTORS

| Actor | Responsibility |
|---|---|
| Reader | Read Quran and explore Tafsir |
| Student | Study Arabic, Tafsir and Hadith |
| Researcher | Compare scholarly interpretations |
| Scholar / Reviewer | Review and verify Islamic content |
| Content Administrator | Manage books and source metadata |
| Platform Administrator | Manage users, models and infrastructure |

---

# 3. CORE USER EXPERIENCE

## Main Reading Interface

Desktop layout:

LEFT PANEL:
- Surah Navigation
- Juz Navigation
- Surah Search
- Bookmarks
- Reading History

CENTER PANEL:
- Arabic Quran Text
- Ayah Numbers
- Thai Translation
- English Translation
- Audio Playback
- Word-by-Word
- Highlight Selected Ayah

RIGHT PANEL:
- AI Tafsir Chat
- Tafsir Agent Selection
- Scholar Comparison
- Source References
- Ask Follow-up Questions

### Core Interaction

User opens Surah Yasin.

User selects Ayah 13.

System automatically:

1. Identifies Surah and Ayah.
2. Retrieves authentic Quran text.
3. Retrieves available translations.
4. Retrieves relevant Tafsir sources.
5. Sends contextual source material to specialized Agents.
6. Generates structured explanations.
7. Displays citations and references in the chat panel.

Example:

User selects:

Surah Yasin 36:13

The right panel displays:

- Ibn Kathir Tafsir
- Al-Tabari Tafsir
- Al-Qurtubi Tafsir
- Ibn Ashur Tafsir
- Al-Sa'di Tafsir
- Wahbah Al-Zuhayli Tafsir

Each Agent provides an independent source-grounded explanation.

---

# 4. TAFSIR AGENT ARCHITECTURE

## Agent 01 — Ibn Kathir Agent

Arabic: تفسير ابن كثير

Mission:
Explain Quranic verses using Quran, authentic Hadith and reports from the Salaf.

Responsibilities:
- Tafsir bil-Ma'thur
- Quran explains Quran
- Hadith references
- Reports from Sahabah
- Reports from Tabi'in
- Identify Isra'iliyyat reports
- Distinguish authentic and weak narrations when grading evidence is available

Output:
- Main explanation
- Supporting Quranic verses
- Hadith references
- Salaf reports
- Source reliability notes

## Agent 02 — Al-Tabari Agent

Arabic: تفسير الطبري

Mission:
Explore early Quranic interpretations and scholarly reports.

Responsibilities:
- Early Tafsir narrations
- Sahabah interpretations
- Tabi'in interpretations
- Arabic linguistic analysis
- Differences between early interpretations
- Analysis of evidence and preferred interpretations

Output:
- Reported interpretations
- Source attribution
- Differences of opinion
- Linguistic explanation
- Scholarly analysis

## Agent 03 — Al-Qurtubi Agent

Arabic: تفسير القرطبي

Mission:
Explain legal rulings derived from Quranic verses.

Responsibilities:
- Ahkam al-Quran
- Fiqh analysis
- Differences between Madhahib
- Legal evidence
- Relevant Hadith
- Contextual legal discussions

Output:
- Relevant rulings
- Madhhab comparisons
- Supporting evidence
- Areas of scholarly disagreement

Important:
Do not present one Madhhab's position as unanimous consensus.

## Agent 04 — Ibn Ashur Agent

Arabic: التحرير والتنوير

Mission:
Analyze Quranic language, rhetoric, context and objectives.

Responsibilities:
- Arabic grammar
- Balaghah
- Linguistic meanings
- Quranic context
- Maqasid al-Shariah
- Thematic connections between verses

Output:
- Linguistic analysis
- Rhetorical interpretation
- Contextual explanation
- Higher objectives and lessons

## Agent 05 — Al-Sa'di Agent

Arabic: تفسير السعدي

Mission:
Provide accessible explanations for general Quran readers.

Responsibilities:
- Simplified Tafsir
- Main meanings
- Practical lessons
- Spiritual reflection
- Clear explanations

Output:
- Easy-to-understand Tafsir
- Main lessons
- Practical applications

## Agent 06 — Wahbah Al-Zuhayli Agent

Arabic: التفسير المنير

Mission:
Connect classical Tafsir with contemporary Islamic scholarship.

Responsibilities:
- Fiqh analysis
- Contemporary applications
- Quranic guidance
- Social and ethical implications
- Comparative scholarly explanations

Output:
- Contemporary relevance
- Legal and social implications
- Supporting scholarly references

---

# 5. AGENT GOVERNANCE

IMPORTANT:

These are AI agents organized by scholarly source and methodology.

They are NOT the actual scholars.

The system must never claim that an AI-generated statement was personally spoken or written by Ibn Kathir, Al-Tabari or another scholar.

Each Agent must follow:

1. Retrieve original source material.
2. Identify the relevant passage.
3. Preserve original Arabic quotations when available.
4. Generate a clearly labeled explanation.
5. Attach citations.
6. Identify uncertainty.
7. Abstain when reliable sources are unavailable.

### Evidence Labels

VERIFIED:
Directly supported by an identifiable source.

SOURCE-ATTRIBUTED:
Found in a scholarly text, but authenticity of the underlying report has not been independently verified.

SCHOLARLY DIFFERENCE:
Multiple recognized scholarly interpretations exist.

UNVERIFIED:
Insufficient evidence to establish the claim.

AI SYNTHESIS:
An explanation generated by AI from cited sources, not a quotation from a scholar.

---

# 6. MULTI-AGENT ORCHESTRATION

Main workflow:

User selects Ayah
        |
        v
Quran Context Resolver
        |
        v
Source Retrieval Engine
        |
        v
Tafsir Knowledge Base
        |
        v
Agent Orchestrator
        |
        +---- Ibn Kathir Agent
        |
        +---- Al-Tabari Agent
        |
        +---- Al-Qurtubi Agent
        |
        +---- Ibn Ashur Agent
        |
        +---- Al-Sa'di Agent
        |
        +---- Al-Zuhayli Agent
        |
        v
Evidence & Citation Validator
        |
        v
Response Formatter
        |
        v
Realtime Chat Interface

### Important Design Decision

Agents should not independently invent their own source material.

All agents must retrieve information from the same verified knowledge infrastructure.

Each agent has a separate source collection, methodology, retrieval configuration and output schema.

---

# 7. TAFSIR KNOWLEDGE ENGINE

## Data Sources

Primary:
- QUL resource downloads (JSON / SQLite, subject to resource-level review)
- Original Quran text
- Verified Quran translations

Optional:
- Quran Foundation API for a verified runtime use case
- Shamela or another reviewed provider through an ingestion adapter

Classical Tafsir:
- Tafsir Ibn Kathir
- Jami' al-Bayan (Al-Tabari)
- Al-Jami' li-Ahkam al-Quran (Al-Qurtubi)
- Al-Tahrir wa al-Tanwir (Ibn Ashur)
- Taysir al-Karim al-Rahman (Al-Sa'di)
- Al-Tafsir al-Munir (Wahbah Al-Zuhayli)

Additional Sources:
- Sahih al-Bukhari
- Sahih Muslim
- Other recognized Hadith collections
- Relevant scholarly references

These are source categories to review, not data currently guaranteed to be
available in the platform. Verify the exact collection, edition, grading
provenance, and usage rights before enabling Hadith-based claims.

## Data Ingestion Pipeline

Source Registry
    |
    v
Resource Selection and Rights Review
    |
    v
Versioned JSON / SQLite Download
    |
    v
Arabic Content Extraction
    |
    v
HTML / Text Normalization
    |
    v
Page and Chapter Segmentation
    |
    v
Ayah Reference Mapping
    |
    v
Metadata Enrichment
    |
    v
Quality Validation
    |
    v
Knowledge Database
    |
    v
Optional Vector Index (candidate discovery only)

### Provider adapters

Use QUL downloads as the first provider adapter. Add Shamela or other providers
only when access and intended use are confirmed. Never assume that a book is
available or licensed for unrestricted storage, quotation, indexing, or AI
processing.

Maintain:
- Book ID
- Book Title
- Author
- Author Death Year (Hijri)
- Edition
- Publisher
- Volume
- Page
- Chapter
- Original Arabic Text
- Source URL
- Copyright / Usage Permission
- Data Version

---

# 8. RAG ARCHITECTURE

Use Retrieval-Augmented Generation.

The system must retrieve relevant passages before generating Tafsir explanations.

### Retrieval Strategy

Hybrid Search:

1. Exact Ayah Reference Search
2. Arabic Full-Text Search
3. Semantic Vector Search
4. Author and Book Filtering
5. Chapter and Volume Filtering

Recommended:
- PostgreSQL
- pgvector
- PostgreSQL Full-Text Search

Optional future:
- Qdrant for dedicated vector infrastructure.

### Citation Structure

Every retrieved passage should contain:

{
  "source_id": "tafsir_001",
  "book": "Tafsir Ibn Kathir",
  "author": "Ibn Kathir",
  "author_ar": "ابن كثير",
  "surah": 36,
  "ayah": 13,
  "volume": null,
  "page": null,
  "original_text": "...",
  "edition": null,
  "source_url": null
}

Never fabricate volume or page numbers.

If unavailable, display "Reference location unavailable".

---

# 9. FRONTEND FEATURES

## Quran Reader

- Surah list
- Ayah navigation
- Arabic Uthmani
- Thai translation
- English translation
- Word-by-word
- Audio recitation
- Ayah highlighting
- Responsive reading interface
- Dark mode
- Font size controls

## Tafsir Chat

- Automatic Ayah context
- Multi-agent responses
- Agent selection
- Ask follow-up questions
- Compare interpretations
- Arabic source quotations
- Expandable citations
- Chat history
- Copy and bookmark responses

## Research Mode

- Compare multiple Tafsir books
- Search Arabic source texts
- Compare scholarly opinions
- View relevant Hadith
- Explore related Quranic verses
- Display source differences

## Reading Progress

- Last-read Ayah
- Bookmarks
- Reading history
- Personal notes
- Study sessions
- Learning goals

---

# 10. SYSTEM ARCHITECTURE

Recommended Production Stack:

Frontend:
- Next.js 14+ App Router
- TypeScript
- Tailwind CSS
- shadcn/ui
- Zustand

Backend:
- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy

AI:
- LLM Provider Adapter
- Multi-Agent Orchestrator
- RAG Retrieval Engine
- Embedding Provider
- Source Validation Engine

Database:
- PostgreSQL
- pgvector
- Redis

Data Ingestion:
- QUL JSON / SQLite import
- Optional provider-specific ingestion adapters
- Quran Foundation API adapter only for an approved runtime use case

Communication:
- REST API
- Server-Sent Events (SSE)

Deployment:
- Containerized Services
- Nginx / Reverse Proxy
- TLS
- Prometheus
- Grafana
- Automated Backups

Architecture principle:

Start with a modular monolith.

Do not introduce unnecessary microservices before actual scaling requirements justify them.

---

# 11. MONOREPO STRUCTURE

quran-ai/
│
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── quran-reader/
│   │   │   ├── tafsir-chat/
│   │   │   ├── agent-comparison/
│   │   │   └── bookmarks/
│   │   └── lib/
│   │
│   └── admin/
│       ├── sources/
│       ├── books/
│       ├── agents/
│       └── verification/
│
├── services/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── models/
│   │   │   ├── schemas/
│   │   │   ├── services/
│   │   │   └── repositories/
│   │
│   ├── ai-engine/
│   │   ├── orchestrator/
│   │   ├── agents/
│   │   ├── retrieval/
│   │   ├── citations/
│   │   └── validators/
│   │
│   └── ingestion/
│       ├── quran-api/
│       ├── shamela/
│       ├── hadith/
│       └── processors/
│
├── packages/
│   ├── shared-types/
│   ├── ui/
│   └── config/
│
├── database/
│   ├── migrations/
│   ├── schemas/
│   └── seeds/
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   ├── AGENT_GOVERNANCE.md
│   ├── API_CONTRACTS.md
│   └── SECURITY.md
│
├── infra/
│   ├── containers/
│   ├── monitoring/
│   └── backup/
│
├── scripts/
│
├── .env.example
├── AGENTS.md
└── README.md

---

# 12. DATABASE DESIGN

PostgreSQL Tables:

Quran:
- surahs
- ayahs
- translations
- recitations
- word_translations

Knowledge:
- scholars
- tafsir_books
- tafsir_editions
- tafsir_passages
- source_references
- hadith_sources
- hadith_reports

AI:
- agents
- agent_configs
- agent_runs
- retrieval_results
- citations
- verification_results

User:
- users
- bookmarks
- reading_progress
- study_notes
- chat_sessions
- chat_messages

Governance:
- source_permissions
- content_reviews
- audit_logs

All religious source records must be traceable to their original source.

---

# 13. API CONTRACTS

Quran:
GET /api/v1/surahs
GET /api/v1/surahs/{surah_id}
GET /api/v1/ayahs/{surah_id}/{ayah_id}
GET /api/v1/ayahs/{surah_id}/{ayah_id}/translations

Tafsir:
GET /api/v1/tafsir/{surah_id}/{ayah_id}
GET /api/v1/tafsir/books
GET /api/v1/tafsir/scholars
GET /api/v1/tafsir/compare/{surah_id}/{ayah_id}

Agents:
GET /api/v1/agents
POST /api/v1/agents/{agent_id}/explain
POST /api/v1/agents/compare

Chat:
POST /api/v1/chat/sessions
POST /api/v1/chat/messages
GET /api/v1/chat/sessions/{session_id}

Research:
POST /api/v1/research/search
GET /api/v1/research/sources/{source_id}

All API responses must use validated schemas.

---

# 14. SECURITY & ISLAMIC CONTENT INTEGRITY

- API secrets remain server-side.
- Rate limiting.
- Input validation.
- Prompt injection protection.
- Retrieval source validation.
- Citation validation.
- User authentication.
- Access control.
- Audit logging.
- Source version tracking.
- Copyright and licensing checks.

### Religious Accuracy Rules

1. Never fabricate Quranic verses.
2. Never invent Hadith references.
3. Never invent quotations from scholars.
4. Never confuse AI analysis with scholarly quotations.
5. Never hide recognized differences of opinion.
6. Never classify Hadith as Sahih or Da'if without supporting grading references.
7. Distinguish Tafsir from personal reflection.
8. Abstain when reliable evidence is unavailable.
9. Preserve the original Arabic text.
10. Require human scholarly review for high-risk religious conclusions.

---

# 15. ISLAMIC KNOWLEDGE DESIGN SYSTEM

Brand:
QURAN AI

Identity:
- Scholarly
- Peaceful
- Trustworthy
- Minimal
- Traditional Knowledge + Modern Technology

Color Palette:

Primary: #0E5E4F
Accent: #C9A227
Surface: #F5F7F6
Dark: #0F172A
Text: #1E293B
Success: #15803D
Warning: #B45309
Danger: #B91C1C

Typography:

Arabic:
- Noto Naskh Arabic
- Amiri

UI:
- Inter

Thai:
- Noto Sans Thai

Components:

- QuranAyahCard
- SurahNavigation
- ArabicTextDisplay
- TranslationPanel
- TafsirAgentCard
- TafsirComparison
- CitationReference
- ScholarlyDifference
- HadithReference
- TafsirChatPanel
- SourceViewer

---

# 16. DEVELOPMENT ROADMAP

PHASE 0 — Research & Foundation

- Verify Quran API access.
- Verify Thai translation availability.
- Audit QUL resources and select the initial Quran, translation, and tafsir datasets.
- Verify per-resource rights, metadata, edition, and ayah mapping before import.
- Verify book availability and usage rights.
- Select initial Tafsir editions.
- Define source attribution schema.
- Finalize architecture.

PHASE 1 — Quran Reader MVP

- Quran API integration.
- Surah navigation.
- Ayah selection.
- Arabic text.
- Translation.
- Audio playback.
- Reading progress.

PHASE 2 — Tafsir Knowledge Base

- Book ingestion.
- Arabic text processing.
- Ayah mapping.
- PostgreSQL storage.
- Full-text search.
- Vector indexing.
- Citation metadata.

PHASE 3 — Tafsir Agents

- Ibn Kathir Agent.
- Al-Tabari Agent.
- Al-Qurtubi Agent.
- Ibn Ashur Agent.
- Al-Sa'di Agent.
- Al-Zuhayli Agent.

PHASE 4 — Multi-Agent Intelligence

- Agent orchestration.
- Independent Tafsir responses.
- Scholarly comparison.
- Citation validation.
- Evidence classification.
- Realtime chat.

PHASE 5 — Research Platform

- Advanced Arabic search.
- Hadith cross-referencing.
- Scholarly differences.
- Research workspace.
- Personal study notes.

PHASE 6 — Production Release

- Security audit.
- Performance optimization.
- Backup and recovery.
- Monitoring.
- Scholarly review.
- Production deployment.

---

# 17. SUCCESS METRICS

Product:
- Quran reading completion.
- Daily active readers.
- Ayah engagement.
- Study session duration.

AI:
- Citation coverage.
- Source retrieval accuracy.
- Unsupported claim rate.
- Agent response consistency.
- Scholarly review acceptance.

Infrastructure:
- API availability.
- Response latency.
- Retrieval latency.
- Error rate.
- Infrastructure cost.

Quality Gates:

- Every generated religious explanation must identify its supporting sources.
- No fabricated source citations.
- No Quran text corruption.
- No unapproved changes to canonical Quran text.
- Unverified claims must be labeled.
- High-risk answers must be eligible for human review.

---

# 18. MVP DEFINITION

The first release should focus on:

1. Quran Reader.
2. Ayah Selection.
3. Thai Translation (subject to verified availability).
4. Ibn Kathir Tafsir.
5. Al-Tabari Tafsir.
6. Al-Sa'di Tafsir.
7. Tafsir Chat.
8. Source Citations.

Do not attempt to ingest every Islamic book or implement all six Agents immediately.

Prove that the system can retrieve, explain and cite one Ayah correctly before scaling to all 114 Surahs.

---

# 19. FINAL PRODUCT PRINCIPLE

QURAN AI is not an AI that claims to interpret religion independently.

It is an intelligent platform that helps people study the Quran through authentic scholarly literature.

The Quran is the primary source.

The Sunnah provides essential explanation and guidance.

Classical Tafsir provides scholarly understanding.

AI organizes, retrieves, compares and explains the available evidence.

Human scholars remain essential for verification and religious judgment.

END OF PRD

---

# 4. ข้อเสนอแนะด้าน UX: หน้าจอที่ผมอยากให้โปรเจกต์นี้มี

ผมแนะนำให้ใช้หน้าจอแบบ 3 คอลัมน์ โดยมีช่องแชตอยู่ด้านขวาเหมือนที่คุณต้องการ



ตัวอย่างการทำงาน:

| ตำแหน่ง | เนื้อหา |
|---|---|
| ซ้าย | รายชื่อซูเราะฮ์และการนำทาง |
| กลาง | อัลกุรอานภาษาอาหรับและคำแปล |
| ขวา | AI Tafsir Chat และ Agents |

เมื่อคลิกอายะฮ์ เช่น 36:14 ระบบจะส่ง Context ไปยัง Agent ทั้งหมดโดยอัตโนมัติ

ในช่องแชตจะมีแท็บ:

- Overview — ภาพรวมความหมาย
- Ibn Kathir — ตัฟซีรอิบนุกะษีร
- Al-Tabari — ตัฟซีรอัฏเฏาะบะรี
- Al-Qurtubi — ฟิกฮ์
- Ibn Ashur — ภาษาและบริบท
- Al-Sa'di — คำอธิบายเข้าใจง่าย
- Al-Zuhayli — ฟิกฮ์และสังคมร่วมสมัย
- Compare — เปรียบเทียบทั้งหมด

---

# 5. สิ่งที่ผมอยากให้ระวังเป็นพิเศษ

มี 3 เรื่องที่สำคัญมากสำหรับโปรเจกต์นี้

**1. อย่าให้ AI สวมบทเป็นอุละมาอ์**

ควรเรียกว่า `Ibn Kathir Tafsir Agent` ไม่ใช่ `Imam Ibn Kathir AI`

เพราะ Agent เป็นระบบที่ใช้ตำราของท่านเป็นฐานข้อมูล ไม่ใช่ตัวท่านเอง

**2. ต้องแยกความถูกต้องของรายงานออกจากความถูกต้องของการอ้างอิง**

ตัวอย่างเช่น ตำราอิบนุกะษีรอาจรวบรวมเรื่องราวจากรายงานหลายประเภท

AI ต้องสามารถบอกได้ว่า:
- มีข้อความนี้อยู่ในตำราอิบนุกะษีร
- แต่ยังไม่ได้ตรวจสอบสายรายงาน
- จึงไม่สามารถยืนยันว่ารายงานนั้นเศาะฮีห์ได้

**3. ต้องมี Original Source Viewer**

เมื่อ AI อธิบายอายะฮ์ ผู้ใช้ควรสามารถกดดูข้อความภาษาอาหรับต้นฉบับจากหนังสือได้ทันที พร้อมเลขเล่มและหน้าเมื่อมีข้อมูล

นี่จะเป็นจุดเด่นที่ทำให้ QURAN AI แตกต่างจาก ChatGPT ทั่วไป

---

# 6. คำแนะนำก่อนเริ่ม Vibe Coding

ผมแนะนำให้เริ่มจาก 3 เรื่องตามลำดับ

| ลำดับ | งาน | ผลลัพธ์ |
|---|---|---|
| 1 | PRD + Architecture | กำหนดระบบทั้งหมด |
| 2 | Data Source Audit | ตรวจสอบ API, ตำรา และสิทธิ์การใช้งาน |
| 3 | MVP Implementation Plan | วางแผนการพัฒนาโดยไม่สร้างระบบซ้ำซ้อน |

**ข้อเสนอเชิงสถาปัตยกรรม:** ใช้ Next.js + FastAPI + PostgreSQL เป็นแกนหลัก
เริ่ม ingestion ด้วย QUL JSON/SQLite และใช้ pgvector เมื่อจำเป็นสำหรับ candidate
discovery; retrieval ที่นำไปอ้างอิงต้องยืนยันกับข้อความต้นฉบับเสมอ เพิ่ม
provider adapter สำหรับ Quran Foundation API หรือ Shamela เฉพาะเมื่อยืนยัน
access และสิทธิ์ใช้งานแล้ว ส่วน Redis ค่อยเพิ่มเมื่อจำเป็นต้องมีงานเบื้องหลัง
หรือคิวประมวลผล

ไม่จำเป็นต้องเริ่มด้วย Kubernetes หรือ Microservices เพราะจะเพิ่มความซับซ้อนโดยที่ยังไม่มีความจำเป็น

### 7. ผมอยากเสนอฟีเจอร์สำคัญเพิ่มเติมอีกหนึ่งอย่าง

**Scholarly Disagreement Engine (ระบบตรวจสอบความเห็นต่างของอุละมาอ์)**

ตัวอย่าง:

เมื่ออ่านอายะฮ์หนึ่ง ระบบพบว่าอัฏเฏาะบะรี อิบนุกะษีร และอัลกุรฏุบีมีคำอธิบายบางประเด็นแตกต่างกัน

แทนที่จะให้ AI เลือกคำตอบเพียงหนึ่งเดียว ระบบจะนำเสนอ:

| นักวิชาการ | ทัศนะ | หลักฐาน | สถานะ |
|---|---|---|---|
| อัฏเฏาะบะรี | ทัศนะ A | รายงานที่อ้างอิง | ตรวจสอบรายงาน |
| อิบนุกะษีร | ทัศนะ B | รายงานและหลักฐาน | ตรวจสอบรายงาน |
| อัลกุรฏุบี | ทัศนะ C | หลักฐานและการวิเคราะห์ | ตรวจสอบรายงาน |

พร้อมอธิบายว่าความเห็นต่างเกิดจากอะไร โดยไม่สร้างความขัดแย้งที่ไม่มีอยู่จริง

ผมคิดว่าฟีเจอร์นี้จะเป็นหนึ่งในคุณค่าทางวิชาการที่สำคัญที่สุดของแพลตฟอร์ม

**คำถามสำคัญสำหรับกำหนดทิศทางการพัฒนา:** ผมแนะนำให้ QURAN AI เริ่มต้นเป็นแพลตฟอร์มภาษาไทยก่อน โดยรองรับภาษาอาหรับต้นฉบับและภาษาอังกฤษเป็นภาษาประกอบ แล้วจึงเพิ่มภาษาอื่นในระยะต่อไป คุณต้องการให้ภาษาไทยเป็นภาษาหลักของทั้ง Quran Reader และ Tafsir Chat หรือไม่?