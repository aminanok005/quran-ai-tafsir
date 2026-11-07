import json
import unittest
from contextlib import contextmanager
from uuid import uuid4

from parser import DevelopmentProvenance, parse_json_payload
from postgres import (
    VECTOR_DIMENSIONS,
    _INSERT_SOURCE_PERMISSION,
    _SELECT_BOOK,
    _SELECT_SOURCE_PERMISSION,
    _UPSERT_BOOK,
    _UPSERT_PASSAGE,
    _UPSERT_SCHOLAR,
    build_development_record_parameters,
    upsert_development_records,
)


class PostgresIngestionMappingTests(unittest.TestCase):
    def setUp(self):
        provenance = DevelopmentProvenance(
            source_id="source-1",
            dataset="fixture.json",
            work="Example work",
            scholar="Example scholar",
            source_url="https://example.test/source",
        )
        self.record = parse_json_payload({"1:1": "<p>text</p>"}, provenance).records[0]
        self.embedding = [0.25] * VECTOR_DIMENSIONS

    def test_mapping_preserves_raw_source_and_never_promotes_status(self):
        mapped = build_development_record_parameters(
            self.record,
            self.embedding,
            scholar_id="example_scholar",
            scholar_name="Example scholar",
            book_title="Example tafsir",
        )
        self.assertEqual(mapped["passage"]["arabic_text"], "<p>text</p>")
        self.assertEqual(mapped["passage"]["surah_number"], 1)
        self.assertEqual(mapped["passage"]["ayah_start"], 1)
        metadata = json.loads(mapped["book"]["metadata"])
        self.assertEqual(metadata["permission_status"], "development_only")
        self.assertEqual(metadata["verification_status"], "unverified")
        self.assertFalse(metadata["production_eligible"])

    def test_record_identifiers_are_deterministic(self):
        arguments = {
            "scholar_id": "example_scholar",
            "scholar_name": "Example scholar",
            "book_title": "Example tafsir",
        }
        first = build_development_record_parameters(self.record, self.embedding, **arguments)
        second = build_development_record_parameters(self.record, self.embedding, **arguments)
        self.assertEqual(first["passage"]["id"], second["passage"]["id"])
        self.assertEqual(first["book"]["id"], second["book"]["id"])

    def test_invalid_embedding_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            build_development_record_parameters(
                self.record,
                [0.1],
                scholar_id="example_scholar",
                scholar_name="Example scholar",
                book_title="Example tafsir",
            )

    def test_non_finite_embedding_values_are_rejected(self):
        embedding = [0.1] * VECTOR_DIMENSIONS
        embedding[0] = float("nan")
        with self.assertRaises(ValueError):
            build_development_record_parameters(
                self.record,
                embedding,
                scholar_id="example_scholar",
                scholar_name="Example scholar",
                book_title="Example tafsir",
            )

    def test_batch_upserts_shared_metadata_once(self):
        scholar_uuid, book_uuid, passage_uuid = uuid4(), uuid4(), uuid4()

        class FakeResult:
            def __init__(self, value=None, row=None):
                self.value = value
                self.row = row

            def mappings(self):
                return self

            def first(self):
                return self.row

            def scalar_one_or_none(self):
                return self.value

        class FakeConnection:
            def __init__(self):
                self.statements = []

            def execute(self, statement, _parameters):
                self.statements.append(statement)
                if statement is _UPSERT_SCHOLAR:
                    return FakeResult(scholar_uuid)
                if statement is _UPSERT_BOOK:
                    return FakeResult(book_uuid)
                if statement is _UPSERT_PASSAGE:
                    return FakeResult(passage_uuid)
                return FakeResult()

        connection = FakeConnection()

        class FakeEngine:
            @contextmanager
            def begin(self):
                yield connection

        second_record = parse_json_payload(
            {"1:2": "second passage"},
            DevelopmentProvenance("source-1", "fixture.json", "Example work", "Example scholar"),
        ).records[0]
        count = upsert_development_records(
            FakeEngine(),
            [(self.record, self.embedding), (second_record, self.embedding)],
            scholar_id="example_scholar",
            scholar_name="Example scholar",
            book_title="Example tafsir",
        )

        self.assertEqual(count, 2)
        self.assertEqual(connection.statements.count(_UPSERT_SCHOLAR), 1)
        self.assertEqual(connection.statements.count(_UPSERT_BOOK), 1)
        self.assertEqual(connection.statements.count(_INSERT_SOURCE_PERMISSION), 1)
        self.assertEqual(connection.statements.count(_UPSERT_PASSAGE), 2)
        self.assertEqual(connection.statements.count(_SELECT_BOOK), 1)
        self.assertEqual(connection.statements.count(_SELECT_SOURCE_PERMISSION), 1)

    def test_ingestion_refuses_existing_approved_book(self):
        class FakeResult:
            def mappings(self):
                return self

            def first(self):
                return {
                    "permission_status": "approved",
                    "verification_status": "verified",
                }

        class FakeConnection:
            def execute(self, *_args):
                return FakeResult()

        class FakeEngine:
            @contextmanager
            def begin(self):
                yield FakeConnection()

        with self.assertRaisesRegex(ValueError, "non-development"):
            upsert_development_records(
                FakeEngine(),
                [(self.record, self.embedding)],
                scholar_id="example_scholar",
                scholar_name="Example scholar",
                book_title="Example tafsir",
            )


if __name__ == "__main__":
    unittest.main()
