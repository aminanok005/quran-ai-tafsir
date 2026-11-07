"""Persist anonymous browser-scoped study notes."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_workspace_notes"
down_revision = "0001_initial_setup"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_notes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("browser_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text, nullable=False, server_default=""),
        sa.Column("surah_number", sa.SmallInteger),
        sa.Column("ayah_number", sa.SmallInteger),
        sa.Column("source_label", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("surah_number IS NULL OR surah_number BETWEEN 1 AND 114", name="ck_user_notes_surah"),
        sa.CheckConstraint("ayah_number IS NULL OR ayah_number BETWEEN 1 AND 286", name="ck_user_notes_ayah"),
    )
    op.create_index("idx_user_notes_browser_updated", "user_notes", ["browser_id", "updated_at"])
    op.execute(sa.text(
        "CREATE TRIGGER update_user_notes_updated_at "
        "BEFORE UPDATE ON user_notes FOR EACH ROW "
        "EXECUTE FUNCTION update_updated_at_column()"
    ))


def downgrade():
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_user_notes_updated_at ON user_notes"))
    op.drop_index("idx_user_notes_browser_updated", table_name="user_notes")
    op.drop_table("user_notes")
