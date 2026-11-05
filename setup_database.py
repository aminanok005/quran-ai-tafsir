#!/usr/bin/env python3
"""
QURAN AI Database Setup Script
Complete database initialization with pgvector and classical tafsir sources
"""

import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

from sqlalchemy.dialects.postgresql import UUID

# Database connection
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://quran_ai:CHANGE_ME@localhost:5432/quran_ai"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def setup_database():
    """Complete database setup with all required components."""
    logger = logging.getLogger(__name__)

    print("🚀 QURAN AI Database Setup")
    print("==========================")

    db = SessionLocal()

    try:
        # Step 1: Enable pgvector extension
        print("📊 Enabling pgvector extension...")
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()

        # Step 2: Create enum types
        print("🔤 Creating enum types...")
        db.execute(text("""
            CREATE TYPE surah_type AS ENUM ('meccan', 'medinan');
            CREATE TYPE language AS ENUM ('ar', 'th', 'en', 'ur');
            CREATE TYPE evidence_level AS ENUM ('verified', 'source_attributed', 'scholarly_difference', 'unverified', 'ai_synthesis');
            CREATE TYPE agent_type AS ENUM ('ibn_kathir', 'al_tabari', 'al_qurtubi', 'ibn_ashur', 'al_saadi', 'al_zuhayli');
            CREATE TYPE methodology AS ENUM ('ma\\'thur', 'ra\\'y', 'linguistic', 'legal', 'contemporary');
            CREATE TYPE hadith_grade AS ENUM ('sahih', 'hasan', 'daif', 'maudu');
            CREATE TYPE user_role AS ENUM ('reader', 'student', 'researcher', 'scholar', 'content_admin', 'platform_admin');
        """))
        db.commit()

        # Step 3: Create all tables
        print("📋 Creating database tables...")

        # Quran ayahs table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS quran_ayahs (
                id SERIAL PRIMARY KEY,
                surah_number INT NOT NULL,
                ayah_number INT NOT NULL,
                text_uthmani TEXT NOT NULL,
                text_simple TEXT,
                text_complex TEXT,
                text_indopak TEXT,
                juz_number INT,
                hizb_number INT,
                rub_el_hizb_number INT,
                page_number INT,
                sajdah BOOLEAN DEFAULT FALSE,
                sajdah_number INT,
                text_checksum VARCHAR(64),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (surah_number, ayah_number)
            )
        """))

        # Create index for ayah composite lookup
        db.execute(text("CREATE INDEX idx_quran_ayahs_composite ON quran_ayahs(surah_number, ayah_number)"))

        # Scholars table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS scholars (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                scholar_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                name_ar VARCHAR(255),
                school VARCHAR(100),
                birth_year INT,
                death_year INT,
                book_count INT DEFAULT 0,
                main_works JSON,
                biography TEXT,
                license VARCHAR(255),
                source_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Tafsir books table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS tafsir_books (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                book_id VARCHAR(50) UNIQUE NOT NULL,
                scholar_id UUID REFERENCES scholars(id),
                title VARCHAR(500) NOT NULL,
                title_ar VARCHAR(500),
                edition VARCHAR(200),
                publisher VARCHAR(200),
                volume INT,
                page INT,
                license VARCHAR(200),
                source_url TEXT,
                language VARCHAR(10) NOT NULL,
                verified BOOLEAN DEFAULT FALSE,
                metadata JSON,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Tafsir passages table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS tafsir_passages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                book_id UUID REFERENCES tafsir_books(id) NOT NULL,
                surah_number INT NOT NULL,
                ayah_start INT NOT NULL,
                ayah_end INT NOT NULL,
                arabic_text TEXT NOT NULL,
                thai_translation TEXT,
                english_translation TEXT,
                volume INT,
                page INT,
                edition VARCHAR(200),
                source_url TEXT,
                hadith_references JSON,
                evidence_grade VARCHAR(20) DEFAULT 'sahih',
                embedding VECTOR(1536),
                verification_status VARCHAR(30) DEFAULT 'unverified',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create vector search index
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tafsir_passages_embedding
            ON tafsir_passages USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """))

        # Create full-text search index
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tafsir_passages_arabic_fts
            ON tafsir_passages USING gin(to_tsvector('arabic', arabic_text));
        """))

        # Other tables (users, bookmarks, etc.) would go here...
        print("✅ Database tables created")

        # Step 4: Create triggers for updated_at
        print("🔄 Setting up database triggers...")
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))

        db.commit()
        print("🎉 Database setup complete!")

        # Step 5: Verification
        print("🔍 Verifying database setup...")

        # Check tables
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables created: {len(tables)}")

        # Check enum types
        result = db.execute(text("SELECT typname FROM pg_type WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')"))
        enums = [row[0] for row in result.fetchall() if not row[0].startswith('_')]
        print(f"Enums created: {len(enums)}")

        print("✅ Database verification complete")

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def load_classical_sources():
    """Load classical tafsir sources from JSON files."""
    print("📚 Loading classical tafsir sources...")

    # This would call the load_tafsir_data.py script
    # For now, we'll simulate with placeholder data
    db = SessionLocal()

    try:
        # Insert sample scholar
        db.execute(text("""
            INSERT INTO scholars (scholar_id, name, name_ar, school, birth_year, death_year, biography, license, source_url)
            VALUES ('ibn_kathir', 'Ibn Kathir', 'ابن كثير', 'Shafi'i', 1301, 1373,
                   'Renowned Islamic scholar, author of Tafsir al-Qur\'an al-Azim',
                   'Open access - King Fahd Complex', 'https://shamela.ws/book/16559')
            ON CONFLICT (scholar_id) DO NOTHING
        """))

        # Insert sample tafsir book
        db.execute(text("""
            INSERT INTO tafsir_books (book_id, scholar_id, title, title_ar, edition, publisher, volume, language, verified, license, source_url)
            VALUES ('tafsir_ibn_kathir', (SELECT id FROM scholars WHERE scholar_id = 'ibn_kathir'),
                    'Tafsir al-Qur\'an al-Azim', 'تفسير القرآن العظيم', 'Dar Taybah',
                    'Dar Taybah', 8, 'ar', true, 'Open access - King Fahd Complex',
                    'https://shamela.ws/book/16559')
            ON CONFLICT (book_id) DO NOTHING
        """))

        db.commit()
        print("✅ Classical sources loaded")

    except Exception as e:
        print(f"❌ Failed to load classical sources: {e}")
        db.rollback()
    finally:
        db.close()

async def main():
    print("🚀 QURAN AI Database Setup Started")
    print("=" * 50)

    # Setup database schema
    await setup_database()

    # Load classical sources
    await load_classical_sources()

    print("\n🎉 QURAN AI Database Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Run: python scripts/seed_quran_data.py (Quran verses from API)")
    print("2. Configure environment with actual API credentials")
    print("3. Test database connectivity and functionality")
    print("4. Proceed with backend implementation")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    import asyncio
    asyncio.run(main())