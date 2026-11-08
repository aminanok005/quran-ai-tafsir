"""Persist browser-scoped chat message retrieval metadata without source text."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    MetaData,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from .quran_metadata import is_valid_ayah


metadata = MetaData()
_json_type = JSON().with_variant(JSONB(), "postgresql")

chat_sessions = Table(
    "chat_sessions",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("browser_id", Uuid(as_uuid=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("id", "browser_id", name="uq_chat_sessions_id_browser"),
    Index("idx_chat_sessions_browser", "browser_id"),
)

chat_message_retrievals = Table(
    "chat_message_retrievals",
    metadata,
    Column("message_id", Uuid(as_uuid=True), primary_key=True),
    Column("session_id", Uuid(as_uuid=True), nullable=False),
    Column("browser_id", Uuid(as_uuid=True), nullable=False),
    Column("question", Text, nullable=False),
    Column("surah_number", SmallInteger, nullable=False),
    Column("ayah_number", SmallInteger, nullable=False),
    Column("selected_agent_ids", _json_type, nullable=False),
    Column("selected_source_ids", _json_type, nullable=False),
    Column("source_snapshots", _json_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    ForeignKeyConstraint(
        ["session_id", "browser_id"],
        ["chat_sessions.id", "chat_sessions.browser_id"],
        name="fk_chat_message_retrievals_session_browser",
        ondelete="CASCADE",
    ),
    CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_chat_retrieval_surah"),
    CheckConstraint("ayah_number BETWEEN 1 AND 286", name="ck_chat_retrieval_ayah"),
    Index(
        "idx_chat_message_retrievals_browser_session",
        "browser_id",
        "session_id",
        "message_id",
    ),
)


class SourceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=255)
    resource_id: int = Field(gt=0)
    verse_key: str = Field(min_length=1, max_length=32)
    similarity: float = Field(ge=-1, le=1)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    scholar_id: str = Field(min_length=1, max_length=80)
    scholar_name: str = Field(min_length=1, max_length=255)
    volume: int | str | None = None
    page: int | str | None = None
    source_kind: Literal["tafsir", "neighboring_ayah", "asbab_al_nuzul"] = "tafsir"


def _uuid(value: UUID | str, field_name: str) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(value)
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError(f"{field_name} must be a UUID") from error


def _validate_ids(values: list[str], field_name: str) -> list[str]:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    return values


def _insert_session(engine: Engine, values: dict[str, UUID]) -> Any:
    if engine.dialect.name == "postgresql":
        return postgres_insert(chat_sessions).values(**values).on_conflict_do_nothing(
            index_elements=[chat_sessions.c.id]
        )
    if engine.dialect.name == "sqlite":
        return sqlite_insert(chat_sessions).values(**values).on_conflict_do_nothing(
            index_elements=[chat_sessions.c.id]
        )
    raise RuntimeError(f"Unsupported chat store database dialect: {engine.dialect.name}")


def store_message_snapshot(
    engine: Engine,
    *,
    browser_id: UUID | str,
    session_id: UUID | str,
    message_id: UUID | str,
    question: str,
    surah: int,
    ayah: int,
    selected_agent_ids: list[str],
    selected_source_ids: list[str],
    source_snapshots: list[SourceSnapshot | dict[str, Any]],
) -> None:
    """Persist only message/source identifiers and metadata for a browser-owned answer."""
    browser = _uuid(browser_id, "browser_id")
    session = _uuid(session_id, "session_id")
    message = _uuid(message_id, "message_id")
    if not question.strip():
        raise ValueError("question must not be empty")
    if not is_valid_ayah(surah, ayah):
        raise ValueError("ayah location is out of range")

    agents = _validate_ids(selected_agent_ids, "selected_agent_ids")
    sources = _validate_ids(selected_source_ids, "selected_source_ids")
    normalized_snapshots = [
        item if isinstance(item, SourceSnapshot) else SourceSnapshot.model_validate(item)
        for item in source_snapshots
    ]
    snapshot_ids = [item.source_id for item in normalized_snapshots]
    if len(set(snapshot_ids)) != len(snapshot_ids):
        raise ValueError("source_snapshots must not contain duplicate source IDs")
    if any(source_id not in sources for source_id in snapshot_ids):
        raise ValueError("source_snapshots must be limited to selected source IDs")

    values = {
        "message_id": message,
        "session_id": session,
        "browser_id": browser,
        "question": question,
        "surah_number": surah,
        "ayah_number": ayah,
        "selected_agent_ids": agents,
        "selected_source_ids": sources,
        "source_snapshots": [item.model_dump(mode="json") for item in normalized_snapshots],
    }

    with engine.begin() as connection:
        connection.execute(
            _insert_session(
                engine,
                {"id": session, "browser_id": browser},
            )
        )
        connection.execute(insert(chat_message_retrievals).values(**values))


def get_message_snapshot(
    engine: Engine,
    *,
    browser_id: UUID | str,
    session_id: UUID | str,
    message_id: UUID | str,
) -> dict[str, Any] | None:
    """Load one message only when all browser/session/message identifiers match."""
    browser = _uuid(browser_id, "browser_id")
    session = _uuid(session_id, "session_id")
    message = _uuid(message_id, "message_id")

    statement = select(chat_message_retrievals).where(
        chat_message_retrievals.c.browser_id == browser,
        chat_message_retrievals.c.session_id == session,
        chat_message_retrievals.c.message_id == message,
    )
    with engine.connect() as connection:
        row = connection.execute(statement).mappings().one_or_none()
    if row is None:
        return None

    try:
        selected_agent_ids = _validate_ids(row["selected_agent_ids"], "selected_agent_ids")
        selected_source_ids = _validate_ids(row["selected_source_ids"], "selected_source_ids")
        raw_sources = row["source_snapshots"]
        if not isinstance(raw_sources, list):
            raise ValueError("source_snapshots must be a list")
        sources = [
            SourceSnapshot.model_validate(item).model_dump(mode="json")
            for item in raw_sources
        ]
        if len({item["source_id"] for item in sources}) != len(sources):
            raise ValueError("source_snapshots must not contain duplicate source IDs")
        if any(item["source_id"] not in selected_source_ids for item in sources):
            raise ValueError("source_snapshots must be limited to selected source IDs")
    except (ValidationError, TypeError, ValueError):
        raise RuntimeError("Stored source snapshot is invalid") from None

    return {
        "message_id": str(row["message_id"]),
        "session_id": str(row["session_id"]),
        "browser_id": str(row["browser_id"]),
        "question": row["question"],
        "surah_number": row["surah_number"],
        "ayah_number": row["ayah_number"],
        "selected_agent_ids": selected_agent_ids,
        "selected_source_ids": selected_source_ids,
        "sources": sources,
    }


__all__ = [
    "SourceSnapshot",
    "chat_message_retrievals",
    "chat_sessions",
    "get_message_snapshot",
    "metadata",
    "store_message_snapshot",
]
