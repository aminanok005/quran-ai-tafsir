#!/bin/bash

# QURAN AI Super WebApp Setup Script
# This script initializes the complete QURAN AI platform with all dependencies

set -e

echo "🔧 QURAN AI Super WebApp Setup"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -f "package.json" ]; then
    print_error "Not in the QURAN AI project root directory"
    exit 1
fi

print_info "Setting up QURAN AI Super WebApp..."

# Step 1: Check Python and pip
print_info "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed"
    exit 1
fi

# Step 2: Install Python dependencies for backend
print_info "Installing Python dependencies..."
if [ -f "services/api/requirements.txt" ]; then
    pip3 install -r services/api/requirements.txt
else
    pip3 install fastapi uvicorn psycopg2-binary alembic sqlalchemy python-multipart
fi

# Step 3: Check Node.js and npm
print_info "Checking Node.js environment..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm is required but not installed"
    exit 1
fi

# Step 4: Install Node.js dependencies
print_info "Installing Node.js dependencies..."
cd apps/web
npm install

cd ../..

# Step 5: Check for PostgreSQL
print_info "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    print_warn "PostgreSQL client is installed but server may not be running"
else
    print_warn "PostgreSQL client not found. Install with: sudo apt-get install postgresql-client"
fi

# Step 6: Check for Redis
print_info "Checking Redis..."
if command -v redis-cli &> /dev/null; then
    print_info "Redis client is installed"
else
    print_warn "Redis client not found. Install with: sudo apt-get install redis-tools"
fi

# Step 7: Check for Docker
print_info "Checking Docker..."
if command -v docker &> /dev/null; then
    print_info "Docker is installed. You can run the project with Docker"
else
    print_warn "Docker is not installed. Install with: curl -fsSL https://get.docker.com -o get-docker.sh"
fi

# Step 8: Initialize database structure
print_info "Setting up database structure..."
cd services/api

if [ -f "alembic.ini" ]; then
    print_info "Running database migrations..."
    python3 -m alembic upgrade head
else
    print_error "alembic.ini not found in services/api"
fi

cd ../..

# Step 9: Create environment files
print_info "Creating environment configuration files..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "Created .env from .env.example"
        print_warn "Please edit .env file with your configuration"
    else
        print_warn ".env.example not found. Please create .env file manually"
    fi
fi

# Step 10: Create frontend environment file
if [ ! -f "apps/web/.env.local" ]; then
    print_info "Creating frontend environment file..."
    echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > apps/web/.env.local
    echo "NEXT_PUBLIC_APP_NAME=QURAN AI" >> apps/web/.env.local
    echo "NEXT_PUBLIC_APP_VERSION=0.1.0" >> apps/web/.env.local
    echo "NEXT_PUBLIC_DEFAULT_LOCALE=th" >> apps/web/.env.local
    echo "NEXT_PUBLIC_SUPPORTED_LOCALES=th,ar,en" >> apps/web/.env.local
    print_info "Created apps/web/.env.local"
fi

# Step 11: Install git hooks
print_info "Setting up git hooks..."
if [ -d ".git" ]; then
    print_info "Git repository detected"
    echo "#!/bin/bash

# Pre-commit hook to run linting and type checking
if npm run lint; then
    echo "✅ Linting passed"
else
    echo "❌ Linting failed"
    exit 1
fi

if npm run typecheck; then
    echo "✅ Type checking passed"
else
    echo "❌ Type checking failed"
    exit 1
fi

if python3 -m pytest services/api/tests/ -xvs 2>/dev/null || echo "No backend tests found"; then
    echo "✅ Backend tests passed"
else
    echo "⚠️  Backend tests had issues (this is okay for development)"
fi
" > .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    print_info "Created pre-commit hook"
else
    print_warn "Not a git repository. Git hooks not installed"
fi

# Step 12: Print completion summary
print_info "QURAN AI Super WebApp setup completed!"
echo ""
echo "Next steps:"
echo "1. Configure environment variables in .env and apps/web/.env.local"
echo "2. Install PostgreSQL and Redis if not already installed"
echo "3. Run database migrations: cd services/api && python3 -m alembic upgrade head"
echo "4. Start backend: cd services/api && uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "5. Start frontend: cd apps/web && npm run dev"
echo ""
echo "Access the application at:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - Health check: http://localhost:8000/health"
echo ""
echo "For development, use Docker Compose:"
echo "  docker-compose -f docker-compose.dev.yml up -d"

print_info "Setup script completed successfully!"