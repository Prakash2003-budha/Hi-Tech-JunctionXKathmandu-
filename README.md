# TrustBridge 🏦

**Alternative Trust Layer for Financial Inclusion**

TrustBridge is an open-source alternative trust middleware that generates credit scores for unbanked merchants using three non-traditional data layers:

| Layer | What it measures | Tech used |
|---|---|---|
| **Social Graph** | Community vouching, reputation, fraud detection | NetworkX, Graph Analysis |
| **Psychometric** | Conscientiousness, risk aversion, resilience | Gemini 2.5 Flash-Lite API |
| **Behavioral** | Payment patterns, income seasonality, consistency | ML-based pattern recognition |

## 📊 Stack

- **Backend:** FastAPI + Python 3.11
- **Database:** PostgreSQL 15
- **Frontend:** Streamlit
- **Package Manager:** `uv` (ultra-fast Python package installer)
- **Container:** Docker + Docker Compose
- **ML:** NetworkX, scikit-learn, XGBoost
- **API:** Gemini 2.5 Flash-Lite

## 🚀 Quick Start

### Option 1: Docker (Recommended)

#### Prerequisites
- Docker & Docker Compose
- Gemini API key (free from [aistudio.google.com](https://aistudio.google.com))

#### Setup & Run

```bash
# 1. Clone/navigate to project
cd Hi-Tech-JunctionXKathmandu-

# 2. Create .env file
cp .env.example .env

# 3. Add your Gemini API key to .env
nano .env
# Edit: GEMINI_API_KEY=your_key_here

# 4. Start all services
docker-compose up --build

# 5. Wait for services to be ready (~2-3 minutes)
# You'll see "Backend startup complete" in logs

# 6. Access the application
# Frontend:  http://localhost:8501
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**That's it!** All three components (PostgreSQL, backend, frontend) start automatically.

### Option 2: Local Development (with `uv`)

#### Prerequisites
- Python 3.11+
- PostgreSQL 15
- `uv` package manager ([install](https://docs.astral.sh/uv/))

#### Setup

```bash
# 1. Navigate to project
cd Hi-Tech-JunctionXKathmandu-

# 2. Create .env file
cp .env.example .env
nano .env  # Add your Gemini API key

# 3. Install dependencies with uv
uv pip install -e .

# 4. Generate mock merchant data
python Backend/data/generate_mock.py

# 5. Start PostgreSQL (macOS)
brew services start postgresql@15

# Or on Linux
sudo systemctl start postgresql

# 6. Initialize database
psql -U postgres -f Backend/db/schema.sql

# 7. Run backend (Terminal 1)
cd Backend
uvicorn main:app --reload --port 8000

# 8. Run frontend (Terminal 2)
streamlit run Frontend/app.py

# 9. Access
# Frontend:  http://localhost:8501
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

## 📁 Project Structure

```
trustbridge/
├── Backend/
│   ├── main.py                  # FastAPI entry point
│   ├── engines/
│   │   ├── social_graph.py      # Layer 1: NetworkX graph engine
│   │   ├── psychometric.py      # Layer 2: Gemini API engine
│   │   ├── behavioral.py        # Layer 3: Pattern analysis
│   │   └── fusion.py            # Score fusion engine
│   ├── models/
│   │   └── merchant.py          # Pydantic models
│   ├── data/
│   │   ├── generate_mock.py     # Synthetic data generator
│   │   └── mock_merchants.json  # Generated merchants
│   └── db/
│       └── schema.sql           # PostgreSQL schema
│
├── Frontend/
│   └── app.py                   # Streamlit dashboard
│
├── pyproject.toml               # uv project config
├── docker-compose.yml           # Container orchestration
├── Dockerfile.backend           # Backend image
├── Dockerfile.frontend          # Frontend image
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🎯 How It Works

### 1. **Social Graph Engine** (Layer 1)
- Analyzes community vouching networks using NetworkX
- Detects fraud rings (mutual collusion)
- Computes weighted PageRank trust scores
- Returns: 0-100 score + fraud flag

### 2. **Psychometric Profiler** (Layer 2)
- Asks 5 situational questions in Nepali business context
- Uses Gemini API for deep analysis (falls back gracefully if unavailable)
- Classifies credit personality: "Cautious Planner", "Community Builder", etc.
- Returns: Trait scores + personality insights

### 3. **Behavioral Proxy** (Layer 3)
- Analyzes 18 months of transaction history
- Scores:
  - **Transactional Consistency:** Revenue volatility
  - **Obligation Fulfillment:** Bill payment punctuality
  - **Airtime Consistency:** Telecom top-up patterns
  - **Seasonality:** Revenue alignment with harvest cycles
  - **Khata Repayment:** Ledger-based repayment for cash merchants

### 4. **Score Fusion**
- Combines 3 layers with dynamic weights per merchant segment:
  - Digital natives: 25% social + 20% psychometric + 55% behavioral
  - Cash merchants: 35% social + 30% psychometric + 35% behavioral
  - New merchants: 45% social + 40% psychometric + 15% behavioral
- Computes confidence band (10-100%)
- Maps to lending tier (A/B/C/D)

## 🔑 API Endpoints

### Merchants
```bash
GET /merchants              # List all merchants
GET /merchants/{id}         # Get merchant details
GET /merchants/{id}/score   # Compute trust score
```

### Assessment
```bash
GET  /psychometric/questions        # Get assessment questions
POST /psychometric/{merchant_id}    # Submit responses
```

### Graph Analytics
```bash
GET /graph/stats           # Network statistics
GET /health                # Health check
```

### Interactive API Docs
Open [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI with try-it-out functionality.

## 📊 Example Score Output

```json
{
  "merchant_id": "M001",
  "merchant_name": "Sita Devi",
  "final_score": 72,
  "confidence": 0.85,
  "confidence_pct": 85,
  "segment": "cash_merchant",
  "sub_scores": {
    "social": 65,
    "psychometric": 78,
    "behavioral": 71
  },
  "lending_tier": {
    "tier": "A",
    "label": "Full credit eligible",
    "max_loan_npr": 50000,
    "interest_rate": "12% per annum",
    "color": "green"
  },
  "fraud_flag": false,
  "credit_personality": "Cautious Planner",
  "improvement_pathway": [
    "Maintain current habits — your score updates monthly"
  ]
}
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild specific service
docker-compose build backend --no-cache

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U postgres -d trustbridge
```

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Gemini API
GEMINI_API_KEY=AIzaSy_...          # Free key from aistudio.google.com
GEMINI_MODEL=gemini-2.5-flash-lite # Model to use

# Database (Docker uses this automatically)
DATABASE_URL=postgresql://postgres:trustbridge_password@postgres:5432/trustbridge

# App
APP_ENV=development                # or production
SECRET_KEY=your_random_key_here
API_URL=http://localhost:8000      # For frontend
```

### Database (PostgreSQL)

- **Host:** `postgres` (in Docker) or `localhost` (local)
- **Port:** `5432`
- **User:** `postgres`
- **Password:** `trustbridge_password`
- **Database:** `trustbridge`

Tables auto-created on first run:
- `merchants` - Merchant profiles
- `trust_scores` - Score history (time-series)
- `psychometric_responses` - Assessment history

## 🧪 Testing

### Generate Mock Data
```bash
python Backend/data/generate_mock.py
```

Generates 30 synthetic Nepali merchants with:
- 18 months of revenue history
- Bill payment records
- Airtime/utility patterns
- Khata ledger entries
- Social vouching networks

### Test API
```bash
# Health check
curl http://localhost:8000/health

# List merchants
curl http://localhost:8000/merchants

# Compute score
curl -X POST http://localhost:8000/score/M001 \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": "M001", "psychometric_responses": {"q1": "A", "q2": "B", "q3": "D", "q4": "C", "q5": "A"}}'
```

## 📈 Demo Walkthrough (5 minutes)

1. **Select a merchant** in sidebar (e.g., "Sita Devi")
2. **Complete psychometric assessment** (Tab 1) - answer 5 questions
3. **Compute full score** (Tab 2) - watch all three engines run
4. **Explore results:**
   - Trust score & lending tier
   - Three-layer sub-scores chart
   - Credit personality insights
   - Actionable improvement pathway
5. **View social network** (Tab 3) - see community vouching

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Port 8000 already in use` | Change port in `docker-compose.yml` or kill process: `lsof -ti:8000 \| xargs kill -9` |
| `ModuleNotFoundError` | Ensure dependencies installed: `uv pip install -e .` |
| `Gemini 429 Too Many Requests` | Hit free rate limit (1000/day). Wait or reduce calls. |
| `PostgreSQL connection refused` | Ensure postgres service is running: `docker-compose logs postgres` |
| `Mock data not found` | Run: `python Backend/data/generate_mock.py` |
| `Backend not responding` | Check logs: `docker-compose logs backend` |
| `Frontend shows old data` | Clear Streamlit cache: Settings → Clear cache |

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Mobile USSD integration for merchant onboarding
- Real-time score updates via WebSockets
- Neo4j graph database for scale
- Blockchain-based score portability
- Multi-language support

## 📜 License

Open source. Use freely for financial inclusion.

## 🎓 Technical Highlights

### Why `uv` instead of pip?
- **10-100x faster** package installation
- Drop-in replacement for pip
- Better dependency resolution
- Used in Docker to keep images lean

### Why Docker?
- **Reproducibility:** Exact same environment everywhere
- **Simplicity:** One command (`docker-compose up`) instead of manual setup
- **Scaling:** Easy to add more services (worker queues, caching, etc.)
- **Collaboration:** Team members don't fight with local setup issues

### Score Algorithm
- **Confidence band:** Reflects data quality, not just point estimates
- **Segment-based weights:** Different merchants need different signals
- **Fraud detection:** Catches collusion rings real-time
- **Adaptive:** Learns as merchant history grows

## 📧 Support

For questions or issues:
1. Check troubleshooting section above
2. Review API docs at `/docs`
3. Check service logs: `docker-compose logs`
4. Open an issue on GitHub

## 🌍 Vision

TrustBridge enables financial inclusion for 1.7B unbanked people by proving creditworthiness through non-traditional data. A farmer's bill payment history, a merchant's supplier relationships, and their financial decision-making patterns are just as predictive of creditworthiness as traditional credit scores—and far more accessible.

**Built for the Alternative Trust Layer for Financial Inclusion Hackathon · May 2026**

**Team:** Ranjesh, Aadarsha, Prakash (Ctrl Alt Elite)

---

*Zero cost. Zero corporate data collection. 100% open source. For financial inclusion.*