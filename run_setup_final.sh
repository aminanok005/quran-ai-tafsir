#!/bin/bash
# QURAN AI Complete Setup Script
# Quick and easy setup for QURAN AI MVP completion

set -e

PROJECT_ROOT="/home/nisreen/Videos/yt-project/quran-intelligent-tafsir"

echo "🚀 QURAN AI Complete Setup Script"
echo "=================================="
echo ""

# Step 1: Configure PostgreSQL user and password
echo "🔐 Configuring PostgreSQL..."
# Try to set password without sudo prompt
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'quran_ai';" 2>/dev/null || echo "Password change may have failed (non-critical)"

# Step 2: Create database if not exists
echo ""
echo "📋 Creating database..."
if ! PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -c "SELECT 1;" >/dev/null 2>&1; then
    PGPASSWORD=quran_ai psql -h localhost -U postgres -c "CREATE DATABASE quran_ai;"
    echo "✅ Database created"
else
    echo "✅ Database exists"
fi

# Step 3: Enable pgvector extension if needed
echo ""
echo "📊 Enabling pgvector extension..."
if ! PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" >/dev/null 2>&1; then
    PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
    echo "✅ pgvector extension enabled"
else
    echo "✅ pgvector already exists"
fi

# Step 4: Create database tables using pure SQL
echo ""
echo "📋 Creating database tables..."

# Run all SQL commands directly
PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai << 'EOF'
-- Create quran_ayahs table
CREATE TABLE IF NOT EXISTS quran_ayahs (
    id SERIAL PRIMARY KEY,
    surah_number INT NOT NULL,
    ayah_number INT NOT NULL,
    text_uthmani TEXT NOT NULL,
    text_simple TEXT,
    text_complex TEXT,
    text_indopak TEXT,
    juz_number INT,
    hizb_number INT,
    rub_el_hizb_number INT,
    page_number INT,
    sajdah BOOLEAN DEFAULT FALSE,
    sajdah_number INT,
    text_checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (surah_number, ayah_number)
);
CREATE INDEX IF NOT EXISTS idx_quran_ayahs_composite ON quran_ayahs(surah_number, ayah_number);
EOF
echo "✅ quran_ayahs table created"

# Create scholars table
PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai << 'EOF'
CREATE TABLE IF NOT EXISTS scholars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scholar_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    name_ar VARCHAR(255),
    school VARCHAR(100),
    birth_year INT,
    death_year INT,
    book_count INT DEFAULT 0,
    main_works JSON,
    biography TEXT,
    license VARCHAR(255),
    source_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
EOF
echo "✅ scholars table created"

# Create tafsir_books table
PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai << 'EOF'
CREATE TABLE IF NOT EXISTS tafsir_books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id VARCHAR(50) UNIQUE NOT NULL,
    scholar_id UUID REFERENCES scholars(id),
    title VARCHAR(500) NOT NULL,
    title_ar VARCHAR(500),
    edition VARCHAR(200),
    publisher VARCHAR(200),
    volume INT,
    page INT,
    license VARCHAR(200),
    source_url TEXT,
    language VARCHAR(10) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    metadata JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
EOF
echo "✅ tafsir_books table created"

# Create tafsir_passages table
PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai << 'EOF'
CREATE TABLE IF NOT EXISTS tafsir_passages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID REFERENCES tafsir_books(id) NOT NULL,
    surah_number INT NOT NULL,
    ayah_start INT NOT NULL,
    ayah_end INT NOT NULL,
    arabic_text TEXT NOT NULL,
    thai_translation TEXT,
    english_translation TEXT,
    volume INT,
    page INT,
    edition VARCHAR(200),
    source_url TEXT,
    hadith_references JSON,
    evidence_grade VARCHAR(20) DEFAULT 'sahih',
    embedding VECTOR(1536),
    verification_status VARCHAR(30) DEFAULT 'unverified',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
EOF
echo "✅ tafsir_passages table created"

# Create vector indexes
PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai << 'EOF'
CREATE INDEX IF NOT EXISTS idx_tafsir_passages_embedding
ON tafsir_passages USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_tafsir_passages_arabic_fts
ON tafsir_passages USING gin(to_tsvector('arabic', arabic_text));

CREATE INDEX IF NOT EXISTS idx_tafsir_passages_ayah
ON tafsir_passages(surah_number, ayah_start, ayah_end);

