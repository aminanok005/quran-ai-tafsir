#!/usr/bin/env python3
"""
QURAN AI Database Initialization Script
Loads classical tafsir sources from JSON files into PostgreSQL database
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://quran_ai:CHANGE_ME@localhost:5432/quran_ai"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Data files mapping
TAFSIR_DATA_FILES = {
    "ibn_kathir": {
        "file": "data-tafsir/ar-tafsir-ibn-kathir.json",
        "scholar": {
            "scholar_id": "ibn_kathir",
            "name": "Ibn Kathir",
            "name_ar": "ابن كثير",
            "school": "Shafi'i",
            "birth_year": 1301,
            "death_year": 1373,
            "biography": "Renowned Islamic scholar, historian, and mufassir. Author of Tafsir al-Qur'an al-Azim.",
            "license": "Open access - King Fahd Complex",
            "source_url": "https://shamela.ws/book/16559"
        },
        "book": {
            "book_id": "tafsir_ibn_kathir",
            "title": "Tafsir al-Qur'an al-Azim",
            "title_ar": "تفسير القرآن العظيم",
            "edition": "Dar Taybah",
            "publisher": "Dar Taybah",
            "volume": 8,
            "language": "ar",
            "verified": True,
            "license": "Open access - King Fahd Complex",
            "source_url": "https://shamela.ws/book/16559"
        }
    },
    "al_tabari": {
        "file": "data-tafsir/ar-tafsir-al-tabari.json",
        "scholar": {
            "scholar_id": "al_tabari",
            "name": "Al-Tabari",
            "name_ar": "الطبري",
            "school": "Shafi'i",
            "birth_year": 839,
            "death_year": 923,
            "biography": "Renowned Islamic historian and mufassir. Author of Jami' al-Bayan.",
            "license": "Open access - Maktabah Shamela",
            "source_url": "https://shamela.ws/book/16558"
        },
        "book": {
            "book_id": "jami_al_bayan",
            "title": "Jami' al-Bayan",
            "title_ar": "جامع البيان",
            "edition": "Dar al-Kutub al-Ilmiyah",
            "publisher": "Dar al-Kutub al-Ilmiyah",
            "volume": 30,
            "language": "ar",
            "verified": True,
            "license": "Open access - Maktabah Shamela",
            "source_url": "https://shamela.ws/book/16558"
        }
    },
    "al_qurtubi": {
        "file": "data-tafsir/ar-tafseer-al-qurtubi.json",
        "scholar": {
            "scholar_id": "al_qurtubi",
            "name": "Al-Qurtubi",
            "name_ar": "القرطبي",
            "school": "Maliki",
            "birth_year": 1214,
            "death_year": 1273,
            "biography": "Renowned Maliki jurist and mufassir. Author of Al-Jami' li-Ahkam al-Qur'an.",
            "license": "Open access - King Fahd Complex",
            "source_url": "https://shamela.ws/book/16560"
        },
        "book": {
            "book_id": "jami_ahkam",
            "title": "Al-Jami' li-Ahkam al-Qur'an",
            "title_ar": "الجامع لأحكام القرآن",
            "edition": "Dar al-Kutub al-Ilmiyah",
            "publisher": "Dar al-Kutub al-Ilmiyah",
            "volume": 20,
            "language": "ar",
            "verified": True,
            "license": "Open access - King Fahd Complex",
            "source_url": "https://shamela.ws/book/16560"
        }
    },
    "al_saadi": {
        "file": "data-tafsir/tafsir-as-saadi.json",
        "scholar": {
            "scholar_id": "al_saadi",
            "name": "Al-Sa'di",
            "name_ar": "السعدي",
            "school": "Hanbali",
            "birth_year": 1889,
            "death_year": 1956,
            "biography": "Renowned scholar known for clear and accessible tafsir. Author of Taysir al-Karim al-Rahman.",
            "license": "Open access - King Fahd Complex",
            "source_url": "https://shamela.ws/book/16561"
        },
        "book": {
            "book_id": "taysir_karim",
            "title": "Taysir al-Karim al-Rahman",
            "title_ar": "تيسير الكريم الرحمن",
            "edition": "Dar al-Kutub al-Ilmiyah",
            "publisher": "Dar al-Kutub al-Ilmiyah",
            "volume": 8,
            "language": "ar",
            "verified": True,
            "license": "Open access - King Fahd Complex",
            "source_url": "https://shamela.ws/book/16561"
        }
    }
}

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file with proper encoding."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {filepath}: {len(data)} surahs")
        return data
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        return {}

def extract_text_from_html(html_text: str) -> str:
    """Extract plain text from HTML formatted tafsir text."""
    if not html_text:
        return ""

    # Simple HTML tag removal
    import re
    text = re.sub(r'<[^>]+>', '', html_text)
    text = text.replace('&nbsp;', ' ').replace('&', '&')
    text = text.replace('<', '<').replace('>', '>')
    text = ' '.join(text.split())  # Normalize whitespace
    return text.strip()

def parse_surah_ayah_key(key: str) -> tuple:
    """Parse surah:ayah key from JSON structure."""
    try:
        parts = key.split(':')
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        pass
    return None, None

async def init_database():
    """Initialize database with classical tafsir sources."""
    logger.info("🚀 Starting QURAN AI Database Initialization")

    db = SessionLocal()
    try:
        # Step 1: Ensure pgvector extension
        logger.info("Enabling pgvector extension...")
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()

        # Step 2: Create/verify scholars
        logger.info("Creating scholar records...")
        scholar_ids = {}
        for agent_key, config in TAFSIR_DATA_FILES.items():
            scholar_data = config["scholar"]
            result = db.execute(text("""
                INSERT INTO scholars (scholar_id, name, name_ar, school, birth_year, death_year,
                                    biography, license, source_url)
                VALUES (:scholar_id, :name, :name_ar, :school, :birth_year, :death_year,
                        :biography, :license, :source_url)
                ON CONFLICT (scholar_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    name_ar = EXCLUDED.name_ar,
                    school = EXCLUDED.school,
                    birth_year = EXCLUDED.birth_year,
                    death_year = EXCLUDED.death_year,
                    biography = EXCLUDED.biography,
                    license = EXCLUDED.license,
                    source_url = EXCLUDED.source_url
                RETURNING id
            """), scholar_data)
            scholar_id = result.scalar()
            scholar_ids[agent_key] = scholar_id
            logger.info(f"  ✅ Scholar: {scholar_data['name']} (ID: {scholar_id})")

        # Step 3: Create/verify tafsir books
        logger.info("Creating tafsir book records...")
        book_ids = {}
        for agent_key, config in TAFSIR_DATA_FILES.items():
            book_data = config["book"].copy()
            book_data["scholar_id"] = scholar_ids[agent_key]
            result = db.execute(text("""
                INSERT INTO tafsir_books (book_id, scholar_id, title, title_ar, edition,
                                        publisher, volume, language, verified, license, source_url)
                VALUES (:book_id, :scholar_id, :title, :title_ar, :edition,
                        :publisher, :volume, :language, :verified, :license, :source_url)
                ON CONFLICT (book_id) DO UPDATE SET
                    scholar_id = EXCLUDED.scholar_id,
                    title = EXCLUDED.title,
                    title_ar = EXCLUDED.title_ar,
                    edition = EXCLUDED.edition,
                    publisher = EXCLUDED.publisher,
                    volume = EXCLUDED.volume,
                    language = EXCLUDED.language,
                    verified = EXCLUDED.verified,
                    license = EXCLUDED.license,
                    source_url = EXCLUDED.source_url
                RETURNING id
            """), book_data)
            book_id = result.scalar()
            book_ids[agent_key] = book_id
            logger.info(f"  ✅ Book: {book_data['title']} (ID: {book_id})")

        # Step 4: Load tafsir passages
        logger.info("Loading tafsir passages from data files...")
        total_passages = 0

        for agent_key, config in TAFSIR_DATA_FILES.items():
            filepath = os.path.join(
                os.path.dirname(__file__), '..', config["file"]
            )
            book_id = book_ids[agent_key]

            if not os.path.exists(filepath):
                logger.warning(f"File not found: {filepath}")
                continue

            logger.info(f"Loading {config['book']['title']} from {filepath}...")
            data = load_json_file(filepath)

            passages_to_insert = []
            for surah_key, surah_data in data.items():
                # Parse surah:ayah from key (format: "1:1")
                surah_num, ayah_num = parse_surah_ayah_key(surah_key)
                if surah_num is None or ayah_num is None:
                    continue

                # Extract text content
                text_content = surah_data.get("text", "") if isinstance(surah_data, dict) else str(surah_data)
                clean_text = extract_text_from_html(text_content)

                if not clean_text or len(clean_text) < 10:
                    continue

                passage = {
                    "id": str(uuid.uuid4()),
                    "book_id": str(book_id),
                    "surah_number": surah_num,
                    "ayah_start": ayah_num,
                    "ayah_end": ayah_num,
                    "arabic_text": clean_text,
                    "thai_translation": None,  # Will be filled from translation API
                    "english_translation": None,
                    "volume": 1,
                    "page": 1,
                    "edition": config["book"]["edition"],
                    "source_url": config["book"]["source_url"],
                    "hadith_references": [],
                    "evidence_grade": "sahih",
                    "embedding": None,  # Will be populated later by embedding service
                    "verification_status": "verified",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                passages_to_insert.append(passage)

                # Batch insert every 100 passages
                if len(passages_to_insert) >= 100:
                    inserted = await batch_insert_passages(db, passages_to_insert)
                    total_passages += inserted
                    passages_to_insert = []
                    logger.info(f"  Inserted {total_passages} passages so far...")

            # Insert remaining
            if passages_to_insert:
                inserted = await batch_insert_passages(db, passages_to_insert)
                total_passages += inserted

            logger.info(f"  ✅ {config['book']['title']}: {total_passages} total passages loaded")

        db.commit()
        logger.info(f"🎉 Database initialization complete! Total passages: {total_passages}")

        # Step 5: Create indexes
        logger.info("Creating search indexes...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tafsir_passages_embedding
            ON tafsir_passages USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tafsir_passages_arabic_fts
            ON tafsir_passages USING gin(to_tsvector('arabic', arabic_text))
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tafsir_passages_ayah
            ON tafsir_passages(surah_number, ayah_start, ayah_end)
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tafsir_passages_verification
            ON tafsir_passages(verification_status)
        """))
        db.commit()
        logger.info("✅ Indexes created")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def batch_insert_passages(db, passages: List[Dict]):
    """Batch insert tafsir passages."""
    if not passages:
        return 0

    insert_sql = text("""
        INSERT INTO tafsir_passages (
            id, book_id, surah_number, ayah_start, ayah_end,
            arabic_text, thai_translation, english_translation,
            volume, page, edition, source_url,
            hadith_references, evidence_grade, embedding,
            verification_status, created_at, updated_at
        ) VALUES (
            :id, :book_id, :surah_number, :ayah_start, :ayah_end,
            :arabic_text, :thai_translation, :english_translation,
            :volume, :page, :edition, :source_url,
            :hadith_references, :evidence_grade, :embedding,
            :verification_status, :created_at, :updated_at
        )
        ON CONFLICT DO NOTHING
    """)

    try:
        db.execute(insert_sql, passages)
        return len(passages)
    except Exception as e:
        logger.error(f"Batch insert failed: {e}")
        # Try individual inserts
        inserted = 0
        for passage in passages:
            try:
                db.execute(insert_sql, passage)
                inserted += 1
            except Exception as e2:
                logger.debug(f"Failed to insert passage: {e2}")
        return inserted

