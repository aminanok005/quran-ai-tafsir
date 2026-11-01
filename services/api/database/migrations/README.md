# Database Migrations

This directory contains Alembic migration scripts for the QURAN AI API service.

## Overview

All migrations are written as SQL files for clarity and version control. Each migration:
- Creates new tables, indexes, or constraints
- Is backward compatible (safe to run)
- Includes rollback statements where possible
- Uses the `id` column pattern with `uuid-ossp` extension

## Migration Process

1. **Initial Setup**
   - Run `alembic init migrations` to create Alembic environment
   - Copy SQL migrations from `../../database/migrations/` to this directory
   - Review and adjust as needed

2. **Running Migrations**
   ```bash
   alembic upgrade head
   ```

3. **Creating New Migrations**
   ```bash
   alembic revision --autogenerate -m "description"
   ```

## Current Migration Status

Based on the main database migration structure:
- `001_initial_quran_schema.sql` - Quran verses and basic data
- `002_tafsir_knowledge_base.sql` - Tafsir books and scholarly content

These migrations are imported into the API service but may need adjustment for specific requirements.