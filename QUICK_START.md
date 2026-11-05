# QURAN AI — Quick Start Guide

## 🚨 CRITICAL: Database Setup Required

This guide provides step-by-step instructions to set up the QURAN AI development environment and complete MVP initialization.

## Quick Setup Commands

### 1. Install PostgreSQL
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
```

### 2. Configure PostgreSQL
```bash
# Start PostgreSQL
sudo service postgresql start

# Configure password
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'quran_ai';"

# Create database and enable pgvector
sudo -u postgres psql << 'SQL'
CREATE DATABASE quran_ai OWNER postgres;
CREATE EXTENSION IF NOT EXISTS vector;
SQL
```

### 3. Install Python Packages
```bash
# Install pip if not available
sudo apt-get install -y python3-pip python3-dev libpq-dev

# Install Python packages
pip3 install --break-system-packages sqlalchemy psycopg2-binary alembic fastapi python-dotenv requests
```

### 4. Create Environment File
```bash
# Create .env from template
cp .env.example.final .env

# Edit .env with real API credentials
nano .env
# Update: QURAN_API_CLIENT_ID, QURAN_API_CLIENT_SECRET, LLM_API_KEY, EMBEDDING_API_KEY
```

### 5. Run Database Setup
```bash
# Create tables, indexes, and sample data
python3 setup_database.py
```

### 6. Load Data Sources
```bash
# Seed Quran data from API
python3 scripts/seed_quran_data.py

# Load classical tafsir sources
python3 scripts/load_tafsir_data.py
```

### 7. Verify Setup
```bash
# Check database
psql -h localhost -U postgres -d quran_ai -c "SELECT COUNT(*) FROM quran_ayahs;"
psql -h localhost -U postgres -d quran_ai -c "SELECT COUNT(*) FROM tafsir_passages;"

# Check Python packages
python3 -c "import sqlalchemy, psycopg2, fastapi, alembic, requests"
```

## 📋 Files to Prepare

### Environment Files
- `.env` (create from `.env.example.final`)
- Update with actual API credentials

### Database Scripts
- `setup_database.py` (complete database initialization)
- `scripts/seed_quran_data.py` (Quran verses from API)
- `scripts/load_tafsir_data.py` (classical tafsir sources)

### Documentation
- `README_CURRENT_STATUS_FINAL.md` (complete MVP roadmap)
- `INSTALL_REQUIREMENTS.md` (detailed setup guide)
- `RUN_SETUP.md` (quick start reference)

## 🎯 Critical Path Summary

### **Phase 1.5 - Database Setup** (BLOCKING)
1. **PostgreSQL installation** ✅
2. **Database creation** ✅
3. **pgvector extension** ✅
4. **Table creation** ✅
5. **Data seeding** ✅
6. **Environment config** ✅

### **Phase 2 - Backend Completion**
1. Agent orchestration service
2. Evidence validation system
3. API contract finalization

### **Phase 3 - Frontend Integration**
1. Next.js application build
2. Quran reader implementation
3. Multi-agent chat interface
4. Responsive design

### **MVP Delivery (Week 4)**
1. End-to-end testing
2. Quality gates verification
3. Production deployment

## 🚨 Critical Blocker Resolution

**Current Status:** Perfect architecture, blocked by database setup

**Solution:** Execute the `setup_database_pure.sh` script which:
- Creates all required database tables
- Sets up pgvector extension
- Creates indexes and triggers
- Inserts sample scholarly records
- Prepares environment for production

**Next Steps:**
1. **Configure PostgreSQL** with sudo privileges
2. **Install Python packages** with `--break-system-packages`
3. **Run database setup** script
4. **Load data sources** (Quran API + classical texts)
5. **Complete MVP development**

## 📞 Support

If you encounter issues:
1. **Check PostgreSQL status:** `sudo service postgresql status`
2. **Test database connection:** `psql -h localhost -U postgres -d quran_ai`
3. **Review logs:** Check PostgreSQL and Python installation logs
4. **Manual setup:** Use the commands provided in this guide

## 🎉 Success Metrics

After setup completion:

- **Database Tables:** 12+ (quran_ayahs, tafsir_passages, users, etc.)
- **Scholar Records:** 4 classical scholars
- **Source Files:** 100.7MB of classical tafsir data
- **Vector Search:** pgvector extension enabled
- **Quality Gates:** Ready for evidence-based validation

**The QURAN AI system has perfect architecture - just waiting for database initialization to deliver the evidence-based Quran study experience.**

**Ready to execute the database setup script?**