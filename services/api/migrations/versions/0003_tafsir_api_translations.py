"""Cache generated translations for live Quran Foundation Tafsir responses."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_tafsir_api_translations"
down_revision = "0002_workspace_notes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tafsir_api_translations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("resource_id", sa.Integer, nullable=False),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("ayah_number", sa.SmallInteger, nullable=False),
        sa.Column(
            "target_language",
            postgresql.ENUM(name="language", create_type=False),
            nullable=False,
            server_default="th",
        ),
        sa.Column("translated_text", sa.Text, nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("model", sa.String(255), nullable=False),
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
        sa.CheckConstraint("resource_id > 0", name="ck_tafsir_api_translation_resource"),
        sa.CheckConstraint(
            "surah_number BETWEEN 1 AND 114", name="ck_tafsir_api_translation_surah"
        ),
        sa.CheckConstraint("ayah_number BETWEEN 1 AND 286", name="ck_tafsir_api_translation_ayah"),
        sa.UniqueConstraint(
            "resource_id",
            "surah_number",
            "ayah_number",
            "target_language",
            "source_hash",
            name="uq_tafsir_api_translation_source",
        ),
    )
    op.create_index(
        "idx_tafsir_api_translation_ayah",
        "tafsir_api_translations",
        ["resource_id", "surah_number", "ayah_number", "target_language"],
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER update_tafsir_api_translations_updated_at "
            "BEFORE UPDATE ON tafsir_api_translations FOR EACH ROW "
            "EXECUTE FUNCTION update_updated_at_column()"
        )
    )


def downgrade():
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS update_tafsir_api_translations_updated_at "
            "ON tafsir_api_translations"
        )
    )
    op.drop_index(
        "idx_tafsir_api_translation_ayah",
        table_name="tafsir_api_translations",
    )
    op.drop_table("tafsir_api_translations")
