import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from services.api.config import Settings


class SettingsEnvironmentTests(unittest.TestCase):
    def settings_from_environment(self, **environment):
        values = {"DATABASE_URL": "postgresql://localhost/quran", **environment}
        with patch.dict(os.environ, values, clear=True):
            return Settings(_env_file=None)

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

    def test_tts_is_disabled_and_independent_from_llm_by_default(self):
        settings = self.settings_from_environment(
            LLM_API_KEY="llm-secret",
            LLM_MODEL="llm-model",
            OPENAI_API_KEY="openai-secret",
        )

        self.assertFalse(settings.tts_enabled)
        self.assertIsNone(settings.tts_api_key)
        self.assertIsNone(settings.tts_model)
        self.assertIsNone(settings.tts_api_base_url)
        self.assertEqual(settings.tts_allowed_editions, [])
        self.assertEqual(settings.tts_voice_map, {})
        self.assertEqual(settings.tts_max_source_bytes, 2000000)
        self.assertEqual(settings.tts_cache_max_bytes, 50000000)

    def test_tts_settings_parse_explicit_editions_and_voice_map(self):
        settings = self.settings_from_environment(
            TTS_ENABLED="true",
            TTS_API_KEY="tts-secret",
            TTS_MODEL="tts-model",
            TTS_API_BASE_URL="https://tts.example.test/v1",
            TTS_ALLOWED_EDITIONS="th.thai, en.sahih, id.indonesian",
            TTS_VOICE_MAP=json.dumps(
                {"th": "thai-voice", "en": "english-voice", "id": "indonesian-voice"}
            ),
            TTS_TIMEOUT_SECONDS="45",
            TTS_MAX_TEXT_CHARS="4000",
            TTS_MAX_AUDIO_BYTES="20000000",
            TTS_MAX_SOURCE_BYTES="3000000",
            TTS_CACHE_MAX_BYTES="75000000",
            TTS_CACHE_TTL_SECONDS="600",
            TTS_RATE_LIMIT_PER_MINUTE="20",
        )

        self.assertTrue(settings.tts_enabled)
        self.assertEqual(settings.tts_api_key, "tts-secret")
        self.assertEqual(settings.tts_model, "tts-model")
        self.assertEqual(settings.tts_api_base_url, "https://tts.example.test/v1")
        self.assertEqual(settings.tts_allowed_editions, ["th.thai", "en.sahih", "id.indonesian"])
        self.assertEqual(
            settings.tts_voice_map,
            {"th": "thai-voice", "en": "english-voice", "id": "indonesian-voice"},
        )
        self.assertEqual(settings.tts_timeout_seconds, 45)
        self.assertEqual(settings.tts_max_text_chars, 4000)
        self.assertEqual(settings.tts_max_audio_bytes, 20000000)
        self.assertEqual(settings.tts_max_source_bytes, 3000000)
        self.assertEqual(settings.tts_cache_max_bytes, 75000000)
        self.assertEqual(settings.tts_cache_ttl_seconds, 600)
        self.assertEqual(settings.tts_rate_limit_per_minute, 20)

    def test_tts_rejects_unapproved_editions(self):
        with self.assertRaises(ValidationError):
            self.settings_from_environment(TTS_ALLOWED_EDITIONS="ar.mishary")

    def test_tts_rejects_non_https_provider_urls(self):
        for url in (
            "http://tts.example.test/v1",
            "ftp://tts.example.test/v1",
            "https://tts.example.test:99999/v1",
            "not-a-url",
        ):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                self.settings_from_environment(TTS_API_BASE_URL=url)

    def test_tts_accepts_http_only_for_recognized_loopback_hosts(self):
        for url in (
            "http://localhost:8001/v1",
            "http://127.0.0.1:8001/v1",
            "http://[::1]:8001/v1",
        ):
            with self.subTest(url=url):
                settings = self.settings_from_environment(TTS_API_BASE_URL=url)
                self.assertEqual(settings.tts_api_base_url, url)

    def test_tts_rejects_invalid_limits(self):
        invalid_limits = (
            ("TTS_TIMEOUT_SECONDS", "0"),
            ("TTS_TIMEOUT_SECONDS", "121"),
            ("TTS_MAX_TEXT_CHARS", "0"),
            ("TTS_MAX_TEXT_CHARS", "100001"),
            ("TTS_MAX_AUDIO_BYTES", "0"),
            ("TTS_MAX_AUDIO_BYTES", "100000001"),
            ("TTS_MAX_SOURCE_BYTES", "0"),
            ("TTS_MAX_SOURCE_BYTES", "100000001"),
            ("TTS_CACHE_MAX_BYTES", "0"),
            ("TTS_CACHE_MAX_BYTES", "1000000001"),
            ("TTS_CACHE_TTL_SECONDS", "0"),
            ("TTS_CACHE_TTL_SECONDS", "86401"),
            ("TTS_RATE_LIMIT_PER_MINUTE", "0"),
            ("TTS_RATE_LIMIT_PER_MINUTE", "1001"),
        )
        for setting, value in invalid_limits:
            with self.subTest(setting=setting, value=value), self.assertRaises(ValidationError):
                self.settings_from_environment(**{setting: value})

    def test_tts_rejects_unknown_voice_languages(self):
        with self.assertRaises(ValidationError):
            self.settings_from_environment(
                TTS_VOICE_MAP=json.dumps({"th": "thai-voice", "fr": "french-voice"})
            )

    def test_tts_rejects_empty_voice_names(self):
        with self.assertRaises(ValidationError):
            self.settings_from_environment(TTS_VOICE_MAP=json.dumps({"en": "  "}))
