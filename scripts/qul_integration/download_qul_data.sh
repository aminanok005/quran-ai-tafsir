#!/bin/bash

# QURAN AI - QUL Data Download and Import Script
# Downloads and imports Tarteel Quranic Universal Library data

set -e

echo "🔧 QURAN AI - QUL Data Integration"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
QUL_DUMP_URL="https://static-cdn.tarteel.ai/qul/mini-dumps/mini_quran_dev.sql.zip"
QUL_DUMP_FILE="mini_quran_dev.sql.zip"
QUL_SQL_FILE="mini_quran_dev.sql"
DOWNLOAD_DIR="/tmp/qul_import"
TARGET_DB="quran_ai"
TARGET_USER="quran_ai"

print_info "Starting QUL data integration..."

# Create download directory
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

# Step 1: Download QUL data dump
print_info "Downloading QUL data dump..."
print_info "URL: $QUL_DUMP_URL"

if ! command -v curl &> /dev/null; then
    print_error "curl is required but not installed"
    exit 1
fi

curl -L -o "$QUL_DUMP_FILE" "$QUL_DUMP_URL"

if [ ! -f "$QUL_DUMP_FILE" ]; then
    print_error "Failed to download QUL data dump"
    exit 1
fi

print_info "Download complete: $(ls -lh "$QUL_DUMP_FILE" | awk '{print $5}')"

# Step 2: Extract SQL file
print_info "Extracting SQL dump..."

if ! command -v unzip &> /dev/null; then
    print_error "unzip is required but not installed"
    exit 1
fi

unzip -o "$QUL_DUMP_FILE"

if [ ! -f "$QUL_SQL_FILE" ]; then
    print_error "SQL file not found after extraction"
    exit 1
fi

print_info "Extraction complete: $(ls -lh "$QUL_SQL_FILE" | awk '{print $5}')"

# Step 3: Check PostgreSQL connection
print_info "Checking PostgreSQL connection..."

if ! command -v psql &> /dev/null; then
    print_error "PostgreSQL client (psql) not found"
    exit 1
fi

# Test connection
if ! psql -U "$TARGET_USER" -d "$TARGET_DB" -c "SELECT 1;" &> /dev/null; then
    print_error "Cannot connect to PostgreSQL database '$TARGET_DB' as user '$TARGET_USER'"
    print_info "Please ensure:"
    print_info "  1. PostgreSQL is running"
    print_info "  2. Database '$TARGET_DB' exists"
    print_info "  3. User '$TARGET_USER' has access"
    print_info "  4. Connection parameters are correct"
    exit 1
fi

print_info "PostgreSQL connection successful"

# Step 4: Import QUL data
print_info "Importing QUL data into database..."
print_warn "This may take several minutes depending on database size..."

# Import with progress tracking
pv "$QUL_SQL_FILE" | psql -U "$TARGET_USER" -d "$TARGET_DB" -q

if [ $? -eq 0 ]; then
    print_info "✅ QUL data import completed successfully!"
else
    print_error "❌ QUL data import failed"
    exit 1
fi

# Step 5: Verify import
print_info "Verifying import..."

TABLES=("verses" "words" "translations" "tafsirs" "audio_files" "roots")
for table in "${TABLES[@]}"; do
    COUNT=$(psql -U "$TARGET_USER" -d "$TARGET_DB" -t -c "SELECT COUNT(*) FROM $table;")
    print_info "  $table: $COUNT records"
done

# Step 6: Cleanup
print_info "Cleaning up temporary files..."
cd /
rm -rf "$DOWNLOAD_DIR"

print_info "🎉 QUL data integration completed successfully!"
print_info ""
print_info "Next steps:"
print_info "1. Run schema alignment migration: python3 -m alembic upgrade head"
print_info "2. Test agent retrieval with real data"
print_info "3. Build embeddings for RAG system"
print_info "4. Verify agent responses with QUL tafsir data"

print_info "Data source: Tarteel Quranic Universal Library (MIT License)"
print_info "Documentation: https://qul.tarteel.ai/docs"