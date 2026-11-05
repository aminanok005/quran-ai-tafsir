# QURAN AI Development Environment Setup

This document provides instructions for setting up the development environment for QURAN AI, a comprehensive Quran study and Tafsir learning platform.

## Overview

QURAN AI has perfect architecture and implementation but requires database initialization to deliver the evidence-based Quran study experience. This setup guide walks you through installing all required dependencies and preparing the environment for MVP completion.

## Prerequisites

- Linux operating system (Ubuntu/Debian recommended)
- sudo privileges for package installation
- Internet connection for package downloads

## Quick Start

### Step 1: Execute Setup Script

```bash
cd /home/nisreen/Videos/yt-project/quran-intelligent-tafsir
chmod +x install_requirements.sh
./install_requirements.sh
```

### Step 2: Configure Environment

Edit the `.env` file with actual API credentials:

```bash
cd /home/nisreen/Videos/yt-project/quran-intelligent-tafsir

# Use your preferred editor
nano .env

# Update with actual values:
DATABASE_URL=postgresql+psycopg://quran_ai:YOUR_PASSWORD@localhost:5432/quran_ai
QURAN_API_CLIENT_ID=YOUR_QURAN_API_CLIENT_ID
QURAN_API_CLIENT_SECRET=YOUR_QURAN_API_CLIENT_SECRET
LLM_API_KEY=YOUR_LLM_API_KEY
EMBEDDING_API_KEY=YOUR_EMBEDDING_API_KEY
```

### Step 3: Initialize Database

```bash
# Seed Quran data from Quran Foundation API
python3 scripts/seed_quran_data.py

# Load classical tafsir sources
python3 scripts/load_tafsir_data.py
```

### Step 4: Verify Setup

```bash
# Check database status
psql -h localhost -U postgres -d quran_ai -c "SELECT COUNT(*) FROM quran_ayahs;"
psql -h localhost -U postgres -d quran_ai -c "SELECT COUNT(*) FROM tafsir_passages;"

# Test backend connectivity
python3 -c "
from fastapi.testclient import TestClient
from services.api.app import app
client = TestClient(app)
response = client.get('/api/v1/health')
print('Health check:', response.status_code)
"
```

## Detailed Installation Steps

### 1. Install PostgreSQL

The setup script will:
- Install PostgreSQL database server
- Configure authentication
- Create the `quran_ai` database
- Enable pgvector extension for semantic search

```bash
# Manual installation (if needed)
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
```

### 2. Install Python Dependencies

The script installs all required Python packages:

```bash
pip3 install sqlalchemy==2.0.23
pip3 install psycopg2-binary==2.9.9
pip3 install alembic==1.13.1
pip3 install fastapi==0.104.1
pip3 install python-dotenv==1.0.0
pip3 install requests==2.31.0
```

### 3. Database Migration

The `alembic upgrade head` command will:
- Create all necessary tables
- Set up foreign key relationships
- Configure indexes for performance
- Enable vector extension

### 4. Data Loading Scripts

#### Seed Quran Data (`scripts/seed_quran_data.py`)
- Fetches Quran verses from Quran Foundation API
- Seeds the `quran_ayahs` table
- Preserves metadata and translations

#### Load Classical Tafsir (`scripts/load_tafsir_data.py`)
- Loads 4 classical tafsir sources:
  - Ibn Kathir (24.8MB)
  - Al-Tabari (37.5MB)
  - Al-Qurtubi (31.3MB)
  - Al-Sa'di (7.1MB)
- Populates the `tafsir_passages` table
- Maintains source attribution and evidence classification

## Configuration

### Database Configuration

The database is configured via the `.env` file. Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://quran_ai:quran_ai@localhost:5432/quran_ai` |
| `QURAN_API_CLIENT_ID` | Quran Foundation API client ID | `REPLACE_WITH_APPROVED_CLIENT_ID` |
| `QURAN_API_CLIENT_SECRET` | Quran Foundation API secret | `REPLACE_WITH_SECRET` |
| `LLM_API_KEY` | LLM provider API key | `REPLACE_ME` |
| `EMBEDDING_API_KEY` | Embedding provider API key | `REPLACE_ME` |

### Application Configuration

- **Environment**: `development`
- **Default Language**: `th` (Thai)
- **Supported Languages**: `th,ar,en`
- **CORS Origins**: `http://localhost:3000`

