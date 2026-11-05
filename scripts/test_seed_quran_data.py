import unittest

from scripts.seed_quran_data import normalize_ayah, validate_ayahs


class QuranSeederTests(unittest.TestCase):
    def test_normalize_ayah_maps_only_canonical_columns(self):
        ayah = normalize_ayah(
            2,
            {
                "number": 255,
                "text_uthmani": "آية",
                "text_simple": "ayah",
                "juz_number": 3,
                "sajdah": False,
            },
        )

        self.assertEqual(ayah["surah_number"], 2)
        self.assertEqual(ayah["ayah_number"], 255)
        self.assertEqual(ayah["text_uthmani"], "آية")
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


if __name__ == "__main__":
    unittest.main()
