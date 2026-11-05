#!/bin/bash
# QURAN AI Development Environment Setup Script
# Installs all required dependencies for database setup and MVP completion

set -e

echo "🚀 QURAN AI Development Environment Setup"
echo "=========================================="

# Function to print status
print_status() {
    echo -e "\n✅ $1"
}

print_error() {
    echo -e "\n❌ $1"
}

# Check if running as root (for system package installation)
if [[ $EUID -eq 0 ]]; then
    echo "🔑 Running with root privileges"
    SUDO=""
else
    echo "⚠️  Not running as root - will need sudo for some packages"
    SUDO="sudo -E"
fi

# 1. Install PostgreSQL
print_status "Installing PostgreSQL database server..."
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq postgresql postgresql-contrib postgresql-server-dev-all

# Configure PostgreSQL authentication
print_status "Configuring PostgreSQL..."
$SUDO service postgresql start

# Set up PostgreSQL user for QURAN AI
$SUDO psql -c "ALTER USER postgres WITH PASSWORD 'quran_ai';" 2>/dev/null || echo "Password change may not be available"

# Create QURAN AI database user
$SUDO psql -c "CREATE DATABASE quran_ai OWNER postgres;" 2>/dev/null

# Enable pgvector extension
$SUDO psql -d quran_ai -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null

# 2. Install Python packages
print_status "Installing Python dependencies..."
$SUDO apt-get install -y -qq python3 python3-pip python3-dev libpq-dev python3-venv

print_status "Installing Python packages via pip..."
pip3 install --upgrade pip
pip3 install sqlalchemy==2.0.23 psycopg2-binary==2.9.9 alembic==1.13.1 fastapi==0.104.1 python-dotenv==1.0.0 requests==2.31.0 python-multipart==0.0.1

# 3. Verify installation
print_status "Verifying installation..."

# Check PostgreSQL
if command -v psql >/devdev/null; then
    echo "✅ PostgreSQL CLI available"
    # Test connection
    psql -h localhost -U postgres -c "SELECT 1;" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ PostgreSQL connection successful"
    else
        print_error "PostgreSQL connection failed"
    fi
else
    print_error "PostgreSQL not found"
fi

# Check Python packages
if python3 -c "import sqlalchemy" >/dev/null 2>&1; then
    echo "✅ SQLAlchemy installed"
else
    print_error "SQLAlchemy not installed"
fi

if python3 -c "import psycopg2" >/dev/null 2>&1; then
    echo "✅ psycopg2 installed"
else
    print_error "psycopg2 not installed"
fi

if python3 -c "import fastapi" >/dev/null 2>&1; then
    echo "✅ FastAPI installed"
else
    print_error "FastAPI not installed"
fi

if python3 -c "import alembic" >/dev/null 2>&1; then
    echo "✅ Alembic installed"
else
    print_error "Alembic not installed"
fi

if python3 -c "import requests" >/dev/null 2>&1; then
    echo "✅ requests installed"
else
    print_error "requests not installed"
fi

# 4. Create project directory structure
print_status "Creating project directory structure..."
mkdir -p /home/nisreen/Videos/yt-project/quran-intelligent-tafsir/scripts
mkdir -p /home/nisreen/Videos/yt-project/quran-intelligent-tafsir/data

# 5. Copy scripts
print_status "Copying setup scripts..."
cp /home/nisreen/Videos/yt-project/quran-intelligent-tafsir/scripts/load_tafsir_data.py /home/nisreen/Videos/yt-project/quran-intelligent-tafsir/scripts/ 2>/dev/null || echo "Script already exists"

# 6. Create .env file if it doesn't exist
if [ ! -f "/home/nisreen/Videos/yt-project/quran-intelligent-tafsir/.env" ]; then
    print_status "Creating .env file template..."
    cat > /home/nisreen/Videos/yt-project/quran-intelligent-tafsir/.env << EOL
# QURAN AI Database Configuration
# Update these values before running the application

# PostgreSQL Database
DATABASE_URL=postgresql+psycopg://quran_ai:quran_ai@localhost:5432/quran_ai

# Quran Foundation API
QURAN_API_BASE_URL=https://apis.quran.foundation
QURAN_API_CLIENT_ID=REPLACE_WITH_APPROVED_CLIENT_ID
QURAN_API_CLIENT_SECRET=REPLACE_WITH_SECRET
QURAN_API_TOKEN_CACHE_TTL_SECONDS=3300

# AI Provider Configuration
LLM_PROVIDER=OPENAI
LLM_API_BASE_URL=
LLM_API_KEY=REPLACE_ME
LLM_MODEL=gpt-4o

# Embedding Configuration
EMBEDDING_PROVIDER=OPENAI
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_API_KEY=REPLACE_ME

# Security
SECRET_KEY=GENERATE_A_LONG_RANDOM_SECRET
CORS_ORIGINS=http://localhost:3000

# Application Settings
APP_ENV=development
APP_NAME=QURAN AI
APP_DEFAULT_LOCALE=th
APP_SUPPORTED_LOCALES=th,ar,en
EOL
    echo "✅ .env file created"
else
    echo "⚠️  .env file already exists"
fi

# 7. Set up project ownership
print_status "Setting up project ownership..."
chown -R nisreen:nisreen /home/nisreen/Videos/yt-project/quran-intelligent-tafsir
chmod -R 755 /home/nisreen/Videos/yt-project/quran-intelligent-tafsir

# 8. Summary
print_status "Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with actual API credentials"
echo "   2. Run: python3 scripts/seed_quran_data.py"
echo "   3. Run: python3 scripts/load_tafsir_data.py"
echo "   4. Check database status: psql -h localhost -U postgres -d quran_ai"
echo ""
echo "🎉 QURAN AI development environment is ready!"