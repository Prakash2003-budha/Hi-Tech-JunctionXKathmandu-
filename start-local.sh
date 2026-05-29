#!/bin/bash

# Start Backend and Frontend locally with uv
# Requires: Python 3.11+, PostgreSQL running, .env configured

set -e

echo "🚀 Starting TrustBridge (Local Development)"
echo "==========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
echo "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv not found. Install: pip install uv${NC}"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo -e "${RED}✗ PostgreSQL not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All dependencies found${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Creating from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Update .env with your Gemini API key${NC}"
    exit 1
fi

echo "Starting services..."
echo ""

# Terminal 1: Backend
echo -e "${GREEN}Starting Backend (FastAPI)...${NC}"
echo "Run this in Terminal 1:"
echo "  cd Backend && uvicorn main:app --reload --port 8000"
echo ""

# Terminal 2: Frontend
echo -e "${GREEN}Starting Frontend (Streamlit)...${NC}"
echo "Run this in Terminal 2:"
echo "  streamlit run Frontend/app.py"
echo ""

echo "Once both are running:"
echo -e "${GREEN}Frontend:  http://localhost:8501${NC}"
echo -e "${GREEN}Backend:   http://localhost:8000${NC}"
echo -e "${GREEN}API Docs:  http://localhost:8000/docs${NC}"
