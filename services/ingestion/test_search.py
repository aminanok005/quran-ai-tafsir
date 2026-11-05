import unittest
from dataclasses import replace

from parser import DevelopmentProvenance, parse_json_payload
from search import search_development


class DevelopmentSearchTests(unittest.TestCase):
    def setUp(self):
        provenance = DevelopmentProvenance("source-1", "fixture.json", "Work", "Scholar")
        self.records = parse_json_payload(
            {
                "1:1": "Mercy and guidance",
                "1:2": "Guidance for students",
                "2:1": "Different topic",
            },
            provenance,
        ).records

    def test_search_uses_normalized_text_and_returns_provenance(self):
        hits = search_development(self.records, "guidance")
        self.assertEqual([hit.record.source_key for hit in hits], ["1:1", "1:2"])
        self.assertEqual(hits[0].provenance["permission_status"], "development_only")
        self.assertEqual(hits[0].provenance["verification_status"], "unverified")
        self.assertFalse(hits[0].provenance["production_eligible"])
        self.assertEqual(hits[0].collection, "tafsir_development")

    def test_search_has_stable_limit_and_empty_query(self):
        self.assertEqual(search_development(self.records, ""), ())
        self.assertEqual(len(search_development(self.records, "guidance", limit=1)), 1)
        with self.assertRaises(ValueError):
            search_development(self.records, "guidance", limit=0)

    def test_search_rejects_non_development_record(self):
        record = replace(self.records[0], production_eligible=True)
        with self.assertRaises(ValueError):
            search_development((record,), "guidance")


if __name__ == "__main__":
    unittest.main()
