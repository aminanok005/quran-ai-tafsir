"""Initial database setup for QURAN AI

This migration creates the core database schema for the QURAN AI Super WebApp.
It includes tables for Quran data, Tafsir passages, agents, citations, and user data.

Revision ID: 0001_initial_setup
Creates: quran_ayahs, tafsir_passages, agents, citations, users, etc.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid

# revision identifiers
revision = '0001_initial_setup'
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    # Enable pgvector extension
    op.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Create enum types
    op.execute(text("""
        CREATE TYPE surah_type AS ENUM ('meccan', 'medinan');
        CREATE TYPE language AS ENUM ('ar', 'th', 'en', 'ur');
        CREATE TYPE evidence_level AS ENUM ('verified', 'source_attributed', 'scholarly_difference', 'unverified', 'ai_synthesis');
        CREATE TYPE agent_type AS ENUM ('ibn_kathir', 'al_tabari', 'al_qurtubi', 'ibn_ashur', 'al_saadi', 'al_zuhayli');
        CREATE TYPE methodology AS ENUM (\"ma'thur\", 'ra'y', 'linguistic', 'legal', 'contemporary');
        CREATE TYPE hadith_grade AS ENUM ('sahih', 'hasan', 'daif', 'maudu');
        CREATE TYPE user_role AS ENUM ('reader', 'student', 'researcher', 'scholar', 'content_admin', 'platform_admin');
    """))

    # Create index for vector similarity search
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_tafsir_passages_embedding 
        ON tafsir_passages 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """))

    # Create full-text search index
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_tafsir_passages_arabic_fts
        ON tafsir_passages
        USING gin(to_tsvector('arabic', arabic_text));
    """))

    # Create quran_ayahs table
    op.create_table('quran_ayahs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('surah_number', sa.Integer, nullable=False),
        sa.Column('ayah_number', sa.Integer, nullable=False),
        sa.Column('text_uthmani', sa.Text, nullable=False),
        sa.Column('text_simple', sa.Text),
        sa.Column('text_complex', sa.Text),
        sa.Column('text_indopak', sa.Text),
        sa.Column('juz_number', sa.Integer),
        sa.Column('hizb_number', sa.Integer),
        sa.Column('rub_el_hizb_number', sa.Integer),
        sa.Column('page_number', sa.Integer),
        sa.Column('sajdah', sa.Boolean, server_default='false'),
        sa.Column('sajdah_number', sa.Integer),
        sa.Column('text_checksum', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('uq_quran_ayah', 'surah_number', 'ayah_number'),
    )

    # Create translations table
    op.create_table('translations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('ayah_id', sa.Integer, sa.ForeignKey('quran_ayahs.id', on_delete=sa.cascade)),
        sa.Column('language', postgresql.ENUM('ar', 'th', 'en', 'ur', name='language'), nullable=False),
        sa.Column('translation_id', sa.Integer, nullable=False),
        sa.Column('author_name', sa.String),
        sa.Column('author_name_ar', sa.String),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('source', sa.String),
        sa.Column('license', sa.String),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create scholars table
    op.create_table('scholars',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('scholar_id', sa.String, unique=True, nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('name_ar', sa.String),
        sa.Column('school', sa.String),
        sa.Column('birth_year', sa.Integer),
        sa.Column('death_year', sa.Integer),
        sa.Column('book_count', sa.Integer, server_default='0'),
        sa.Column('main_works', sa.JSON),
        sa.Column('biography', sa.Text),
        sa.Column('license', sa.String),
        sa.Column('source_url', sa.String),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create tafsir_books table
    op.create_table('tafsir_books',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('book_id', sa.String, unique=True, nullable=False),
        sa.Column('scholar_id', sa.UUID, sa.ForeignKey('scholars.id')),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('title_ar', sa.String),
        sa.Column('edition', sa.String),
        sa.Column('publisher', sa.String),
        sa.Column('volume', sa.Integer),
        sa.Column('page', sa.Integer),
        sa.Column('license', sa.String),
        sa.Column('source_url', sa.String),
        sa.Column('language', postgresql.ENUM('ar', 'en', 'ur', name='language'), nullable=False),
        sa.Column('verified', sa.Boolean, server_default='false'),
        sa.Column('metadata', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create tafsir_passages table
    op.create_table('tafsir_passages',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('book_id', sa.UUID, sa.ForeignKey('tafsir_books.id'), nullable=False),
        sa.Column('surah_number', sa.Integer, nullable=False),
        sa.Column('ayah_start', sa.Integer, nullable=False),
        sa.Column('ayah_end', sa.Integer, nullable=False),
        sa.Column('arabic_text', sa.Text, nullable=False),
        sa.Column('thai_translation', sa.Text),
        sa.Column('english_translation', sa.Text),
        sa.Column('volume', sa.Integer),
        sa.Column('page', sa.Integer),
        sa.Column('edition', sa.String),
        sa.Column('source_url', sa.String),
        sa.Column('hadith_references', sa.JSON),
        sa.Column('evidence_grade', postgresql.ENUM('sahih', 'hasan', 'daif', 'maudu', name='hadith_grade')),
        sa.Column('embedding', postgresql.VECTOR(1536)),
        sa.Column('verification_status', postgresql.ENUM('verified', 'source_attributed', 'scholarly_difference', 'unverified', 'ai_synthesis', name='evidence_level'), server_default='unverified'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String, unique=True, nullable=False),
        sa.Column('email', sa.String, unique=True, nullable=False),
        sa.Column('password_hash', sa.String, nullable=False),
        sa.Column('role', postgresql.ENUM('reader', 'student', 'researcher', 'scholar', 'content_admin', 'platform_admin', name='user_role'), server_default='reader'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('preferences', sa.JSON, server_default='{}'),
        sa.Column('profile', sa.JSON, server_default='{}'),
        sa.Column('stripe_customer_id', sa.String),
        sa.Column('stripe_subscription_status', sa.String, server_default='none'),
        sa.Column('streak_count', sa.Integer, server_default='0'),
        sa.Column('last_active_date', sa.DateTime(timezone=True)),
        sa.Column('gems_wallet', sa.Integer, server_default='0'),
        sa.Column('hearts_count', sa.Integer, server_default='5'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create bookmarks table
    op.create_table('bookmarks',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('surah_number', sa.Integer, nullable=False),
        sa.Column('ayah_number', sa.Integer, nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('uq_user_ayah_bookmark', 'user_id', 'surah_number', 'ayah_number'),
    )

    # Create reading_progress table
    op.create_table('reading_progress',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('ayah_id', sa.Integer, sa.ForeignKey('quran_ayahs.id'), nullable=False),
        sa.Column('last_read', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('progress_percentage', sa.Float, server_default='0.0'),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create agent_executions table
    op.create_table('agent_executions',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', sa.UUID, sa.ForeignKey('scholars.id'), nullable=False),
        sa.Column('ayah_id', sa.Integer, sa.ForeignKey('quran_ayahs.id'), nullable=False),
        sa.Column('context', sa.JSON, nullable=False),
        sa.Column('sources', sa.JSON, server_default='[]'),
        sa.Column('output', sa.JSON, nullable=False),
        sa.Column('citations', sa.JSON, server_default='[]'),
        sa.Column('quality_score', sa.Float, server_default='0.0'),
        sa.Column('llm_provider', sa.String),
        sa.Column('llm_model', sa.String),
        sa.Column('token_usage', sa.JSON, server_default='{}'),
        sa.Column('execution_time', sa.Float, server_default='0.0'),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create flashcards table
    op.create_table('flashcards',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('surah_number', sa.Integer, nullable=False),
        sa.Column('ayah_number', sa.Integer, nullable=False),
        sa.Column('front_text_ar', sa.Text, nullable=False),
        sa.Column('back_translation', sa.Text, nullable=False),
        sa.Column('root_word', sa.String),
        sa.Column('key_tafsir_note', sa.Text),
        sa.Column('is_favorite', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create quiz_sessions table
    op.create_table('quiz_sessions',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('surah_number', sa.Integer, nullable=False),
        sa.Column('total_questions', sa.Integer, nullable=False),
        sa.Column('score', sa.Integer, nullable=False),
        sa.Column('time_spent_seconds', sa.Integer, server_default='0'),
        sa.Column('question_breakdown', sa.JSON, nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create indexes for performance
    op.execute(text("CREATE INDEX idx_quran_ayahs_composite ON quran_ayahs(surah_number, ayah_number)"))
    op.execute(text("CREATE INDEX idx_tafsir_passages_ayah ON tafsir_passages(surah_number, ayah_start, ayah_end)"))
    op.execute(text("CREATE INDEX idx_tafsir_passages_verification ON tafsir_passages(verification_status)"))
    op.execute(text("CREATE INDEX idx_users_stripe ON users(stripe_subscription_status)"))
    op.execute(text("CREATE INDEX idx_flashcards_user ON flashcards(user_id, is_favorite)"))
    op.execute(text("CREATE INDEX idx_bookmarks_user ON bookmarks(user_id)"))

    # Add foreign key constraints with proper naming
    op.create_foreign_key('fk_tafsir_books_scholar', 'tafsir_books', 'scholars', ['scholar_id'], ['id'])
    op.create_foreign_key('fk_tafsir_passages_book', 'tafsir_passages', 'tafsir_books', ['book_id'], ['id'])
    op.create_foreign_key('fk_translations_ayah', 'translations', 'quran_ayahs', ['ayah_id'], ['id'])
    op.create_foreign_key('fk_bookmarks_user', 'bookmarks', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_bookmarks_ayah', 'bookmarks', 'quran_ayahs', ['surah_number', 'ayah_number'], ['id', 'id'])
    op.create_foreign_key('fk_reading_progress_user', 'reading_progress', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_reading_progress_ayah', 'reading_progress', 'quran_ayahs', ['ayah_id'], ['id'])
    op.create_foreign_key('fk_agent_executions_scholar', 'agent_executions', 'scholars', ['agent_id'], ['id'])
    op.create_foreign_key('fk_agent_executions_ayah', 'agent_executions', 'quran_ayahs', ['ayah_id'], ['id'])
    op.create_foreign_key('fk_flashcards_user', 'flashcards', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_quiz_sessions_user', 'quiz_sessions', 'users', ['user_id'], ['id'])

    # Create trigger to update updated_at timestamps
    op.execute(text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """))

    # Apply the trigger to relevant tables
    op.execute(text("""
        CREATE TRIGGER update_quran_ayahs_updated_at
        BEFORE UPDATE ON quran_ayahs
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """))

    op.execute(text("""
        CREATE TRIGGER update_tafsir_books_updated_at
        BEFORE UPDATE ON tafsir_books
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """))

    op.execute(text("""
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """))

    op.execute(text("""
        CREATE TRIGGER update_flashcards_updated_at
        BEFORE UPDATE ON flashcards
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """))

