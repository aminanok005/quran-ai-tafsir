from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, update

from services.api.services.chat_message_store import (
    chat_message_retrievals,
    metadata,
    get_message_snapshot,
    store_message_snapshot,
)


def test_message_snapshot_is_stored_without_passage_text():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    browser_id, session_id, message_id = uuid4(), uuid4(), uuid4()
    source = {
        "source_id": "qf:168:1:1",
        "resource_id": 168,
        "verse_key": "1:1",
        "similarity": 0.82,
        "content_hash": "a" * 64,
        "scholar_id": "ibn_kathir",
        "scholar_name": "Tafsir Ibn Kathir",
        "volume": None,
        "page": None,
        "source_kind": "tafsir",
    }

    store_message_snapshot(
        engine,
        browser_id=browser_id,
        session_id=session_id,
        message_id=message_id,
        question="  What context should I study?  ",
        surah=1,
        ayah=1,
        selected_agent_ids=["ibn_kathir"],
        selected_source_ids=["qf:168:1:1"],
        source_snapshots=[source],
    )
    saved = get_message_snapshot(
        engine,
        browser_id=browser_id,
        session_id=session_id,
        message_id=message_id,
    )

    assert saved is not None
    assert saved["message_id"] == str(message_id)
    assert saved["question"] == "  What context should I study?  "
    assert saved["selected_agent_ids"] == ["ibn_kathir"]
    assert saved["sources"] == [source]
    assert "text" not in saved["sources"][0]
    assert "arabic_text" not in saved["sources"][0]


def test_message_snapshot_cannot_be_loaded_by_another_browser():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    browser_id, session_id, message_id = uuid4(), uuid4(), uuid4()
    store_message_snapshot(
        engine,
        browser_id=browser_id,
        session_id=session_id,
        message_id=message_id,
        question="A question",
        surah=1,
        ayah=1,
        selected_agent_ids=["ibn_kathir"],
        selected_source_ids=[],
        source_snapshots=[],
    )

    assert get_message_snapshot(
        engine,
        browser_id=uuid4(),
        session_id=session_id,
        message_id=message_id,
    ) is None


def test_message_snapshot_rejects_nonexistent_ayah_for_surah():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)

    with pytest.raises(ValueError, match="ayah location is out of range"):
        store_message_snapshot(
            engine,
            browser_id=uuid4(),
            session_id=uuid4(),
            message_id=uuid4(),
            question="A question",
            surah=1,
            ayah=8,
            selected_agent_ids=["ibn_kathir"],
            selected_source_ids=[],
            source_snapshots=[],
        )


def test_message_snapshot_rejects_source_text_fields():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)

    with pytest.raises(ValueError, match="source_text"):
        store_message_snapshot(
            engine,
            browser_id=uuid4(),
            session_id=uuid4(),
            message_id=uuid4(),
            question="A question",
            surah=1,
            ayah=1,
            selected_agent_ids=["ibn_kathir"],
            selected_source_ids=[],
            source_snapshots=[{
                "source_id": "qf:168:1:1",
                "resource_id": 168,
                "verse_key": "1:1",
                "similarity": 0.82,
                "content_hash": "a" * 64,
                "scholar_id": "ibn_kathir",
                "scholar_name": "Tafsir Ibn Kathir",
                "volume": None,
                "page": None,
                "source_kind": "tafsir",
                "source_text": "must not be persisted",
            }],
        )


def test_message_snapshot_read_rejects_persisted_source_text():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    browser_id, session_id, message_id = uuid4(), uuid4(), uuid4()
    store_message_snapshot(
        engine,
        browser_id=browser_id,
        session_id=session_id,
        message_id=message_id,
        question="A question",
        surah=1,
        ayah=1,
        selected_agent_ids=["ibn_kathir"],
        selected_source_ids=["qf:168:1:1"],
        source_snapshots=[{
            "source_id": "qf:168:1:1",
            "resource_id": 168,
            "verse_key": "1:1",
            "similarity": 0.82,
            "content_hash": "a" * 64,
            "scholar_id": "ibn_kathir",
            "scholar_name": "Tafsir Ibn Kathir",
            "volume": None,
            "page": None,
            "source_kind": "tafsir",
        }],
    )
    with engine.begin() as connection:
        connection.execute(
            update(chat_message_retrievals)
            .where(chat_message_retrievals.c.message_id == message_id)
            .values(source_snapshots=[{
                "source_id": "qf:168:1:1",
                "resource_id": 168,
                "verse_key": "1:1",
                "similarity": 0.82,
                "content_hash": "a" * 64,
                "scholar_id": "ibn_kathir",
                "scholar_name": "Tafsir Ibn Kathir",
                "volume": None,
                "page": None,
                "source_kind": "tafsir",
                "source_text": "must not be returned",
            }]),
        )

    with pytest.raises(RuntimeError, match="Stored source snapshot is invalid"):
        get_message_snapshot(
            engine,
            browser_id=browser_id,
            session_id=session_id,
            message_id=message_id,
        )


def test_migration_has_browser_scoped_snapshot_tables_and_expected_revision():
    migration = importlib.import_module(
        "services.api.migrations.versions.0004_chat_message_retrievals"
    )
    operations = MagicMock()
    assert migration.down_revision == "0003_tafsir_api_translations"

    with patch.object(migration, "op", operations):
        migration.upgrade()

    table_calls = {
        call.args[0]: call.args[1:]
        for call in operations.create_table.call_args_list
    }
    assert {"chat_sessions", "chat_message_retrievals"} <= table_calls.keys()

    session_columns = {
        column.name
        for column in table_calls["chat_sessions"]
        if hasattr(column, "name")
    }
    assert {"id", "browser_id"} <= session_columns

    message_columns = {
        column.name
        for column in table_calls["chat_message_retrievals"]
        if hasattr(column, "name")
    }
    assert {
        "message_id",
        "session_id",
        "browser_id",
        "question",
        "selected_agent_ids",
        "selected_source_ids",
        "source_snapshots",
    } <= message_columns

    created_index_names = {
        call.args[0] for call in operations.create_index.call_args_list
    }
    assert {
        "idx_chat_sessions_browser",
        "idx_chat_message_retrievals_browser_session",
    } <= created_index_names
