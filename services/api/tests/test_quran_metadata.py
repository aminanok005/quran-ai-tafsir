import unittest

from services.api.services.quran_metadata import (
    SURAH_AYAH_COUNTS,
    is_valid_ayah,
    validate_surah_ayah_counts,
)


class QuranMetadataTests(unittest.TestCase):
    def test_canonical_counts_have_expected_shape_and_boundaries(self):
        self.assertEqual(len(SURAH_AYAH_COUNTS), 114)
        self.assertTrue(all(type(count) is int and count > 0 for count in SURAH_AYAH_COUNTS))
        self.assertEqual(sum(SURAH_AYAH_COUNTS), 6236)
        self.assertEqual(SURAH_AYAH_COUNTS[0], 7)
        self.assertEqual(SURAH_AYAH_COUNTS[1], 286)
        self.assertEqual(SURAH_AYAH_COUNTS[113], 6)

    def test_validator_rejects_non_positive_and_boolean_counts(self):
        invalid_counts = [(0, 7), (-1, 8), (True, 6)]

        for invalid_count, adjustment in invalid_counts:
            counts = list(SURAH_AYAH_COUNTS)
            counts[0] = invalid_count
            counts[1] += adjustment
            with self.subTest(first_count=invalid_count):
                with self.assertRaises(ValueError):
                    validate_surah_ayah_counts(counts)

    def test_is_valid_ayah_checks_surah_and_ayah_boundaries(self):
        self.assertTrue(is_valid_ayah(1, 1))
        self.assertTrue(is_valid_ayah(1, 7))
        self.assertFalse(is_valid_ayah(1, 8))
        self.assertTrue(is_valid_ayah(114, 6))
        self.assertFalse(is_valid_ayah(114, 7))
        self.assertFalse(is_valid_ayah(0, 1))
        self.assertFalse(is_valid_ayah(115, 1))
        self.assertFalse(is_valid_ayah(1, 0))
        self.assertFalse(is_valid_ayah(True, 1))


if __name__ == "__main__":
    unittest.main()
