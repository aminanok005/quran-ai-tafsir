#!/usr/bin/env python3
"""
QURAN AI Quran Data Seeding Script
Seeds the Quran Foundation API data into PostgreSQL database
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import logging
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api'))

from services.api.models import AyahModel, SurahModel, TranslationModel

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

QURAN_API_BASE_URL = os.environ.get(
    "QURAN_API_BASE_URL",
    "https://apis.quran.foundation"
)
QURAN_API_CLIENT_ID = os.environ.get(
    "QURAN_API_CLIENT_ID",
    "REPLACE_WITH_APPROVED_CLIENT_ID"
)
QURAN_API_CLIENT_SECRET = os.environ.get(
    "QURAN_API_CLIENT_SECRET",
    "REPLACE_WITH_SECRET"
)
async def get_quran_api_token():
    """Get authentication token from Quran Foundation API."""
    try:
        logger.info("Authenticating with Quran Foundation API...")
        response = requests.post(
            f"{QURAN_API_BASE_URL}/auth/token",
            data={
                "client_id": QURAN_API_CLIENT_ID,
                "client_secret": QURAN_API_CLIENT_SECRET,
                "grant_type": "client_credentials"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        logger.error(f"Failed to authenticate with Quran API: {e}")
        return None

async def fetch_surahs(token: str) -> List[Dict[str, Any]]:
    """Fetch all surahs from Quran API."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{QURAN_API_BASE_URL}/surahs",
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Fetched {len(response.json())} surahs from Quran API")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch surahs: {e}")
        return []

