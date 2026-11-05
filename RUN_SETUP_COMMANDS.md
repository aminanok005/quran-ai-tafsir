# QURAN AI Complete Setup Commands

## 🚀 Quick Start - Setup QURAN AI MVP

This document provides the complete sequence of commands to set up the QURAN AI Super WebApp development environment and complete MVP implementation.

---

## Phase 1.5 - Database Setup (CRITICAL PATH)

### Step 1: Execute Database Initialization

```bash
cd /home/nisreen/Videos/yt-project/quran-intelligent-tafsir
chmod +x setup_database_pure.sh
./setup_database_pure.sh
```

**What this script does:**
- Creates PostgreSQL database with pgvector extension
- Sets up all 12 required tables (quran_ayahs, scholars, tafsir_books, tafsir_passages, etc.)
- Configures indexes for vector and full-text search
- Inserts sample scholarly data (4 classical scholars)
- Creates admin user account

### Step 2: Configure Environment

```bash
# Create .env file from template
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql+psycopg://quran_ai:quran_ai@localhost:5432/quran_ai

# Quran Foundation API
QURAN_API_BASE_URL=https://apis.quran.foundation
QURAN_API_CLIENT_ID=REPLACE_WITH_APPROVED_CLIENT_ID
QURAN_API_CLIENT_SECRET=REPLACE_WITH_SECRET

# AI Provider Configuration
LLM_PROVIDER=OPENAI
LLM_API_KEY=REPLACE_ME
EMBEDDING_API_KEY=REPLACE_ME

# Security
SECRET_KEY=GENERATE_A_LONG_RANDOM_SECRET
CORS_ORIGINS=http://localhost:3000

# Application Settings
APP_ENV=development
APP_NAME=QURAN AI
APP_DEFAULT_LOCALE=th
APP_SUPPORTED_LOCALES=th,ar,en
EOF
```

### Step 3: Load Data Sources

```bash
# Load classical tafsir sources (100.7MB total)
python3 scripts/load_tafsir_data.py

# Seed Quran data from API
python3 scripts/seed_quran_data.py
```

### Step 4: Verify Setup
```bash
# Check database contents
psql -h localhost -U postgres -d quran_ai -c "SELECT COUNT(*) FROM quran_ayahs;"
psql -h localhost -U postgres -d quran_ai -c "SELECT COUNT(*) FROM tafsir_passages;"
psql -h localhost -U postgres -d quran_ai -c "SELECT scholar_id, name FROM scholars;"

# Test Python packages
python3 -c "import sqlalchemy; import psycopg2; import fastapi; print('✅ Python packages installed')"
```

---

## Phase 2 - Backend Development (AFTER DATABASE SETUP)

### Step 5: Backend API Endpoints
```bash
# The backend API is already implemented in services/api/
# Run tests if needed
python3 -m pytest services/api/tests/ -v

# Start development server (if needed)
cd services/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Phase 3 - Frontend Development (AFTER BACKEND)

### Step 6: Build Frontend Application
```bash
# Navigate to project root
cd /home/nisreen/Videos/yt-project/quran-intelligent-tafsir

# Install dependencies
bun install  # or npm install

# Build the application
bun run build:web

# Start development server
bun run dev:web
```

### Step 7: Verify Integration
```bash
# Check if both frontend and backend are running
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/api/v1/health
```

---

## 📋 Complete Command Summary

```bash
# Step 1-4: Setup
chmod +x setup_database_pure.sh
./setup_database_pure.sh
nano .env
# Edit .env with actual credentials

# Step 5: Data loading
python3 scripts/load_tafsir_data.py
python3 scripts/seed_quran_data.py

# Step 6-7: Development
# Backend testing and development
# Frontend development and testing
```

---

## 🚀 MVP Completion Status

### After All Steps Complete:

- ✅ **Database Schema** - All 12 tables created with relationships
- ✅ **Classical Sources** - 100.7MB of authentic tafsir data loaded
- ✅ **Quran Data** - 6,236 verses from API seeded
- ✅ **Evidence Classification** - Quality gates ready
- ✅ **Backend API** - All 6 agents functional
- ✅ **Frontend Application** - 3-column layout, Thai-first UI
- ✅ **Quality Gates** - Zero citation hallucination enforced
- ✅ **User Experience** - Gamified learning, active recall

### Quality Gates Verification:
1. **Zero Citation Hallucination** - 100% of claims traceable to sources
2. **Quranic Text Integrity** - Canonical Uthmani text preserved
3. **Performance** - Sub-second reader performance, <800ms RAG retrieval
4. **Active Learning** - >65% quiz completion, sustained streaks

---

## 📞 Support

If you encounter issues:

1. **Database Setup Issues:**
   ```bash
   # Check PostgreSQL status
   sudo service postgresql status
   

   # Test database connection
   psql -h localhost -U postgres -d quran_ai
   ```

2. **Python Package Issues:**
   ```bash
   # Install missing packages
   pip3 install --break-system-packages sqlalchemy psycopg2-binary
   ```

3. **Data Loading Issues:**
   ```bash
   # Check script logs
   tail -f scripts/load_tafsir_data.py.log
   ```

## 🎯 Success Metrics

After completing all setup steps:

- **Database Population:** 100.7MB + 6,236 Quran verses
- **Evidence Classification:** 5 badges (VERIFIED, SOURCE-ATTRIBUTED, etc.)
- **User Accounts:** Admin + registered users
- **API Endpoints:** All 10+ endpoints functional
- **Frontend Features:** Quran reader, tafsir chat, flashcards, quizzes
- **Quality Gates:** All 11 MVP requirements met

**The QURAN AI system is architecturally complete - this script completes the foundation needed for MVP delivery!**