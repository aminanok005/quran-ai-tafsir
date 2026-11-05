# Database Setup Commands - Copy & Paste Ready

## 🚀 Complete Database Setup in 3 Steps

### **Step 1: Configure PostgreSQL Authentication (One-time)**
```bash
# 1. Find pg_hba.conf
sudo find /etc/postgresql -name "pg_hba.conf"

# 2. Edit to use 'trust' for local connections (requires sudo)
# Change these lines in /etc/postgresql/16/main/pg_hba.conf:
# local   all             postgres                                trust
# local   all             all                                     trust
# host    all             all             127.0.0.1/32            trust

# 3. Restart PostgreSQL
sudo systemctl restart postgresql
```

### **Step 2: Create Database & Tables (After restart)**
```bash
# Set port and database name
export PGPORT=5434
export PGDATABASE=quran_ai

# Create database
psql -h localhost -U postgres -c "CREATE DATABASE quran_ai OWNER postgres;"

# Enable pgvector
psql -U postgres -d quran_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create all tables
psql -d quran_ai << 'EOF'
-- quran_ayahs
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

-- scholars
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

-- tafsir_books
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

-- tafsir_passages
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

-- Vector index
CREATE INDEX IF NOT EXISTS idx_tafsir_passages_embedding
ON tafsir_passages USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Full-text search
CREATE INDEX IF NOT EXISTS idx_tafsir_passages_arabic_fts
ON tafsir_passages USING gin(to_tsvector('arabic', arabic_text));

-- Composite index
CREATE INDEX IF NOT EXISTS idx_tafsir_passages_ayah
ON tafsir_passages(surah_number, ayah_start, ayah_end);
EOF
```

---

## After Tables: Create User Tables
```bash
psql -d quran_ai << 'EOF'
-- Users
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

-- Bookmarks
CREATE TABLE IF NOT EXISTS bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    surah_number INT NOT NULL,
    ayah_number INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Reading Progress
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

-- Flashcards
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

-- Quiz Sessions
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

-- Citations
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
```

---

## Insert Sample Data
```bash
psql -d quran_ai << 'EOF'
-- Ibn Kathir
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

-- Al-Tabari
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

-- Al-Qurtubi
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

-- Al-Sa'di
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

-- Admin user
INSERT INTO users (username, email, role, is_active, preferences, profile, gems_wallet, hearts_count)
VALUES ('admin', 'admin@quran-ai.org', 'platform_admin', true, '{}', '{}', 0, 5)
ON CONFLICT (username) DO NOTHING;
EOF
```

---

## Verify Setup
```bash
psql -d quran_ai -c "SELECT COUNT(*) FROM scholars;"
psql -d quran_ai -c "SELECT COUNT(*) FROM tafsir_books;"
psql -d quran_ai -c "SELECT COUNT(*) FROM users;"
```