"""
Ibn Kathir Source Retrieval

Retrieves relevant sources from Ibn Kathir's tafsir for specific Quran verses.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
from functools import lru_cache

from ....shared_types import TafsirSource

logger = logging.getLogger(__name__)

class IbnKathirSourceRetrieval:
    """
    Source retrieval system for Ibn Kathir's tafsir.

    This class implements the source retrieval functionality for the Ibn Kathir agent,
    finding relevant passages from Ibn Kathir's tafsir based on the Quran verse
    and context.
    """

    def __init__(self):
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.index: Dict[str, List[str]] = {}  # Ayah ID -> list of source IDs
        self.embedding_model = None
        self.vector_db = None
        self.cache = {}

        # Source metadata
        self.source_metadata = {
            "tafsir_ibn_kathir": {
                "title": "Tafsir al-Bahr al-Mu'taqqad (Tafsir Ibn Kathir)",
                "author": "Ibn Kathir",
                "author_ar": "ابن كثير",
                "scholar": "Ibn Kathir",
                "scholar_ar": "ابن كثير",
                "methodology": "ma'thur",
                "language": "ar",
                "volumes": 30,
                "chapters": 114,
                "sources": ["shamela", "quran-database"],
                "verification_status": "pending"
            }
        }

    async def load_sources(self, source_path: Optional[str] = None):
        """
        Load and index sources for retrieval.

        Args:
            source_path: Optional path to source files
        """
        try:
            if source_path:
                await self._load_from_file(source_path)
            else:
                await self._load_from_database()

            await self._build_index()
            logger.info("Sources loaded and indexed successfully")

        except Exception as e:
            logger.error(f"Failed to load sources: {str(e)}")
            raise

    async def _load_from_file(self, source_path: str):
        """Load sources from file."""
        path = Path(source_path)
        if not path.exists():
            logger.warning(f"Source path does not exist: {source_path}")
            return

        # Mock implementation - would load actual Ibn Kathir tafsir data
        # In reality, this would parse Shamela or other tafsir databases
        self.sources = {
            "ibn_kathir_1_1": {
                "id": "ibn_kathir_1_1",
                "source_id": "tafsir_ibn_kathir",
                "book_id": "tafsir_ibn_kathir",
                "author": "Ibn Kathir",
                "author_ar": "ابن كثير",
                "title": "Tafsir Ibn Kathir - Surah Al-Fatiha",
                "edition": "Dar Al-Fikr",
                "volume": 1,
                "page": 1,
                "chapter": 1,
                "surah": 1,
                "ayah": 1,
                "original_text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
                "thai_translation": "ใน� Nome de Allah, le Miséricordieux, le Compasseur.",
                "grading": "sahih",
                "verified": True,
                "language": "ar",
                "source_url": "https://shamela.org/book/tafsir_ibn_kathir/1/1",
                "metadata": {"confidence": 0.95}
            },
            "ibn_kathir_2_255": {
                "id": "ibn_kathir_2_255",
                "source_id": "tafsir_ibn_kathir",
                "book_id": "tafsir_ibn_kathir",
                "author": "Ibn Kathir",
                "author_ar": "ابن كثير",
                "title": "Tafsir Ibn Kathir - Surah Al-Baqarah Verse 255",
                "edition": "Dar Al-Fikr",
                "volume": 2,
                "page": 255,
                "chapter": 2,
                "surah": 2,
                "ayah": 255,
                "original_text": "اللَّهُ لا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
                "thai_translation": "อัลลอฮฺไม่มีเจ้าอื่นใดนอกจากพระองค์ ผู้ทรงเป็นอมตะ ผู้ทรงดำรงอยู่ตลอดเวลา",
                "grading": "sahih",
                "verified": True,
                "language": "ar",
                "source_url": "https://shamela.org/book/tafsir_ibn_kathir/2/255",
                "metadata": {"confidence": 0.98}
            },
            "ibn_kathir_3_32": {
                "id": "ibn_kathir_3_32",
                "source_id": "tafsir_ibn_kathir",
                "book_id": "tafsir_ibn_kathir",
                "author": "Ibn Kathir",
                "author_ar": "ابن كثير",
                "title": "Tafsir Ibn Kathir - Surah Al-Imran Verse 32",
                "edition": "Dar Al-Fikr",
                "volume": 3,
                "page": 32,
                "chapter": 3,
                "surah": 3,
                "ayah": 32,
                "original_text": "وَلَا تَقُولُوا لِرَسُولِ اللَّهِ أَو لاتَقُولُوا لِأَحَدٍ بَعْدَ أَنْ تُسْلِمَ",
                "thai_translation": "และอย่ากล่าวว่า \"โอ้ บรรดาผู้ศรัทธาทั้งหลาย ท่านอย่าได้กล่าวว่า (ทำนองว่า) เราจะไม่ฟังคำของท่านใด\"",
                "grading": "sahih",
                "verified": True,
                "language": "ar",
                "source_url": "https://shamela.org/book/tafsir_ibn_kathir/3/32",
                "metadata": {"confidence": 0.97}
            }
        }

    async def _load_from_database(self):
        """Load sources from database."""
        # Mock implementation - would connect to actual database
        logger.info("Loading Ibn Kathir sources from database...")
        # Would query database for tafsir passages with proper Ayah mapping
        await asyncio.sleep(0.1)  # Simulate async database query

    async def _build_index(self):
        """Build index for efficient retrieval."""
        self.index = {}

        for source_id, source in self.sources.items():
            ayah_id = f"{source.get('surah', '')}:{source.get('ayah', '')}"

            if ayah_id not in self.index:
                self.index[ayah_id] = []

            self.index[ayah_id].append(source_id)

        logger.info(f"Built index for {len(self.index)} Ayahs")

    @lru_cache(maxsize=128)
    async def retrieve(self, ayah_id: str, context: Dict[str, Any],
                      methodology: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve sources for a specific ayah.

        Args:
            ayah_id: Ayah identifier (e.g., "1:1")
            context: Context information
            methodology: Agent methodology
            max_results: Maximum number of sources to return

        Returns:
            List of retrieved sources
        """
        try:
            # Check cache first
            cache_key = f"{ayah_id}:{methodology}:{max_results}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            sources = []

            # Direct lookup from index
            if ayah_id in self.index:
                source_ids = self.index[ayah_id]

                for source_id in source_ids[:max_results]:
                    if source_id in self.sources:
                        source = self.sources[source_id].copy()

                        # Calculate relevance score
                        relevance = await self._calculate_relevance(source, context)
                        source["relevance_score"] = relevance
                        source["methodology_match"] = self._check_methodology_match(
                            source, methodology
                        )

                        sources.append(source)

            # If no direct matches, try semantic search
            if not sources:
                sources = await self._semantic_search(ayah_id, context, max_results)

            # Sort by relevance
            sources.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

            # Cache results
            self.cache[cache_key] = sources

            logger.debug(f"Retrieved {len(sources)} sources for ayah {ayah_id}")
            return sources

        except Exception as e:
            logger.error(f"Source retrieval failed for {ayah_id}: {str(e)}")
            return []

    async def _calculate_relevance(self, source: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate relevance score for a source.

        Args:
            source: Source to evaluate
            context: Context information

        Returns:
            Relevance score between 0 and 1
        """
        scores = []

        # Match score based on ayah number
        if "surah" in source and "ayah" in source:
            source_surah = source["surah"]
            source_ayah = source["ayah"]
            context_surah = context.get("surah", 0)
            context_ayah = context.get("ayah", 0)

            if source_surah == context_surah and source_ayah == context_ayah:
                scores.append(1.0)
            elif source_surah == context_surah:
                # Same surah, different ayah - lower relevance
                scores.append(0.7)
            else:
                scores.append(0.1)

        # Text match score
        source_text = source.get("original_text", "")
        context_text = context.get("arabic_text", "")

        if source_text and context_text:
            # Simple text matching
            common_words = set(source_text.split()) & set(context_text.split())
            if common_words:
                text_score = len(common_words) / max(len(source_text.split()), 1)
                scores.append(text_score)
            else:
                scores.append(0.0)
        else:
            scores.append(0.0)

        # Methodology match
        if "methodology" in source:
            methodology_score = 1.0 if source["methodology"] == context.get("methodology") else 0.0
            scores.append(methodology_score)

        # Source quality score
        quality_score = source.get("metadata", {}).get("confidence", 0.5)
        scores.append(quality_score)

        # Calculate weighted average
        if scores:
            return sum(scores) / len(scores)

        return 0.0

    def _check_methodology_match(self, source: Dict[str, Any], methodology: str) -> bool:
        """
        Check if source matches the agent's methodology.

        Args:
            source: Source to check
            methodology: Target methodology

        Returns:
            True if source matches methodology
        """
        source_methodology = source.get("methodology", "")
        return source_methodology == methodology or methodology == "ma'thur"

    async def _semantic_search(self, ayah_id: str, context: Dict[str, Any],
                             max_results: int) -> List[Dict[str, Any]]:
        """
        Perform semantic search for relevant sources.

        Args:
            ayah_id: Ayah identifier
            context: Context information
            max_results: Maximum number of results

        Returns:
            List of relevant sources
        """
        # Mock implementation - would use vector embeddings in real system
        # For now, return empty list as we're relying on direct index matching
        return []

    def get_source_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about available sources.

        Returns:
            Source metadata
        """
        return self.source_metadata