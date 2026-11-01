import asyncio
import importlib.util
import sqlite3
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "services/ai-engine/agents/ibn-kathir/source_retrieval.py"
)
SPEC = importlib.util.spec_from_file_location("tafsir_source_retrieval", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SOURCE_RETRIEVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCE_RETRIEVAL)
IbnKathirSourceRetrieval = SOURCE_RETRIEVAL.IbnKathirSourceRetrieval


def _create_dataset(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """CREATE TABLE tafsir (
                ayah_key TEXT,
                group_ayah_key TEXT,
                from_ayah TEXT,
                to_ayah TEXT,
                ayah_keys TEXT,
                text TEXT
            )"""
        )
        connection.executemany(
            "INSERT INTO tafsir VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("1:1", "1:1", "1:1", "1:2", "1:1,1:2",
                 "<div lang='ar'><p>نص التفسير الأول</p></div>"),
                ("1:2", "1:1", "", "", "", ""),
                ("1:3", "1:3", "1:3", "1:3", "1:3", ""),
            ],
        )


def test_retrieves_exact_ayah_text_from_sqlite(tmp_path):
    database = tmp_path / "ar-tafsir-ibn-kathir.db"
    _create_dataset(database)
    retrieval = IbnKathirSourceRetrieval(str(database))

    sources = asyncio.run(retrieval.retrieve("1:1", {"ayah_id": "1:1"}, "ma'thur"))

    assert len(sources) == 1
    assert sources[0]["original_text"] == "نص التفسير الأول"
    assert sources[0]["source_backend"] == "qul_sqlite"
    assert sources[0]["ayah_range"] == "1:1-1:2"
    assert sources[0]["verified"] is False
    assert sources[0]["rights_status"] == "unknown"
    assert "grading" not in sources[0]


def test_uses_grouped_passage_for_ayah_without_own_text(tmp_path):
    database = tmp_path / "id-tafsir-as-saadi.db"
    _create_dataset(database)
    retrieval = IbnKathirSourceRetrieval(str(database))

    sources = asyncio.run(retrieval.retrieve("1:2", {"ayah_id": "1:2"}, "ma'thur"))

    assert len(sources) == 1
    assert sources[0]["ayah_key"] == "1:2"
    assert sources[0]["group_ayah_key"] == "1:1"
    assert sources[0]["ayah_range"] == "1:1-1:2"
    assert sources[0]["language"] == "id"


def test_empty_or_invalid_records_do_not_create_citations(tmp_path):
    database = tmp_path / "ar-tafsir-ibn-kathir.db"
    _create_dataset(database)
    retrieval = IbnKathirSourceRetrieval(str(database))

    assert asyncio.run(retrieval.retrieve("1:3", {}, "ma'thur")) == []

    try:
        asyncio.run(retrieval.retrieve("0:1", {}, "ma'thur"))
    except ValueError as error:
        assert "Invalid Quran ayah key" in str(error)
    else:
        raise AssertionError("Invalid ayah keys must be rejected")