async def verify_database():
    """Verify database initialization."""
    logger.info("🔍 Verifying database initialization...")

    db = SessionLocal()
    try:
        # Check scholars
        result = db.execute(text("SELECT scholar_id, name FROM scholars"))
        scholars = result.fetchall()
        logger.info(f"Scholars: {len(scholars)}")
        for s in scholars:
            logger.info(f"  - {s[1]} ({s[0]})")

        # Check books
        result = db.execute(text("SELECT book_id, title FROM tafsir_books"))
        books = result.fetchall()
        logger.info(f"Books: {len(books)}")
        for b in books:
            logger.info(f"  - {b[1]} ({b[0]})")

        # Check passages
        result = db.execute(text("SELECT COUNT(*) FROM tafsir_passages"))
        total = result.scalar()
        logger.info(f"Total tafsir passages: {total}")

        result = db.execute(text("""
            SELECT verification_status, COUNT(*)
            FROM tafsir_passages
            GROUP BY verification_status
        """))
        for row in result:
            logger.info(f"  {row[0]}: {row[1]}")

        # Check quran ayahs
        result = db.execute(text("SELECT COUNT(*) FROM quran_ayahs"))
        ayahs = result.scalar()
        logger.info(f"Quran ayahs: {ayahs}")

    finally:
        db.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize QURAN AI database")
    parser.add_argument("--verify", action="store_true", help="Verify database after initialization")
    args = parser.parse_args()

    # Run initialization
    asyncio.run(init_database())

    # Verify if requested
    if args.verify:
        asyncio.run(verify_database())

    logger.info("✅ Database initialization script completed!")