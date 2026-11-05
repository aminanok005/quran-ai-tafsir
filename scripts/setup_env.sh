#!/bin/bash
# QURAN AI Environment Setup Script
# Configures environment variables for database initialization

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔧 QURAN AI Environment Setup"
echo "============================"

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo "✅ .env created"
else
    echo "⚠️  .env already exists, skipping creation"
fi

# Check PostgreSQL
echo ""
echo "🔍 Checking PostgreSQL..."
if command -v psql >/dev/null 2>&1; then
    echo "✅ psql available"
    if psql -h localhost -U postgres -c "SELECT 1;" >/dev/null 2>&1; then
        echo "✅ PostgreSQL connection works"
    else
        echo "⚠️  Cannot connect to PostgreSQL on localhost"
        echo "   Make sure PostgreSQL is running and accessible"
    fi
else
    echo "⚠️  psql not found - make sure PostgreSQL is installed"
fi

# Check Python
echo ""
echo "🔍 Checking Python..."
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "✅ Python $PYTHON_VERSION available"
else
    echo "❌ Python 3 not found"
    exit 1
fi

# Check pip
echo ""
echo "🔍 Checking pip..."
if command -v pip3 >/dev/null 2>&1; then
    echo "✅ pip3 available"
else
    echo "❌ pip3 not found"
    exit 1
fi

# Check required Python packages
echo ""
echo "🔍 Checking Python packages..."
REQUIRED_PACKAGES=("sqlalchemy" "psycopg2-binary" "alembic" "fastapi")
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $pkg" 2>/dev/null; then
        echo "✅ $pkg installed"
    else
        echo "⚠️  $pkg not installed - run: pip install $pkg"
    fi
done

# Check Bun
echo ""
echo "🔍 Checking Bun..."
if command -v bun >/dev/null 2>&1; then
    BUN_VERSION=$(bun --version 2>&1)
    echo "✅ Bun $BUN_VERSION available"
else
    echo "⚠️  Bun not found - install from https://bun.sh"
fi

# Check Node.js
echo ""
echo "🔍 Checking Node.js..."
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version 2>&1)
    echo "✅ Node.js $NODE_VERSION available"
else
    echo "⚠️  Node.js not found"
fi

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env with your database credentials"
echo "   2. Run: python3 scripts/load_tafsir_data.py"
echo "   3. Run: python3 scripts/seed_quran_data.py"