import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from parser import (
    DEVELOPMENT_COLLECTION,
    DevelopmentProvenance,
    embedding_collection,
    is_production_eligible,
    parse_ayah_key,
    parse_json_file,
    parse_sqlite_file,
)


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.provenance = DevelopmentProvenance(
            source_id="local-tafsir",
            dataset="fixture.json",
            work="Example work",
            scholar="Example scholar",
        )

    def test_parse_ayah_key_is_strict(self):
        self.assertEqual(parse_ayah_key("2:255"), (2, 255))
        for value in ("0:1", "1:0", "115:1", "1", "1/x", "1:287"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_ayah_key(value)

    def test_json_preserves_raw_text_and_derives_normalized_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps({"1:1": {"text": "<p> بِسْمِ </p>"}}), encoding="utf-8")
            result = parse_json_file(path, self.provenance)
        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual(record.raw_text, "<p> بِسْمِ </p>")
        self.assertEqual(record.normalized_text, "بِسْمِ")
        self.assertIsNone(record.volume)
        self.assertIsNone(record.page)

    def test_json_reports_invalid_and_empty_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps({"bad": {"text": "x"}, "1:2": {"text": "  "}}), encoding="utf-8")
            result = parse_json_file(path, self.provenance)
        codes = {issue.code for issue in result.issues}
        self.assertIn("invalid_ayah_key", codes)
        self.assertIn("empty_text", codes)

    def test_json_reports_duplicate_object_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text('{"1:1":{"text":"first"},"1:1":{"text":"second"}}', encoding="utf-8")
            result = parse_json_file(path, self.provenance)
        self.assertIn("duplicate_key", {issue.code for issue in result.issues})

    def test_sqlite_preserves_provenance_and_rejects_duplicate_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.db"
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE tafsir (ayah_key TEXT, from_ayah TEXT, to_ayah TEXT, text TEXT)")
            connection.executemany(
                "INSERT INTO tafsir VALUES (?, ?, ?, ?)",
                [("2:1", "2:1", "2:3", "<p>one</p>"), ("2:1", "", "", "duplicate")],
            )
            connection.commit()
            connection.close()
            result = parse_sqlite_file(path, self.provenance)
        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual((record.surah_number, record.ayah_start, record.ayah_end), (2, 1, 3))
        self.assertEqual(record.source_id, "local-tafsir")
        self.assertEqual(record.permission_status, "development_only")
        self.assertEqual(record.verification_status, "unverified")
        self.assertIn("duplicate_key", {issue.code for issue in result.issues})

    def test_development_records_are_isolated_from_production(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps({"1:1": "text"}), encoding="utf-8")
            record = parse_json_file(path, self.provenance).records[0]
        self.assertFalse(record.production_eligible)
        self.assertFalse(is_production_eligible(record))
        self.assertEqual(embedding_collection(record), DEVELOPMENT_COLLECTION)
        self.assertIsNone(record.license)
        self.assertIsNone(record.source_url)

    def test_provenance_rejects_automatic_status_promotion(self):
        with self.assertRaises(ValueError):
            DevelopmentProvenance("s1", "fixture", permission_status="approved")
        with self.assertRaises(ValueError):
            DevelopmentProvenance("s1", "fixture", verification_status="verified")
        with self.assertRaises(ValueError):
            DevelopmentProvenance("s1", "fixture", production_eligible=True)

    def test_sqlite_table_name_is_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.db"
            with self.assertRaises(ValueError):
                parse_sqlite_file(path, self.provenance, table='tafsir; DROP TABLE tafsir')


if __name__ == "__main__":
    unittest.main()