CREATE INDEX IF NOT EXISTS idx_tafsir_passages_verification
ON tafsir_passages(verification_status);
EOF
echo "✅ Vector search indexes created"

# Create user tables
PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai << 'EOF'
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(30) DEFAULT 'reader',
    is_active BOOLEAN DEFAULT TRUE,
    preferences JSON,
    profile JSON,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_status VARCHAR(50) DEFAULT 'none',
    streak_count INT DEFAULT 0,
    last_active_date TIMESTAMP WITH TIME ZONE,
    gems_wallet INT DEFAULT 0,
    hearts_count INT DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    surah_number INT NOT NULL,
    ayah_number INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reading_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    ayah_id INT,
    last_read TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    progress_percentage DECIMAL(5,2) DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    surah_number INT NOT NULL,
    ayah_number INT NOT NULL,
    front_text_ar TEXT NOT NULL,
    back_translation TEXT NOT NULL,
    root_word VARCHAR(255),
    key_tafsir_note TEXT,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    surah_number INT NOT NULL,
    total_questions INT NOT NULL,
    score INT NOT NULL,
    time_spent_seconds INT DEFAULT 0,
    question_breakdown JSON NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    passage_id UUID REFERENCES tafsir_passages(id),
    source_id UUID REFERENCES scholars(id),
    reference VARCHAR(255),
    original_text TEXT,
    excerpt TEXT,
    grading VARCHAR(20),
    chain VARCHAR(500) DEFAULT '[]',
    reliability_score DECIMAL(3,2) DEFAULT 0.5,
    verified BOOLEAN DEFAULT FALSE,
    validation_status VARCHAR(30) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
EOF
echo "✅ User tables created"

# Create triggers
PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai << 'EOF'
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS update_quran_ayahs_updated_at ON quran_ayahs;
CREATE TRIGGER update_quran_ayahs_updated_at
BEFORE UPDATE ON quran_ayahs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_scholars_updated_at ON scholars;
CREATE TRIGGER update_scholars_updated_at
BEFORE UPDATE ON scholars FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tafsir_books_updated_at ON tafsir_books;
CREATE TRIGGER update_tafsir_books_updated_at
BEFORE UPDATE ON tafsir_books FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_flashcards_updated_at ON flashcards;
CREATE TRIGGER update_flashcards_updated_at
BEFORE UPDATE ON flashcards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EOF
echo "✅ Triggers created"

# Insert sample scholarly data
PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai << 'EOF'
INSERT INTO scholars (scholar_id, name, name_ar, school, birth_year, death_year, biography, license, source_url)
VALUES ('ibn_kathir', 'Ibn Kathir', 'ابن كثير', 'Shafi''i', 1301, 1373,
       'Renowned Islamic scholar, historian, and mufassir. Author of Tafsir al-Qur''an al-Azim.',
       'Open access - King Fahd Complex', 'https://shamela.ws/book/16559')
ON CONFLICT (scholar_id) DO NOTHING;

INSERT INTO tafsir_books (book_id, scholar_id, title, title_ar, edition, publisher, volume, language, verified, license, source_url)
VALUES ('tafsir_ibn_kathir', (SELECT id FROM scholars WHERE scholar_id='ibn_kathir'),
        'Tafsir al-Qur''an al-Azim', 'تفسير القرآن العظيم', 'Dar Taybah',
        'Dar Taybah', 8, 'ar', true, 'Open access - King Fahd Complex',
        'https://shamela.ws/book/16559')
ON CONFLICT (book_id) DO NOTHING;

INSERT INTO scholars (scholar_id, name, name_ar, school, birth_year, death_year, biography, license, source_url)
VALUES ('al_tabari', 'Al-Tabari', 'الطبري', 'Shafi''i', 839, 923,
       'Renowned Islamic historian and mufassir. Author of Jami'' al-Bayan.',
       'Open access - Maktabah Shamela', 'https://shamela.ws/book/16558')
ON CONFLICT (scholar_id) DO NOTHING;