def downgrade():
    # Drop triggers first
    op.execute(text("DROP TRIGGER IF EXISTS update_quran_ayahs_updated_at ON quran_ayahs"))
    op.execute(text("DROP TRIGGER IF EXISTS update_tafsir_books_updated_at ON tafsir_books"))
    op.execute(text("DROP TRIGGER IF EXISTS update_users_updated_at ON users"))
    op.execute(text("DROP TRIGGER IF EXISTS update_flashcards_updated_at ON flashcards"))

    # Drop function
    op.execute(text("DROP FUNCTION IF EXISTS update_updated_at_column()"))

    # Drop indexes
    op.execute(text("DROP INDEX IF EXISTS idx_quran_ayahs_composite"))
    op.execute(text("DROP INDEX IF EXISTS idx_tafsir_passages_ayah"))
    op.execute(text("DROP INDEX IF EXISTS idx_tafsir_passages_verification"))
    op.execute(text("DROP INDEX IF EXISTS idx_users_stripe"))
    op.execute(text("DROP INDEX IF EXISTS idx_flashcards_user"))
    op.execute(text("DROP INDEX IF EXISTS idx_bookmarks_user"))

    # Drop foreign key constraints
    op.execute(text("ALTER TABLE tafsir_passages DROP CONSTRAINT IF EXISTS fk_tafsir_passages_book"))
    op.execute(text("ALTER TABLE translations DROP CONSTRAINT IF EXISTS fk_translations_ayah"))
    op.execute(text("ALTER TABLE bookmarks DROP CONSTRAINT IF EXISTS fk_bookmarks_user"))
    op.execute(text("ALTER TABLE bookmarks DROP CONSTRAINT IF EXISTS fk_bookmarks_ayah"))
    op.execute(text("ALTER TABLE reading_progress DROP CONSTRAINT IF EXISTS fk_reading_progress_user"))
    op.execute(text("ALTER TABLE reading_progress DROP CONSTRAINT IF EXISTS fk_reading_progress_ayah"))
    op.execute(text("ALTER TABLE agent_executions DROP CONSTRAINT IF EXISTS fk_agent_executions_scholar"))
    op.execute(text("ALTER TABLE agent_executions DROP CONSTRAINT IF EXISTS fk_agent_executions_ayah"))
    op.execute(text("ALTER TABLE flashcards DROP CONSTRAINT IF EXISTS fk_flashcards_user"))
    op.execute(text("ALTER TABLE quiz_sessions DROP CONSTRAINT IF EXISTS fk_quiz_sessions_user"))

    # Drop tables in reverse order (child tables first)
    op.drop_table('quiz_sessions')
    op.drop_table('flashcards')
    op.drop_table('agent_executions')
    op.drop_table('reading_progress')
    op.drop_table('bookmarks')
    op.drop_table('users')
    op.drop_table('tafsir_passages')
    op.drop_table('tafsir_books')
    op.drop_table('scholars')
    op.drop_table('translations')
    op.drop_table('quran_ayahs')

    # Drop custom types
    op.execute(text("DROP TYPE IF EXISTS surah_type"))
    op.execute(text("DROP TYPE IF EXISTS language"))
    op.execute(text("DROP TYPE IF EXISTS evidence_level"))
    op.execute(text("DROP TYPE IF EXISTS agent_type"))
    op.execute(text("DROP TYPE IF EXISTS methodology"))
    op.execute(text("DROP TYPE IF EXISTS hadith_grade"))
    op.execute(text("DROP TYPE IF EXISTS user_role"))

    # Drop vector extension
    op.execute(text("DROP EXTENSION IF EXISTS vector"))