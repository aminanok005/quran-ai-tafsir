import unittest
from dataclasses import replace

from embedding import build_development_embedding_document
from parser import DevelopmentProvenance, parse_json_payload


class DevelopmentEmbeddingTests(unittest.TestCase):
    def setUp(self):
        provenance = DevelopmentProvenance("source-1", "fixture.json", "Work", "Scholar")
        self.record = parse_json_payload({"1:1": "Mercy and guidance"}, provenance).records[0]

    def test_document_uses_development_collection_and_provenance(self):
        document = build_development_embedding_document(self.record)
        self.assertEqual(document.collection, "tafsir_development")
        self.assertEqual(document.text, "Mercy and guidance")
        self.assertEqual(document.metadata["permission_status"], "development_only")
        self.assertEqual(document.metadata["verification_status"], "unverified")
        self.assertEqual(document.metadata["ingestion_mode"], "development")
        self.assertFalse(document.metadata["production_eligible"])
        self.assertEqual(document.metadata["source_id"], "source-1")

    def test_document_rejects_promoted_record(self):
        with self.assertRaises(ValueError):
            build_development_embedding_document(replace(self.record, production_eligible=True))

    def test_document_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            build_development_embedding_document(replace(self.record, normalized_text=""))


if __name__ == "__main__":
    unittest.main()
