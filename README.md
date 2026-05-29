# TrustBridge

Alternative trust middleware for unbanked merchants in Nepal.
Generates credit scores using three non-traditional data layers.

## Stack

- **Backend**: FastAPI + NetworkX + Gemini API (Python 3.11, managed by `uv`)
- **Frontend**: React 18 + Vite + Recharts

## Quick Start

### 1. Generate mock data (one-time)
```bash
uv run backend/data/generate_mock.py
```

### 2. Start the backend
```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```
API docs → http://localhost:8000/docs

### 3. Start the frontend
```bash
cd frontend
npm install
npm run dev
```
App → http://localhost:5173

### 4. Set up your .env
```bash
cp .env.example .env
# Add your GEMINI_API_KEY from https://aistudio.google.com
```

## Scoring Layers

| Layer | Engine | Score |
|---|---|---|
| Social Graph | NetworkX PageRank + fraud ring detection | 0–100 |
| Psychometric | 5 situational questions → Gemini analysis | 0–100 |
| Behavioral | Utility payments, airtime, revenue consistency | 0–100 |

Final score = weighted fusion by merchant segment (digital_native / cash_merchant / new_merchant).

## Database (optional)
```bash
psql -U postgres -f backend/db/schema.sql
```
