"""Initial canonical development schema.

Revision ID: 0001_initial_setup
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import VECTOR

revision = "0001_initial_setup"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Extensions must precede UUID defaults and vector columns.
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Types must precede columns that reference them.
    op.execute(sa.text("""
        CREATE TYPE surah_type AS ENUM ('meccan', 'medinan');
        CREATE TYPE language AS ENUM ('ar', 'th', 'en', 'ur');
        CREATE TYPE evidence_level AS ENUM (
            'verified', 'source_attributed', 'scholarly_difference',
            'unverified', 'ai_synthesis'
        );
        CREATE TYPE agent_type AS ENUM (
            'ibn_kathir', 'al_tabari', 'al_qurtubi',
            'ibn_ashur', 'al_saadi', 'al_zuhayli'
        );
        CREATE TYPE methodology AS ENUM (
            'ma''thur', 'ra''y', 'linguistic', 'legal', 'contemporary'
        );
        CREATE TYPE hadith_grade AS ENUM ('sahih', 'hasan', 'daif', 'maudu');
        CREATE TYPE user_role AS ENUM (
            'reader', 'student', 'researcher', 'scholar',
            'content_admin', 'platform_admin'
        );
        CREATE TYPE permission_status AS ENUM (
            'pending', 'approved', 'rejected', 'suspended', 'development_only'
        );
        CREATE TYPE verification_status AS ENUM ('unverified', 'verified');
    """))

    op.create_table(
        "quran_ayahs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("surah_number", sa.Integer, nullable=False),
        sa.Column("ayah_number", sa.Integer, nullable=False),
        sa.Column("text_uthmani", sa.Text, nullable=False),
        sa.Column("text_simple", sa.Text),
        sa.Column("text_complex", sa.Text),
        sa.Column("text_indopak", sa.Text),
        sa.Column("juz_number", sa.Integer),
        sa.Column("hizb_number", sa.Integer),
        sa.Column("rub_el_hizb_number", sa.Integer),
        sa.Column("page_number", sa.Integer),
        sa.Column("sajdah", sa.Boolean, server_default=sa.text("false")),
        sa.Column("sajdah_number", sa.Integer),
        sa.Column("text_checksum", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("surah_number", "ayah_number", name="uq_quran_ayah"),
    )
    op.create_table(
        "translations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ayah_id", sa.Integer, sa.ForeignKey("quran_ayahs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", postgresql.ENUM(name="language", create_type=False), nullable=False),
        sa.Column("translation_id", sa.Integer, nullable=False),
        sa.Column("author_name", sa.String),
        sa.Column("author_name_ar", sa.String),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("source", sa.String),
        sa.Column("license", sa.String),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "scholars",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("scholar_id", sa.String, unique=True, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("name_ar", sa.String),
        sa.Column("school", sa.String),
        sa.Column("birth_year", sa.Integer),
        sa.Column("death_year", sa.Integer),
        sa.Column("book_count", sa.Integer, server_default="0"),
        sa.Column("main_works", sa.JSON),
        sa.Column("biography", sa.Text),
        sa.Column("license", sa.String),
        sa.Column("source_url", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "tafsir_books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("book_id", sa.String, unique=True, nullable=False),
        sa.Column("scholar_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scholars.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("title_ar", sa.String),
        sa.Column("edition", sa.String),
        sa.Column("publisher", sa.String),
        sa.Column("volume", sa.Integer),
        sa.Column("page", sa.Integer),
        sa.Column("license", sa.String),
        sa.Column("source_url", sa.Text),
        sa.Column("language", postgresql.ENUM(name="language", create_type=False), nullable=False),
        sa.Column("permission_status", postgresql.ENUM(name="permission_status", create_type=False), nullable=False, server_default="pending"),
        sa.Column("verification_status", postgresql.ENUM(name="verification_status", create_type=False), nullable=False, server_default="unverified"),
        sa.Column("verification_evidence", sa.Text),
        sa.Column("metadata", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "tafsir_passages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tafsir_books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.Integer, nullable=False),
        sa.Column("ayah_start", sa.Integer, nullable=False),
        sa.Column("ayah_end", sa.Integer, nullable=False),
        sa.Column("arabic_text", sa.Text, nullable=False),
        sa.Column("thai_translation", sa.Text),
        sa.Column("english_translation", sa.Text),
        sa.Column("volume", sa.Integer),
        sa.Column("page", sa.Integer),
        sa.Column("edition", sa.String),
        sa.Column("source_url", sa.Text),
        sa.Column("hadith_references", sa.JSON),
        sa.Column("evidence_grade", postgresql.ENUM(name="hadith_grade", create_type=False)),
        sa.Column("embedding", VECTOR(1536)),
        sa.Column("verification_status", postgresql.ENUM(name="evidence_level", create_type=False), nullable=False, server_default="unverified"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String, unique=True, nullable=False),
        sa.Column("email", sa.String, unique=True, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("role", postgresql.ENUM(name="user_role", create_type=False), server_default="reader"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("preferences", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("profile", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("stripe_customer_id", sa.String),
        sa.Column("stripe_subscription_status", sa.String, server_default="none"),
        sa.Column("streak_count", sa.Integer, server_default="0"),
        sa.Column("last_active_date", sa.DateTime(timezone=True)),
        sa.Column("gems_wallet", sa.Integer, server_default="0"),
        sa.Column("hearts_count", sa.Integer, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.Integer, nullable=False),
        sa.Column("ayah_number", sa.Integer, nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", "surah_number", "ayah_number", name="uq_user_ayah_bookmark"),
    )
    op.create_table(
        "reading_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ayah_id", sa.Integer, sa.ForeignKey("quran_ayahs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("last_read", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("progress_percentage", sa.Float, server_default="0.0"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "agent_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scholars.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ayah_id", sa.Integer, sa.ForeignKey("quran_ayahs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("context", sa.JSON, nullable=False),
        sa.Column("sources", sa.JSON, server_default=sa.text("'[]'")),
        sa.Column("output", sa.JSON, nullable=False),
        sa.Column("citations", sa.JSON, server_default=sa.text("'[]'")),
        sa.Column("quality_score", sa.Float, server_default="0.0"),
        sa.Column("llm_provider", sa.String),
        sa.Column("llm_model", sa.String),
        sa.Column("token_usage", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("execution_time", sa.Float, server_default="0.0"),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "flashcards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.Integer, nullable=False),
        sa.Column("ayah_number", sa.Integer, nullable=False),
        sa.Column("front_text_ar", sa.Text, nullable=False),
        sa.Column("back_translation", sa.Text, nullable=False),
        sa.Column("root_word", sa.String),
        sa.Column("key_tafsir_note", sa.Text),
        sa.Column("is_favorite", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "quiz_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.Integer, nullable=False),
        sa.Column("total_questions", sa.Integer, nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("time_spent_seconds", sa.Integer, server_default="0"),
        sa.Column("question_breakdown", sa.JSON, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "source_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.String(255), nullable=False, unique=True),
        sa.Column("source_url", sa.Text),
        sa.Column("license", sa.String(255)),
        sa.Column("permission_status", postgresql.ENUM(name="permission_status", create_type=False), nullable=False, server_default="pending"),
        sa.Column("verification_status", postgresql.ENUM(name="verification_status", create_type=False), nullable=False, server_default="unverified"),
        sa.Column("verification_evidence", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # All indexes follow their tables.
    op.create_index("idx_quran_ayahs_composite", "quran_ayahs", ["surah_number", "ayah_number"])
    op.create_index("idx_tafsir_passages_ayah", "tafsir_passages", ["surah_number", "ayah_start", "ayah_end"])
    op.create_index("idx_tafsir_passages_verification", "tafsir_passages", ["verification_status"])
    op.create_index("idx_users_stripe", "users", ["stripe_subscription_status"])
    op.create_index("idx_flashcards_user", "flashcards", ["user_id", "is_favorite"])
    op.create_index("idx_bookmarks_user", "bookmarks", ["user_id"])
    op.create_index("idx_source_permissions_status", "source_permissions", ["permission_status", "verification_status"])
    op.create_index("idx_source_permissions_url", "source_permissions", ["source_url"])
    op.execute(sa.text("CREATE INDEX idx_tafsir_passages_embedding ON tafsir_passages USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"))
    op.execute(sa.text("CREATE INDEX idx_tafsir_passages_arabic_fts ON tafsir_passages USING gin(to_tsvector('arabic', arabic_text))"))

    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
    for table in ("quran_ayahs", "tafsir_books", "tafsir_passages", "users", "flashcards", "source_permissions"):
        op.execute(sa.text(
            f"CREATE TRIGGER update_{table}_updated_at "
            f"BEFORE UPDATE ON {table} FOR EACH ROW "
            "EXECUTE FUNCTION update_updated_at_column()"
        ))


def downgrade():
    for table in ("source_permissions", "flashcards", "users", "tafsir_passages", "tafsir_books", "quran_ayahs"):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS update_updated_at_column()"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_tafsir_passages_arabic_fts"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_tafsir_passages_embedding"))
    for index in (
        "idx_source_permissions_url", "idx_source_permissions_status",
        "idx_bookmarks_user", "idx_flashcards_user", "idx_users_stripe",
        "idx_tafsir_passages_verification", "idx_tafsir_passages_ayah",
        "idx_quran_ayahs_composite",
    ):
        op.drop_index(index)
    for table in (
        "source_permissions", "quiz_sessions", "flashcards", "agent_executions",
        "reading_progress", "bookmarks", "users", "tafsir_passages",
        "tafsir_books", "scholars", "translations", "quran_ayahs",
    ):
        op.drop_table(table)
    for enum_name in (
        "verification_status", "permission_status", "user_role", "hadith_grade",
        "methodology", "agent_type", "evidence_level", "language", "surah_type",
    ):
        op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))
    op.execute(sa.text('DROP EXTENSION IF EXISTS "vector"'))
    op.execute(sa.text('DROP EXTENSION IF EXISTS "pgcrypto"'))