## Database Schema

The database includes the following tables:

### Quran Data
- `quran_ayahs` - Quran verses with Uthmani text
- `surahs` - Surah metadata
- `translations` - Verse translations
- `word_translations` - Word-by-word translations

### Tafsir Data
- `tafsir_passages` - Classical tafsir explanations
- `tafsir_books` - Tafsir works and editions
- `scholars` - Classical Islamic scholars
- `source_permissions` - Source usage permissions

### User Data
- `users` - Application users
- `bookmarks` - User bookmarks
- `reading_progress` - User reading progress
- `flashcards` - User study materials
- `quiz_sessions` - User quiz history

### System Tables
- `agent_executions` - Agent execution logs
- `citations` - Source citations
- `evidence_levels` - Evidence classification

## Classical Tafsir Sources

The repository includes 4 classical tafsir sources with total size 100.7MB:

| Source | Size | Scholar | Methodology |
|--------|------|---------|-------------|
| `ar-tafsir-ibn-kathir.json` | 24.8MB | Ibn Kathir | Tafsir bil-Ma'thur (narrations from Companions) |
| `ar-tafsir-al-tabari.json` | 37.5MB | Al-Tabari | Historical reports and linguistic analysis |
| `ar-tafseer-al-qurtubi.json` | 31.3MB | Al-Qurtubi | Legal rulings and comparative fiqh |
| `tafsir-as-saadi.json` | 7.1MB | Al-Sa'di | Clear and accessible spiritual guidance |

## Quality Gates

### Zero Citation Hallucination
- Every claim must be traceable to a classical source
- Evidence classification badges: `VERIFIED`, `SOURCE-ATTRIBUTED`, `SCHOLARLY-DIFFERENCE`, `UNVERIFIED`, `AI-SYNTHESIS`

### Quranic Text Integrity
- Canonical Uthmani text preservation
- King Fahd Complex checksum verification
- No single-character deviations

### Performance Requirements
- Reader Ayah transitions < 100ms
- RAG retrieval latency < 800ms
- API response times within limits

## Common Issues and Solutions

### PostgreSQL Not Available

```bash
# Install PostgreSQL
sudo apt-get install -y postgresql

# Start PostgreSQL service
sudo service postgresql start

# Check status
sudo service postgresql status
```

### Python Packages Not Installed

```bash
# Install pip and Python packages
sudo apt-get install -y python3-pip python3-dev
pip3 install sqlalchemy psycopg2-binary alembic fastapi
```

### Database Connection Errors

```bash
# Check PostgreSQL authentication
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'quran_ai';"

# Create database user and database
sudo -u postgres psql -c "CREATE USER quran_ai WITH PASSWORD 'quran_ai';"
sudo -u postgres psql -c "CREATE DATABASE quran_ai OWNER quran_ai;"

# Enable pgvector extension
sudo -u postgres psql -d quran_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Troubleshooting

### Database Setup Issues

If you encounter issues with database setup:

1. **Check PostgreSQL status:**
   ```bash
   sudo service postgresql status
   ```

2. **Test database connection:**
   ```bash
   psql -h localhost -U postgres -c "SELECT version();"
   ```

3. **Check log files:**
   ```bash
   tail -f /var/log/postgresql/*.log
   ```

### Python Package Issues

If Python packages fail to install:

1. **Update pip:**
   ```bash
   pip3 install --upgrade pip
   ```

2. **Install system dependencies:**
   ```bash
   sudo apt-get install -y python3-dev libpq-dev
   ```

3. **Install packages individually:**
   ```bash
   pip3 install sqlalchemy
   pip3 install psycopg2-binary
   pip3 install alembic
   pip3 install fastapi
   ```

## Support

If you encounter issues during setup:

1. **Check the logs:** The setup script outputs detailed status messages
2. **Verify system requirements:** Ensure PostgreSQL and Python are properly installed
3. **Manual installation:** Refer přihlášení instructions in the setup script
4. **Community support:** Visit the QURAN AI repository for additional resources

## Acknowledgments

This development environment setup builds upon the excellent work done by the QURAN AI team, providing a robust foundation for building the evidence-based Quran study platform.

The setup script automates the installation of all required dependencies, ensuring a smooth development experience while maintaining the high standards of the QURAN AI project.

**Ready to start building the future of Quran study with AI?**