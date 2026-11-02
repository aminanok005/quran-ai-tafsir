# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## QURAN AI: INTELLIGENT QURAN STUDY & TAFSIR LEARNING SUPER WEBAPP
**Version**: 2.0 (Integrated Super Platform)  
**Status**: Ready for Implementation / Vibe Coding  
**Target Repositories**: Upgraded from `aminanok005/quran-ai-tafsir`

---

## 1. EXECUTIVE SUMMARY & PRODUCT VISION

### 1.1 The Vision
**QURAN AI** is an intelligent, evidence-grounded Quranic study and learning platform. It unites classical Islamic scholarship with state-of-the-art AI engineering.

By fusing four complementary systems into a unified **Super WebApp**:
1. **Quran Reader & Classical Multi-Agent Tafsir Engine** (from `quran-ai-tafsir` & Islamic Knowledge Framework): Verse-by-verse reading backed by 6 classical Tafsir Agents and a Scholarly Disagreement Engine.
2. **Gamified SaaS Learning & Curriculum Engine** (from `SkillPet Next.js + Strapi`): Structured bite-sized courses, interactive slide exercises, daily streaks, gem rewards, hearts for hints, and automated content authoring via Strapi MCP.
3. **AI Study Assistant & Active Recall System** (from `Full-Stack MERN Assistant`): Automated 3D flip flashcards, configurable AI quizzes with detailed analytical scorecards, 1-click summarization, and root-word concept explainers.
4. **Document Research Workspace**: Embedded PDF reader with AI chat for studying contemporary Islamic research papers, fatwas, and academic journals.

### 1.2 Core Philosophy & Product Promise
- **Quran & Authentic Sunnah First**: AI never innovates religious rulings or creates unsupported interpretations.
- **Traceable Attribution**: Every explanation must link to its authentic source text (Book, Volume, Page, Scholar).
- **Scholarly Differences Respected**: Presenting diverse classical views (*Ikhtilaf*) objectively rather than forcing artificial uniformity.
- **Active Engagement**: Transforming passive reading into retained knowledge through gamified active-recall learning.

---

## 2. USER PERSONAS

1. **The Daily Devotional Reader (Nadia, 28)**:
   - Reads daily Quran portions. Wants audio recitation, clear Thai translations, and daily streaks to stay consistent.
2. **The Islamic Studies Student (Zayd, 22)**:
   - Studies Quranic Arabic and Tafsir. Uses flashcards for vocabulary, takes quizzes after each Surah, and compares Ibn Kathir with Al-Tabari.
3. **The Academic Researcher & Khatib (Dr. Faruq, 45)**:
   - Researches specific legal verses (*Ahkam*), cross-references Al-Qurtubi with modern scholars (Wahbah Al-Zuhayli), and inspects original Arabic sources.

---

## 3. CORE FUNCTIONAL SPECIFICATIONS

### MODULE 1: The Intelligent Quran Reader
- **Quran.Foundation API Integration**:
  - Full 114 Surahs with Uthmani script, Ayah-by-Ayah indexing, Juz, Hizb, and Rub divisions.
  - Authentic Thai translation (King Fahd Complex / Thai Islamic Council certified) & Sahih International English translation.
  - Word-by-Word morphology, transliteration, and root-word breakdown.
  - Continuous and verse-by-verse audio playback from world-renowned reciters (e.g., Mishary Rashid, Al-Husary).
- **Interactive Verse Selection**: Clicking any Ayah automatically locks context and broadcasts it to the Tafsir Chat and Study Assistant.

### MODULE 2: Classical Multi-Agent Tafsir Engine
- **Six Specialized Scholarly Agents**:
  1. *Ibn Kathir Agent*: Focuses on Tafsir bil-Ma'thur, Hadith references, and reports from the Companions.
  2. *Al-Tabari Agent*: Explores early Salaf narrations, linguistic nuances, and historical reports.
  3. *Al-Qurtubi Agent*: Focuses on legal deductions (*Ahkam*), comparative Madhhab jurisprudence, and practical rulings.
  4. *Ibn Ashur Agent*: Delivers rhetorical analysis (*Balaghah*), structural coherence, and higher objectives (*Maqasid*).
  5. *Al-Sa'di Agent*: Clear, simplified, devotional explanations for general readers.
  6. *Wahbah Al-Zuhayli Agent*: Modern comparative fiqh and contemporary societal applications.
- **Scholarly Disagreement Engine (*Ikhtilaf Matrix*)**:
  - Compares interpretations across scholars side-by-side in a comparative matrix.
  - Highlights common consensus vs. divergent linguistic or legal deductions with evidence badges.
- **Original Source Viewer**: 1-click modal showing the original Arabic passage from Maktabah Shamela with volume, page, and book edition.

### MODULE 3: Gamified Quran Learning Tracks (SkillPet Engine)
- **Structured Curricula**:
  - Courses organized by themes (e.g. *Tafsir Juz Amma*, *Stories of the Prophets*, *The Miracles of Surah Al-Kahf*).
  - Micro-chapters (5-10 minutes each) with progress bars.
