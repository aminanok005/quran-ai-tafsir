import os
import unittest
from unittest import mock

from scripts.seed_quran_data import (
    EXPECTED_AYAH_COUNT,
    SURAH_AYAH_COUNTS,
    get_api_token,
    get_auth_base_url,
    fetch_surah_ayahs,
    normalize_ayah,
    validate_ayahs,
)


class QuranSeederTests(unittest.TestCase):
    def test_normalize_ayah_maps_only_canonical_columns(self):
        ayah = normalize_ayah(
            2,
            {
                "verse_number": 255,
                "text_uthmani": "آية",
                "text_uthmani_simple": "ayah",
                "text_imlaei": "ayah",
                "juz_number": 3,
                "sajdah_type": "recommended",
            },
        )

        self.assertEqual(ayah["surah_number"], 2)
        self.assertEqual(ayah["ayah_number"], 255)
        self.assertEqual(ayah["text_uthmani"], "آية")
        self.assertEqual(ayah["text_simple"], "ayah")
        self.assertEqual(ayah["text_complex"], "ayah")
        self.assertTrue(ayah["sajdah"])
        self.assertNotIn("id", ayah)
        self.assertNotIn("surah_id", ayah)

    def test_normalize_ayah_rejects_missing_uthmani_text(self):
        with self.assertRaisesRegex(ValueError, "Missing Uthmani text"):
            normalize_ayah(1, {"ayah_number": 1})

    def test_validate_ayahs_rejects_incomplete_or_duplicate_results(self):
        with self.assertRaisesRegex(ValueError, "Expected 2"):
            validate_ayahs([{"surah_number": 1, "ayah_number": 1}], expected_count=2)

        duplicate = [
            {"surah_number": 1, "ayah_number": 1},
            {"surah_number": 1, "ayah_number": 1},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_ayahs(duplicate, expected_count=2)

    def test_canonical_surah_counts_sum_to_expected_total(self):
        self.assertEqual(len(SURAH_AYAH_COUNTS), 114)
        self.assertEqual(sum(SURAH_AYAH_COUNTS), EXPECTED_AYAH_COUNT)

    def test_auth_base_url_matches_production_and_prelive_api_hosts(self):
        self.assertEqual(
            get_auth_base_url("https://apis.quran.foundation"),
            "https://oauth2.quran.foundation",
        )
        self.assertEqual(
            get_auth_base_url("https://apis-prelive.quran.foundation/content/api/v4"),
            "https://prelive-oauth2.quran.foundation",
        )

    def test_get_api_token_uses_oauth2_basic_auth_and_configured_scope(self):
        with (
            mock.patch.dict(
                os.environ,
                {
                    "QURAN_API_CLIENT_ID": "test-client",
                    "QURAN_API_CLIENT_SECRET": "test-secret",
                    "QURAN_API_CONTENT_SCOPE": "content",
                },
                clear=True,
            ),
            mock.patch(
                "scripts.seed_quran_data.QURAN_API_BASE_URL",
                "https://apis.quran.foundation",
            ),
            mock.patch("requests.post") as post,
        ):
            post.return_value.json.return_value = {"access_token": "test-token"}

            token = get_api_token()

        self.assertEqual(token, "test-token")
        post.assert_called_once_with(
            "https://oauth2.quran.foundation/oauth2/token",
            auth=("test-client", "test-secret"),
            data={"grant_type": "client_credentials", "scope": "content"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )

    @mock.patch.dict(os.environ, {"QURAN_API_CLIENT_ID": "test-client"})
    @mock.patch("requests.get")
    def test_fetch_surah_ayahs_follows_all_api_pages(self, get):
        verses = [
            {"verse_number": number, "text_uthmani": f"ayah {number}"}
            for number in range(1, 8)
        ]
        get.side_effect = [
            mock.Mock(
                json=lambda: {
                    "verses": verses[:4],
                    "pagination": {"current_page": 1, "total_pages": 2},
                }
            ),
            mock.Mock(
                json=lambda: {
                    "verses": verses[4:],
                    "pagination": {"current_page": 2, "total_pages": 2},
                }
            ),
        ]

        result = fetch_surah_ayahs(1, "test-token")

        self.assertEqual(result, verses)
        self.assertEqual(get.call_count, 2)
        self.assertIn("/verses/by_chapter/1", get.call_args_list[0].args[0])
        self.assertEqual(get.call_args_list[0].kwargs["params"]["page"], 1)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["page"], 2)
        self.assertEqual(
            get.call_args_list[0].kwargs["headers"]["x-auth-token"],
            "test-token",
        )


if __name__ == "__main__":
    unittest.main()
