#!/bin/bash

# TrustBridge Setup Script
# Automated setup for local development with uv

set -e

echo "🏦 TrustBridge Setup Script"
echo "================================"

# Check for Python 3.11+
echo "✓ Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $PYTHON_VERSION"

# Check for PostgreSQL
echo "✓ Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "  ❌ PostgreSQL not found. Install with:"
    echo "     macOS: brew install postgresql@15"
    echo "     Linux: sudo apt install postgresql"
    exit 1
fi
echo "  PostgreSQL found: $(psql --version)"

# Check for uv
echo "✓ Checking uv..."
if ! command -v uv &> /dev/null; then
    echo "  ❌ uv not found. Install with: pip install uv"
    exit 1
fi
echo "  uv found: $(uv --version)"

# Create .env if not exists
echo "✓ Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env file (update with your Gemini API key)"
else
    echo "  .env already exists"
fi

# Install dependencies
echo "✓ Installing dependencies with uv..."
uv pip install -e .

# Generate mock data
echo "✓ Generating mock merchant data..."
cd Backend
python data/generate_mock.py
cd ..

# Start PostgreSQL
echo "✓ Starting PostgreSQL..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start postgresql@15 || true
    sleep 2
else
    sudo systemctl start postgresql || true
    sleep 2
fi

# Initialize database
echo "✓ Initializing database..."
psql -U postgres -f Backend/db/schema.sql

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your Gemini API key"
echo "2. Start backend: cd Backend && uvicorn main:app --reload"
echo "3. Start frontend: streamlit run Frontend/app.py"
echo "4. Open http://localhost:8501"
