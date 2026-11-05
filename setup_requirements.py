#!/bin/bash
# Setup requirements and install Python packages
# This script handles the Python dependency setup for QURAN AI

set -e

echo "🔧 Setting up Python dependencies for QURAN AI..."

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Installing pip..."
    apt-get update && apt-get install -y python3-pip
fi

# Install packages with --break-system-packages flag
echo "📦 Installing Python packages..."
pip3 install --break-system-packages sqlalchemy psycopg2-binary alembic fastapi python-dotenv requests

# Verify installation
echo "🔍 Verifying installation..."
if python3 -c "import sqlalchemy" && python3 -c "import psycopg2" && python3 -c "import fastapi" && python3 -c "import alembic" && python3 -c "import requests"; then
    echo "✅ All Python packages installed successfully!"
else
    echo "❌ Some packages failed to install"
    exit 1
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x /home/nisreen/Videos/yt-project/quran-intelligent-tafsir/scripts/*.py
echo "chmod +x /home/nisreen/Videos/yt-project/quran-intelligent-tafsir/setup_database.py"

# Install database extension
if ! psql -h localhost -U postgres -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" >/dev/null 2>&1; then
    echo "📊 Installing pgvector extension..."
    sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
fi

# Create databases
if ! psql -h localhost -U postgres -c "SELECT 1 FROM pg_database WHERE datname = 'quran_ai';" >/dev/null 2>&1; then
    echo "📋 Creating quran_ai database..."
    sudo -u postgres psql -c "CREATE DATABASE quran_ai OWNER postgres;"
fi

# Configure PostgreSQL user
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'quran_ai';" 2>/devnull || echo "Password change may have failed"

# Run database setup
if [ -f "/home/nisreen/Videos/yt-project/quran-intelligent-tafsir/setup_database.py" ]; then
    echo "🚀 Running database setup..."
    python3 /home/nisreen/Videos/yt-project/quran-intelligent-tafsir/setup_database.py
    if [ $? -eq 0 ]; then
        echo "✅ Database setup completed successfully"
    else
        echo "❌ Database setup failed"
        exit 1
    fi
fi

echo "🎉 Environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Configure .env file with actual API credentials"
echo "   2. Edit scripts/setup_env.sh if needed"
echo "   3. Run remaining setup scripts"
echo "   4. Test database connectivity"