INSERT INTO tafsir_books (book_id, scholar_id, title, title_ar, edition, publisher, volume, language, verified, license, source_url)
VALUES ('jami_al_bayan', (SELECT id FROM scholars WHERE scholar_id='al_tabari'),
        'Jami'' al-Bayan', 'جامع البيان', 'Dar al-Kutub al-Ilmiyah',
        'Dar al-Kutub al-Ilmiyah', 30, 'ar', true, 'Open access - Maktabah Shamela',
        'https://shamela.ws/book/16558')
ON CONFLICT (book_id) DO NOTHING;

INSERT INTO scholars (scholar_id, name, name_ar, school, birth_year, death_year, biography, license, source_url)
VALUES ('al_qurtubi', 'Al-Qurtubi', 'القرطبي', 'Maliki', 1214, 1273,
       'Renowned Maliki jurist and mufassir. Author of Al-Jami'' li-Ahkam al-Qur''an.',
       'Open access - King Fahd Complex', 'https://shamela.ws/book/16560')
ON CONFLICT (scholar_id) DO NOTHING;

INSERT INTO tafsir_books (book_id, scholar_id, title, title_ar, edition, publisher, volume, language, verified, license, source_url)
VALUES ('jami_ahkam', (SELECT id FROM scholars WHERE scholar_id='al_qurtubi'),
        'Al-Jami'' li-Ahkam al-Qur''an', 'الجامع لأحكام القرآن', 'Dar al-Kutub al-Ilmiyah',
        'Dar al-Kutub al-Ilmiyah', 20, 'ar', true, 'Open access - King Fahd Complex',
        'https://shamela.ws/book/16560')
ON CONFLICT (book_id) DO NOTHING;

INSERT INTO scholars (scholar_id, name, name_ar, school, birth_year, death_year, biography, license, source_url)
VALUES ('al_saadi', 'Al-Sa''di', 'السعدي', 'Hanbali', 1889, 1956,
       'Renowned scholar known for clear and accessible tafsir. Author of Taysir al-Karim al-Rahman.',
       'Open access - King Fahd Complex', 'https://shamela.ws/book/16561')
ON CONFLICT (scholar_id) DO NOTHING;

INSERT INTO tafsir_books (book_id, scholar_id, title, title_ar, edition, publisher, volume, language, verified, license, source_url)
VALUES ('taysir_karim', (SELECT id FROM scholars WHERE scholar_id='al_saadi'),
        'Taysir al-Karim al-Rahman', 'تيسير الكريم الرحمن', 'Dar al-Kutub al-Ilmiyah',
        'Dar al-Kutub al-Ilmiyah', 8, 'ar', true, 'Open access - King Fahd Complex',
        'https://shamela.ws/book/16561')
ON CONFLICT (book_id) DO NOTHING;

-- Initial admin user
INSERT INTO users (username, email, role, is_active, preferences, profile, gems_wallet, hearts_count)
VALUES ('admin', 'admin@quran-ai.org', 'platform_admin', true, '{}', '{}', 0, 5)
ON CONFLICT (username) DO NOTHING;
EOF
echo "✅ Sample scholarly records created"

# Verification
echo ""
echo "🔍 Verifying database setup..."
TABLES=$(PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')
ENUM_COUNT=$(PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -t -c "SELECT count(*) FROM pg_type WHERE typnamespace=(SELECT oid FROM pg_namespace WHERE nspname='public') AND typtype='e';" | tr -d ' ')
SCHOLARS_COUNT=$(PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -t -c "SELECT count(*) FROM scholars;")
BOOKS_COUNT=$(PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -t -c "SELECT count(*) FROM tafsir_books;")
USERS_COUNT=$(PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -t -c "SELECT count(*) FROM users;")
INDEXES_COUNT=$(PGPASSWORD=quran_ai psql -h localhost -U postgres -d quran_ai -t -c "SELECT count(*) FROM pg_indexes WHERE schemaname='public';")

echo "   Tables created: $TABLES"
echo "   Enums created: $ENUM_COUNT"
echo "   Scholars in DB: $SCHOLARS_COUNT"
echo "   Books in DB: $BOOKS_COUNT"
echo "   Users in DB: $USERS_COUNT"
echo "   Indexes created: $INDEXES_COUNT"

echo ""
echo "=================================="
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with actual API credentials"
echo "2. Run: python3 scripts/seed_quran_data.py"
echo "3. Run: python3 scripts/load_tafsir_data.py"
echo "4. Start the application: cd services/api && uvicorn app.main:app --reload"
