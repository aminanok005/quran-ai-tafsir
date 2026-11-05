#!/bin/bash
# Complete setup script for QURAN AI development environment
# This script handles all necessary setup steps including:
# - PostgreSQL installation and configuration
# - Python package installation
# - Database initialization
# - Environment file creation

set -e

PROJECT_ROOT="/home/nisreen/Videos/yt-project/quran-intelligent-tafsir"

echo "🚀 QURAN AI Complete Setup Script"
echo "=================================="
echo ""

# Step 1: Python packages
echo "📦 Step 1: Installing Python dependencies..."
pip3 install --break-system-packages sqlalchemy psycopg2-binary alembic fastapi python-dotenv requests

if [ $? -eq 0 ]; then
    echo "✅ Python packages installed"
else
    echo "❌ Failed to install Python packages"
    exit 1
fi

# Step 2: Database extension
echo ""
echo "📊 Step 2: Setting up PostgreSQL with pgvector..."

# Check if pgvector extension exists
if ! psql -h localhost -U postgres -d quran_ai -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" >/dev/null 2>&1; then
    sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
    echo "✅ pgvector extension enabled"
else
    echo "✅ pgvector already exists"
fi

# Step 3: Create database
echo ""
echo "📋 Step 3: Creating database..."

if ! psql -h localhost -U postgres -d quran_ai -c "SELECT 1;" >/dev/null 2>&1; then
    sudo -u postgres psql -c "CREATE DATABASE quran_ai OWNER postgres;"
    echo "✅ Database created"
else
    echo "✅ Database exists"
fi

# Configure user authentication
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'quran_ai';" 2>/dev/null || echo "Password update may have failed (non-critical)"

# Step 4: Run database setup
echo ""
echo "🚀 Step 4: Running database setup script..."

cd "$PROJECT_ROOT"
python3 setup_database.py

if [ $? -eq 0 ]; then
    echo "✅ Database setup completed"
else
    echo "❌ Database setup failed"
    echo "You can manually run: python3 setup_database.py"
    exit 1
fi

# Step 5: Environment configuration
echo ""
echo "🔐 Step 5: Configuring environment file..."

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    cp "$PROJECT_ROOT/.env.example.final" "$PROJECT_ROOT/.env"
    echo "✅ .env file created from template"
else
    echo "⚠️  .env already exists, skipping"
fi

# Step 6: Final verification
echo ""
echo "🔍 Step 6: Verifying environment..."

# Check Python
python3 -c "import sqlalchemy, psycopg2, fastapi, alembic, requests" && echo "✅ Python packages OK" || echo "❌ Python packages missing"

# Check database
psql -h localhost -U postgres -d quran_ai -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" >/dev/null 2>&1 && echo "✅ Database OK" || echo "❌ Database connection failed"

echo ""
echo "=================================="
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with actual API credentials"
echo "2. Run: python3 scripts/seed_quran_data.py"
echo "3. Run: python3 scripts/load_tafsir_data.py"
echo "4. Start the application: cd services/api && uvicorn app.main:app --reload"