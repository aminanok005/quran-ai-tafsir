#!/bin/bash
# Fix for Python package installation in Debian/Ubuntu systems
# Use --break-system-packages to bypass PEP 668 restrictions

set -e

echo "🔧 Installing Python dependencies for QURAN AI..."

# Install packages with --break-system-packages to bypass PEP 668 restrictions
pip3 install --break-system-packages sqlalchemy psycopg2-binary alembic fastapi python-dotenv requests

if [ $? -eq 0 ]; then
    echo "✅ Python packages installed successfully"

    # Verify installation
    echo "🔍 Verifying installation..."
    python3 -c "import sqlalchemy; print('✅ SQLAlchemy:', sqlalchemy.__version__)"
    python3 -c "import psycopg2; print('✅ psycopg2:', psycopg2.__version__)"
    python3 -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
    python3 -c "import alembic; print('✅ Alembic:', alembic.__version__)"
    python3 -c "import requests; print('✅ requests:', requests.__version__)"

    echo "🎉 Python environment setup complete!"
else
    echo "❌ Python package installation failed"
    exit 1
fi