"""Persist browser-owned chat message retrieval metadata."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_chat_message_retrievals"
down_revision = "0003_tafsir_api_translations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chat_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("browser_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("id", "browser_id", name="uq_chat_sessions_id_browser"),
    )
    op.create_index(
        "idx_chat_sessions_browser",
        "chat_sessions",
        ["browser_id"],
    )

    op.create_table(
        "chat_message_retrievals",
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("browser_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("ayah_number", sa.SmallInteger, nullable=False),
        sa.Column(
            "selected_agent_ids",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "selected_source_ids",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "source_snapshots",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id", "browser_id"],
            ["chat_sessions.id", "chat_sessions.browser_id"],
            name="fk_chat_message_retrievals_session_browser",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "surah_number BETWEEN 1 AND 114",
            name="ck_chat_retrieval_surah",
        ),
        sa.CheckConstraint(
            "ayah_number BETWEEN 1 AND 286",
            name="ck_chat_retrieval_ayah",
        ),
    )
    op.create_index(
        "idx_chat_message_retrievals_browser_session",
        "chat_message_retrievals",
        ["browser_id", "session_id", "message_id"],
    )


def downgrade():
    op.drop_index(
        "idx_chat_message_retrievals_browser_session",
        table_name="chat_message_retrievals",
    )
    op.drop_table("chat_message_retrievals")
    op.drop_index("idx_chat_sessions_browser", table_name="chat_sessions")
    op.drop_table("chat_sessions")
