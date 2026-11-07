import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@localhost/quran_ai_test")

from scripts import ingest_tafsir_vectors
from services.api.config import Settings


class IngestionEnvironmentGuardTests(unittest.TestCase):
    def test_explicit_development_environment_is_allowed(self):
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+psycopg://postgres@localhost/quran_ai_test",
            ENVIRONMENT="development",
        )

        ingest_tafsir_vectors._require_development_environment(
            settings.environment,
            "environment" in settings.model_fields_set,
        )

    def test_missing_environment_is_rejected(self):
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+psycopg://postgres@localhost/quran_ai_test",
        )

        with self.assertRaisesRegex(RuntimeError, "explicitly configured"):
            ingest_tafsir_vectors._require_development_environment(
                settings.environment,
                "environment" in settings.model_fields_set,
            )

    def test_non_development_environment_is_rejected(self):
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+psycopg://postgres@localhost/quran_ai_test",
            ENVIRONMENT="production",
        )

        with self.assertRaisesRegex(RuntimeError, "explicitly configured"):
            ingest_tafsir_vectors._require_development_environment(
                settings.environment,
                "environment" in settings.model_fields_set,
            )


class IngestionModeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.args = SimpleNamespace(
            batch_size=16,
            file=Path(__file__),
            source_id="fixture-source",
            dataset="in-memory-fixture",
            work=None,
            scholar_name="Fixture scholar",
            source_url=None,
            edition=None,
            license=None,
            verification_evidence=None,
            apply_development_only=False,
        )
        self.parsed = SimpleNamespace(
            records=[SimpleNamespace(normalized_text="fixture text")],
            issues=[],
        )

    async def test_default_dry_run_does_not_call_embedding_or_database(self):
        with (
            patch.object(ingest_tafsir_vectors, "parse_json_file", return_value=self.parsed),
            patch.object(ingest_tafsir_vectors, "create_engine") as create_engine,
            patch.object(ingest_tafsir_vectors, "upsert_development_records") as upsert,
            patch(
                "services.api.services.embedding.embed_texts",
                new_callable=AsyncMock,
            ) as embed_texts,
        ):
            result = await ingest_tafsir_vectors._ingest(self.args)

        self.assertEqual(result, 0)
        embed_texts.assert_not_awaited()
        create_engine.assert_not_called()
        upsert.assert_not_called()

    async def test_apply_without_explicit_environment_stops_before_provider_or_database(self):
        self.args.apply_development_only = True
        unset_environment = SimpleNamespace(
            environment="development",
            model_fields_set=set(),
            database_url="postgresql+psycopg://postgres@localhost/quran_ai_test",
        )
        with (
            patch.object(ingest_tafsir_vectors, "parse_json_file", return_value=self.parsed),
            patch.object(ingest_tafsir_vectors, "create_engine") as create_engine,
            patch.object(ingest_tafsir_vectors, "upsert_development_records") as upsert,
            patch("services.api.config.settings", unset_environment),
            patch(
                "services.api.services.embedding.embed_texts",
                new_callable=AsyncMock,
            ) as embed_texts,
        ):
            with self.assertRaisesRegex(RuntimeError, "explicitly configured"):
                await ingest_tafsir_vectors._ingest(self.args)

        embed_texts.assert_not_awaited()
        create_engine.assert_not_called()
        upsert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
