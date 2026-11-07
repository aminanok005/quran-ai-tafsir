import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.api.config import Settings


class SettingsEnvironmentTests(unittest.TestCase):
    def test_local_environment_file_overrides_base_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".env").write_text(
                "DATABASE_URL=postgresql://base.example/quran\n"
                "LLM_MODEL=base-model\n",
                encoding="utf-8",
            )
            (root / ".env.local").write_text(
                "DATABASE_URL=postgresql://local.example/quran\n"
                "LLM_MODEL=local-model\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                settings = Settings(
                    _env_file=(root / ".env", root / ".env.local"),
                )

        self.assertEqual(settings.database_url, "postgresql://local.example/quran")
        self.assertEqual(settings.llm_model, "local-model")

    def test_shell_environment_overrides_local_environment_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            local_file = Path(temporary_directory) / ".env.local"
            local_file.write_text(
                "DATABASE_URL=postgresql://local.example/quran\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql://shell.example/quran"},
            ):
                settings = Settings(_env_file=local_file)

        self.assertEqual(settings.database_url, "postgresql://shell.example/quran")

    def test_comma_separated_lists_are_accepted_from_environment_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            local_file = Path(temporary_directory) / ".env.local"
            local_file.write_text(
                "DATABASE_URL=postgresql://local.example/quran\n"
                "APP_SUPPORTED_LOCALES=th, ar, en\n"
                "CORS_ORIGINS=http://localhost:3000, https://example.test\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                settings = Settings(_env_file=local_file)

        self.assertEqual(settings.supported_languages, ["th", "ar", "en"])
        self.assertEqual(
            settings.cors_origins,
            ["http://localhost:3000", "https://example.test"],
        )
