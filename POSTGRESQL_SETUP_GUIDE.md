# PostgreSQL Setup Guide for QURAN AI

## Current Status
- PostgreSQL 16.15 running on **port 5434** (not default 5432)
- Cluster: `16/main` online at `/var/lib/postgresql/16/main`
- Need to configure authentication and create `quran_ai` database

---

## Step-by-Step Setup Commands

### 1. Configure PostgreSQL Authentication
Edit the pg_hba.conf to allow password authentication:

```bash
# Find the config file
sudo find /etc/postgresql -name "pg_hba.conf"

# Edit the file (requires sudo)
sudo nano /etc/postgresql/16/main/pg_hba.conf

# Change the following lines from "peer" or "md5" to "trust" for local connections:
# TYPE  DATABASE        USER            ADDRESS                 METHOD
# local   all             postgres                                trust
# local   all             all                                     trust
# host    all             all             127.0.0.1/32            trust
# host    all             all             ::1/128                 trust
```

### 2. Restart PostgreSQL
```bash
sudo systemctl restart postgresql
```

### 3. Create Database and Configure
```bash
# Now you can connect without password
psql -h localhost -p 5434 -U postgres -c "CREATE DATABASE quran_ai OWNER postgres;"

# Enable pgvector extension
psql -h localhost -p 5434 -U postgres -d quran_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create tables and sample data
psql -h localhost -p 5434 -U postgres -d quran_ai << 'SQL'
-- All the SQL from MANUAL_DATABASE_SETUP.md goes here
SQL
```

---

## Alternative: Use Environment Variable for Password

```bash
export PGPASSWORD=quran_ai
psql -h localhost -p 5434 -U postgres -c "CREATE DATABASE quran_ai OWNER postgres;"
```

---

## After Database Setup

```bash
# Load classical tafsir sources
python3 scripts/load_tafsir_data.py

# Seed Quran data
python3 scripts/seed_quran_data.py

# Verify
psql -h localhost -p 5434 -U postgres -d quran_ai -c "SELECT COUNT(*) FROM quran_ayahs;"
```