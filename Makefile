.PHONY: help build up down logs docker-logs backend-logs frontend-logs db-logs clean reset test lint format

help:
	@echo "TrustBridge - Make targets"
	@echo "=========================="
	@echo ""
	@echo "Docker commands:"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make logs          - View all logs"
	@echo "  make backend-logs  - View backend logs"
	@echo "  make frontend-logs - View frontend logs"
	@echo "  make db-logs       - View database logs"
	@echo ""
	@echo "Local development:"
	@echo "  make install       - Install dependencies with uv"
	@echo "  make migrate       - Initialize database"
	@echo "  make seed          - Generate mock data"
	@echo "  make backend-local - Run backend locally"
	@echo "  make frontend-local- Run frontend locally"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean         - Remove containers and volumes"
	@echo "  make reset         - Full reset (⚠ removes data)"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code"

# Docker targets
build:
	docker-compose build --no-cache

up:
	docker-compose up -d
	@echo "🚀 Services starting..."
	@echo "Frontend:  http://localhost:8501"
	@echo "Backend:   http://localhost:8000"
	@echo "Docs:      http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

backend-logs:
	docker-compose logs -f backend

frontend-logs:
	docker-compose logs -f frontend

db-logs:
	docker-compose logs -f postgres

# Local development targets
install:
	uv pip install -e .

migrate:
	psql -U postgres -f Backend/db/schema.sql

seed:
	python Backend/data/generate_mock.py

backend-local:
	cd Backend && uvicorn main:app --reload --port 8000

frontend-local:
	streamlit run Frontend/app.py

# Utility targets
clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

reset:
	docker-compose down -v
	rm -rf Backend/data/mock_merchants.json
	@echo "✓ Everything reset"

lint:
	uv pip install ruff
	ruff check Backend/ Frontend/

format:
	uv pip install black
	black Backend/ Frontend/

test:
	@echo "Testing framework not yet set up"
	@echo "Use: pytest Backend/ Frontend/"

shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U postgres -d trustbridge

.SILENT: help