- **Dynamic Content Blocks**:
  - `theory`: Context, verse translation, and core Tafsir commentary.
  - `mcq`: 4-option multiple-choice questions with instant rationale feedback.
  - `fill_in_the_blanks`: Interactive drag-and-drop or dropdown vocabulary completion.
  - `matching_block`: Connecting Arabic vocabulary to authentic meanings or connecting verses to their causes of revelation (*Asbab al-Nuzul*).
- **Gamification Mechanics**:
  - **Daily Zap Streak**: Logs daily learning consistency.
  - **Gems System**: Earned by completing chapters and exercises.
  - **Hearts / Lives**: Spent when requesting deep AI hints; regenerates over time or via completed review sessions.
  - **Leaderboard**: Top daily/weekly learners across the community.

### MODULE 4: AI Study Assistant & Active Recall (MERN Assistant Engine)
- **Auto-Generated Flashcards**:
  - Automatically synthesizes flashcard sets from any selected Surah or Tafsir passage.
  - 3D flip card animation with Arabic on the front and Thai/English translation, root word, and context on the back.
  - Favorites & Bookmark system for spaced repetition.
- **Custom AI Quiz Generator**:
  - Configurable quiz generation (5, 10, or 20 questions) by difficulty (Beginner, Intermediate, Advanced Scholar).
  - Comprehensive score breakdown, analytics, review of incorrect answers, and direct links back to the source Ayah.
- **1-Click Surah & Ayah Summarizer**:
  - Synthesizes central themes, historical context (*Makki/Madani*), and main lessons.
- **Quranic Arabic Concept Explainer**:
  - Deep-dive explainer for complex Quranic terminology (e.g., *Taqwa*, *Ihsan*, *Riba*, *Hikmah*).

### MODULE 5: Document Study & Research Workspace
- **PDF Upload & Storage**: Secure file management via Cloudinary / Local Object Storage.
- **Embedded PDF Viewer**: Dual-pane document viewer enabling users to highlight passages and converse with the document using AI RAG.

### MODULE 6: Monetization, Auth & SaaS Management
- **Authentication**: JWT & OAuth2 (Google & Email/Password) with secure session storage.
- **Stripe Billing Integration**:
  - **Free Tier**: Complete Quran reader, Thai translation, basic Al-Sa'di Tafsir, 3 flashcard sets/day.
  - **Premium Scholar Plan ($5.99/mo or $49.99/yr)**: Unlimited Multi-Agent Tafsir, all 6 scholars, comparative matrix, unlimited flashcards, all gamified courses, and priority RAG responses.

---

## 4. TECHNICAL ARCHITECTURE SUMMARY

- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui, Zustand, Lucide React.
- **Backend API**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0.
- **CMS & Course Management**: Strapi v4/v5 Headless CMS with Strapi MCP Server for AI course authoring.
- **Database & Search**: PostgreSQL with `pgvector` for hybrid vector & full-text search, Redis for cache & rate limiting.
- **Media & Recitation**: Cloudinary for user assets; Quran.Foundation CDN for high-fidelity audio streams.
- **AI & RAG Pipeline**: LangChain / LlamaIndex + Gemini 1.5 Pro / Claude 3.5 Sonnet + Text-Embedding-3-Large.

---

## 5. DEVELOPMENT PHASES & MILESTONES

| Phase | Milestone | Scope |
|---|---|---|
| **Phase 1** | Foundation & Unified Reader | Next.js 3-column layout, Quran API, Arabic typography, Thai translation, Audio player. |
| **Phase 2** | Knowledge Base & Hybrid RAG | PostgreSQL + pgvector setup, Shamela ingestion pipeline, Tafsir citation schemas. |
| **Phase 3** | Multi-Agent Tafsir Engine | 6 Tafsir agents, prompt isolation, evidence classification badges, Disagreement matrix. |
| **Phase 4** | Gamified Learning SaaS | Strapi CMS + MCP setup, dynamic exercise blocks (Theory, MCQ, Blanks, Matching), Streaks & Gems. |
| **Phase 5** | AI Active Recall Suite | Auto flashcards with 3D flip, Quiz generator with scorecards, Document PDF viewer. |
| **Phase 6** | Billing, Security & Production | Stripe checkout, rate limiting, human scholar review workflows, Vercel & Cloud deployment. |

---

## 6. QUALITY GATES & SUCCESS METRICS

1. **Zero Citation Hallucination**: 100% of religious claims must link to verified classical database records.
2. **Quranic Text Integrity**: Canonical Uthmani text must match King Fahd Complex checksums without single-character deviations.
3. **Sub-second Reader Performance**: Quran reader Ayah transitions < 100ms; RAG retrieval latency < 800ms.
4. **Active Learning Retention**: > 65% quiz completion rate and sustained 7-day user streak engagement.\n