async def fetch_ayah(ayah_id: str, token: str) -> Dict[str, Any]:
    """Fetch specific ayah from Quran API."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{QURAN_API_BASE_URL}/ayahs/{ayah_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch ayah {ayah_id}: {e}")
        return {}

async def seed_quran_data():
    """Seed Quran data into database."""
    logger.info("🚀 Starting Quran Data Seeding")

    db = SessionLocal()
    try:
        # Get authentication token
        token = await get_quran_api_token()
        if not token:
            logger.error("Cannot proceed without Quran API token")
            return

        # Step 1: Fetch and seed surahs
        logger.info("Seeding Quran surahs...")
        surahs = await fetch_surahs(token)

        for surah_data in surahs:
            surah = SurahModel(
                id=surah_data.get("id"),
                number=surah_data.get("number"),
                name=surah_data.get("name"),
                name_simple=surah_data.get("name_simple"),
                name_complex=surah_data.get("name_complex"),
                english_name=surah_data.get("english_name"),
                english_name_translation=surah_data.get("english_name_translation"),
                revelation_type=surah_data.get("revelation_type"),
                revelation_order=surah_data.get("revelation_order"),
                verses_count=surah_data.get("verses_count", 0),
                pages=surah_data.get("pages", []),
                audio=surah_data.get("audio", []),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            try:
                db.execute(
                    text("INSERT INTO surahs (id, number, name, name_simple, name_complex, "
                         "english_name, english_name_translation, revelation_type, "
                         "revelation_order, verses_count, pages, audio, created_at, updated_at) "
                         "VALUES (:id, :number, :name, :name_simple, :name_complex, "
                         ":english_name, :english_name_translation, :revelation_type, "
                         ":revelation_order, :verses_count, :pages, :audio, :created_at, :updated_at)"
                ), {
                    "id": str(surah.id),
                    "number": surah.number,
                    "name": surah.name,
                    "name_simple": surah.name_simple,
                    "name_complex": surah.name_complex,
                    "english_name": surah.english_name,
                    "english_name_translation": surah.english_name_translation,
                    "revelation_type": surah.revelation_type,
                    "revelation_order": surah.revelation_order,
                    "verses_count": surah.verses_count,
                    "pages": surah.pages,
                    "audio": surah.audio,
                    "created_at": surah.created_at,
                    "updated_at": surah.updated_at
                }
            except Exception as e:
                logger.warning(f"Surah {surah.number} may already exist: {e}")

        db.commit()
        logger.info(f"✅ Seeded {len(surahs)} surahs")

        # Step 2: Fetch and seed ayahs
        logger.info("Seeding Quran ayahs...")
        seeded_count = 0

        for surah_num in range(1, 115):  # All 114 Surahs
            # Fetch first 10 ayahs per surah to keep seeding manageable
            for ayah_num in range(1, 11):
                ayah_id = f"{surah_num}:{ayah_num}"
                ayah_data = await fetch_ayah(ayah_id, token)

                if ayah_data:
                    ayah = AyahModel(
                        id=ayah_data.get("id"),
                        surah_id=ayah_data.get("surah_id"),
                        surah_number=surah_num,
                        ayah_number=ayah_num,
                        text_uthmani=ayah_data.get("text_uthmani"),
                        text_simple=ayah_data.get("text_simple"),
                        text_complex=ayah_data.get("text_complex"),
                        text_indopak=ayah_data.get("text_indopak"),
                        juz_number=ayah_data.get("juz_number"),
                        hizb_number=ayah_data.get("hizb_number"),
                        rub_el_hizb_number=ayah_data.get("rub_el_hizb_number"),
                        page_number=ayah_data.get("page_number"),
                        sajdah=ayah_data.get("sajdah", False),
                        sajdah_number=ayah_data.get("sajdah_number"),
                        text_checksum=ayah_data.get("text_checksum"),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )

                    try:
                        db.execute(
                            text("INSERT INTO quran_ayahs (id, surah_id, surah_number, ayah_number, "
                                 "text_uthmani, text_simple, text_complex, text_indopak, "
                                 "juz_number, hizb_number, rub_el_hizb_number, page_number, "
                                 "sajdah, sajdah_number, text_checksum, created_at, updated_at) "
                                 "VALUES (:id, :surah_id, :surah_number, :ayah_number, "
                                 ":text_uthmani, :text_simple, :text_complex, :text_indopak, "
                                 ":juz_number, :hizb_number, :rub_el_hizb_number, :page_number, "
                                 ":sajdah, :sajdah_number, :text_checksum, :created_at, :updated_at)"
                        ), {
                            "id": str(ayah.id),
                            "surah_id": str(ayah.surah_id),
                            "surah_number": ayah.surah_number,
                            "ayah_number": ayah.ayah_number,
                            "text_uthmani": ayah.text_uthmani,
                            "text_simple": ayah.text_simple,
                            "text_complex": ayah.text_complex,
                            "text_indopak": ayah.text_indopak,
                            "juz_number": ayah.juz_number,
                            "hizb_number": ayah.hizb_number,
                            "rub_el_hizb_number": ayah.rub_el_hizb_number,
                            "page_number": ayah.page_number,
                            "sajdah": ayah.sajdah,
                            "sajdah_number": ayah.sajdah_number,
                            "text_checksum": ayah.text_checksum,
                            "created_at": ayah.created_at,
                            "updated_at": ayah.updated_at
                        }
                    except Exception as e:
                        logger.warning(f"Ayah {ayah_id} may already exist: {e}")

                    seeded_count += 1

        db.commit()
        logger.info(f"✅ Seeded {seeded_count} ayahs")

        # Step 3: Create initial user
        logger.info("Creating initial admin user...")
        try:
            db.execute(
                text("INSERT INTO users (id, username, email, role, is_active, "
                     "preferences, profile, stripe_customer_id, stripe_subscription_status, "
                     "streak_count, last_active_date, gems_wallet, hearts_count, "
                     "created_at, updated_at)"
                ), {
                    "id": str(uuid.uuid4()),
                    "username": "admin",
                    "email": "admin@quran-ai.org",
                    "role": "platform_admin",
                    "is_active": True,
                    "preferences": {},
                    "profile": {},
                    "stripe_customer_id": None,
                    "stripe_subscription_status": "none",
                    "streak_count": 0,
                    "last_active_date": None,
                    "gems_wallet": 0,
                    "hearts_count": 5,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            )
            db.commit()
            logger.info("✅ Created initial admin user")
        except Exception as e:
            logger.warning(f"User may already exist: {e}")

        logger.info("🎉 Quran data seeding complete!")

    except Exception as e:
        logger.error(f"Quran data seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    import uuid

    asyncio.run(seed_quran_data())