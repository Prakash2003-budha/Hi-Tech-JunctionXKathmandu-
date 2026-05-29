# TrustBridge Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                          │
│                   (Streamlit UI)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Frontend Service                            │
│         (Streamlit on Port 8501)                        │
│  - Merchant selection                                   │
│  - Psychometric assessment form                         │
│  - Score visualization (Plotly)                         │
│  - Social graph display                                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ REST API Calls (JSON)
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Backend API Service                         │
│         (FastAPI on Port 8000)                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Score Computation Pipeline              │  │
│  ├──────────────────────────────────────────────────┤  │
│  │                                                  │  │
│  │  Layer 1: Social Graph Engine                   │  │
│  │  ├─ Build merchant network from vouchers        │  │
│  │  ├─ Compute weighted PageRank                   │  │
│  │  ├─ Detect fraud rings (cliques)                │  │
│  │  └─ Score: 0-100                                │  │
│  │                                                  │  │
│  │  Layer 2: Psychometric Profiler                 │  │
│  │  ├─ Score 5 situational questions               │  │
│  │  ├─ Call Gemini API for analysis                │  │
│  │  ├─ Classify credit personality                 │  │
│  │  └─ Score: 0-100 + traits                       │  │
│  │                                                  │  │
│  │  Layer 3: Behavioral Proxy                      │  │
│  │  ├─ Analyze 18-month transaction history        │  │
│  │  ├─ Calculate 5 behavioral sub-scores           │  │
│  │  ├─ Detect seasonality patterns                 │  │
│  │  └─ Score: 0-100                                │  │
│  │                                                  │  │
│  │  Score Fusion Engine                            │  │
│  │  ├─ Apply segment-specific weights              │  │
│  │  ├─ Compute confidence band                     │  │
│  │  ├─ Map to lending tier (A/B/C/D)               │  │
│  │  ├─ Generate improvement pathway                │  │
│  │  └─ Final Score: 0-100                          │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  Endpoints:                                             │
│  - GET  /merchants                                      │
│  - GET  /merchants/{id}                                 │
│  - POST /score/{id}                                     │
│  - GET  /psychometric/questions                         │
│  - GET  /graph/stats                                    │
│  - GET  /health                                         │
│                                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ SQL Queries
                     ▼
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database                         │
│         (Port 5432, Docker volume persisted)            │
├─────────────────────────────────────────────────────────┤
│ Tables:                                                  │
│ - merchants (merchant profiles)                          │
│ - trust_scores (time-series scoring history)             │
│ - psychometric_responses (assessment history)            │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (Streamlit)

**Purpose:** User interface for merchant assessment and score visualization

**Technology Stack:**
- Streamlit (rapid prototyping UI framework)
- Plotly (interactive charts)
- Requests (HTTP client)

**Features:**
- Merchant dropdown selector
- Merchant profile display
- Psychometric assessment form (5 questions)
- Trust score computation trigger
- Score visualization:
  - 3-layer sub-scores bar chart
  - Behavioral breakdown metrics
  - Lending tier badge
  - Improvement pathway
- Social graph statistics
- Raw JSON output for API integration

**File:** `Frontend/app.py`

### 2. Backend API (FastAPI)

**Purpose:** Core business logic, score computation, data management

**Technology Stack:**
- FastAPI (high-performance REST framework)
- Pydantic (data validation)
- NetworkX (graph algorithms)
- Google Generative AI (Gemini API)

**Endpoints:**
```
GET    /
GET    /health
GET    /merchants
GET    /merchants/{merchant_id}
GET    /psychometric/questions
POST   /score/{merchant_id}
GET    /graph/stats
```

**File:** `Backend/main.py`

### 3. Scoring Engines

#### 3.1 Social Graph Engine (`Backend/engines/social_graph.py`)

**Input:**
- Merchant list with voucher data
- Vouching relationships (supplier, peer, elder, family)
- Months known + voucher trust score

**Algorithm:**
1. Build directed weighted graph from voucher relationships
2. Weight edges by:
   - Relationship type (supplier=1.0, peer=0.8, etc.)
   - Voucher's own trust score (0-100)
   - Duration of relationship (capped at 24 months)
3. Detect fraud rings:
   - Find all maximal cliques in undirected version
   - Flag cliques of 3+ with zero external edges
4. Compute weighted PageRank on directed graph
5. Normalize PageRank to 0-100
6. Add diversity bonus (different relationship types)

**Output:**
```python
{
  "social_score": 0-100,
  "fraud_flag": bool,
  "pagerank_raw": float,
  "voucher_count": int,
  "relationship_diversity": int,
  "explanation": str
}
```

#### 3.2 Psychometric Profiler (`Backend/engines/psychometric.py`)

**Input:**
- 5 Nepali-context situational questions
- Merchant's answers (A/B/C/D)

**Algorithm:**
1. Score responses deterministically using predefined rubric
2. Normalize each trait to 0-100
3. Send to Gemini API with response summary
4. Parse JSON response for traits + personality
5. Graceful fallback if API unavailable

**Traits Measured:**
- Risk aversion
- Conscientiousness
- Social trust
- Resilience
- Planning ability

**Output:**
```python
{
  "psychometric_score": 0-100,
  "trait_scores": {
    "conscientiousness": 0-100,
    "risk_aversion": 0-100,
    "social_trust": 0-100,
    "resilience": 0-100,
    "planning": 0-100
  },
  "credit_personality": "Cautious Planner|Community Builder|...",
  "insight": str,
  "red_flags": str,
  "strengths": str
}
```

#### 3.3 Behavioral Proxy Engine (`Backend/engines/behavioral.py`)

**Input:**
- 18 months revenue history
- Utility payment records (NEA bills)
- Airtime top-up patterns (Ncell/NTC)
- Khata entries (cash ledger for unbanked)
- Business type

**Algorithm:**

1. **Transactional Consistency** (25-35% weight)
   - Calculate coefficient of variation (CV = σ/μ)
   - Score = 100 * e^(-CV)
   - Rewards stable, predictable revenue

2. **Obligation Fulfillment** (25-30% weight)
   - Percentage of on-time bill payments
   - Penalty for partial payments (30% reduction per partial)
   - Score = (on_time_rate - partial_penalty) * 100

3. **Airtime Consistency** (15-20% weight)
   - Analyze monthly top-up amounts
   - Score = 100 * e^(-CV * 0.8)
   - Regular top-ups indicate stable income

4. **Cash Flow Seasonality** (15% weight)
   - Compare actual revenue spikes to expected harvest calendar
   - Nepali crops: vegetables (Sept-Feb), dairy (May-Feb), clothing (Oct-Jan), etc.
   - Score = alignment_rate * 100

5. **Khata Repayment** (0-20% weight)
   - For cash-only merchants with USSD ledger entries
   - Track debt repayment rate and speed
   - Score = repayment_rate * 100 * speed_factor

**Output:**
```python
{
  "behavioral_score": 0-100,
  "sub_scores": {
    "transactional_consistency": 0-100,
    "obligation_fulfillment": 0-100,
    "airtime_consistency": 0-100,
    "cash_flow_seasonality": 0-100,
    "khata_repayment": 0-100
  }
}
```

#### 3.4 Score Fusion Engine (`Backend/engines/fusion.py`)

**Input:**
- Social score (0-100)
- Psychometric score (0-100)
- Behavioral score (0-100)
- Merchant profile

**Algorithm:**

1. **Segment Classification:**
   - Digital native: Has eSewa/Khalti + 12+ months history
   - Cash merchant: Has khata entries, no digital
   - New merchant: Everything else

2. **Dynamic Weighting:**
   ```
   Digital native:  25% social + 20% psychometric + 55% behavioral
   Cash merchant:   35% social + 30% psychometric + 35% behavioral
   New merchant:    45% social + 40% psychometric + 15% behavioral
   ```

3. **Raw Score:**
   ```
   raw_score = Σ(weight_i * score_i)
   ```

4. **Confidence Calculation:**
   ```
   confidence = (
     data_points/18 * 0.5 +
     data_sources/4 * 0.4 +
     psychometric_bonus * 0.1
   ) * (1 - fraud_penalty)
   ```
   - Reflects data quality, not just point estimates
   - Range: 0.1-1.0 (10-100%)

5. **Lending Tier Mapping:**
   ```
   effective_score = final_score * confidence
   
   A: effective >= 65 (NPR 50,000, 12%)
   B: effective >= 45 (NPR 15,000, 16%)
   C: effective >= 28 (NPR 0, building profile)
   D: effective < 28  (NPR 0, insufficient data)
   ```

6. **Improvement Pathway:**
   - Suggestions based on weakest components
   - Actionable next steps (record khata, pay bills on time, etc.)

**Output:**
```python
{
  "merchant_id": str,
  "merchant_name": str,
  "final_score": 0-100,
  "confidence": 0.0-1.0,
  "segment": "digital_native|cash_merchant|new_merchant",
  "sub_scores": {
    "social": 0-100,
    "psychometric": 0-100,
    "behavioral": 0-100
  },
  "lending_tier": {
    "tier": "A|B|C|D",
    "label": str,
    "max_loan_npr": int,
    "interest_rate": str
  },
  "fraud_flag": bool,
  "improvement_pathway": [str, ...]
}
```

### 4. Database Schema (PostgreSQL)

```sql
merchants
├── id (PK)
├── merchant_id (UK) -- M001, M002, ...
├── name
├── district
├── business_type
├── phone
├── digital_footprint
├── esewa_registered
├── khalti_registered
└── created_at

trust_scores (time-series)
├── id (PK)
├── merchant_id (FK) -- tracks which merchant
├── final_score
├── confidence
├── segment
├── social_score
├── psychometric_score
├── behavioral_score
├── lending_tier
├── fraud_flag
├── full_result (JSONB) -- complete score object
└── scored_at (indexed)

psychometric_responses (history)
├── id (PK)
├── merchant_id (FK)
├── responses (JSONB) -- {"q1": "A", "q2": "B", ...}
├── trait_scores (JSONB)
├── credit_personality
└── assessed_at
```

## Data Flow

### Scoring a Merchant

```
1. User selects merchant from dropdown
   └─> Frontend loads merchant profile + vouchers

2. User completes psychometric assessment
   └─> Frontend stores responses in session

3. User clicks "Compute Score"
   ├─> Frontend sends POST /score/{merchant_id} with responses
   │
   └─> Backend:
       ├─ Load merchant from memory (mock_merchants.json)
       ├─ Layer 1: score_merchant_social()
       │   └─ Use pre-built GRAPH (built at startup)
       ├─ Layer 2: run_psychometric_assessment()
       │   ├─ Score responses deterministically
       │   └─ Call Gemini API for analysis
       ├─ Layer 3: compute_behavioral_score()
       │   └─ Analyze merchant's history
       └─ fuse_scores()
           └─ Combine all three + generate tier + pathway
   
   └─> Backend returns full score JSON

4. Frontend displays score + visualizations

5. (Optional) Backend stores in PostgreSQL for audit trail
```

## Deployment Architecture

### Docker Compose Stack

```
trustbridge-network (bridge)
├── postgres (postgres:15-alpine)
│   ├── Port: 5432
│   └── Volume: postgres_data
├── backend (FastAPI service)
│   ├── Port: 8000
│   ├── Depends on: postgres
│   └── Health check: GET /health
└── frontend (Streamlit service)
    ├── Port: 8501
    ├── Depends on: backend
    └── Health check: HTTP 200
```

### Environment Isolation

- **Backend:** Runs Python 3.11 slim image, dependencies via uv
- **Frontend:** Runs separate Python 3.11 image, shares codebase
- **Database:** Persistent volume `postgres_data` survives container restarts
- **Network:** All services on isolated bridge network

## Performance Considerations

### Scoring Latency
- Social graph: ~50-200ms (depends on graph size)
- Psychometric: 500ms-2s (Gemini API call)
- Behavioral: ~100-300ms (18 months of history)
- Fusion: ~50ms
- **Total:** 1-3 seconds per score

### Data Storage
- Mock merchants: ~30 merchants = ~500KB JSON
- Time-series scores: 1 new row per score = minimal growth
- Historical data can be archived to S3 after 1-2 years

### Scaling Paths
1. Cache merchant graphs + behavioral history
2. Use Redis for request deduplication
3. Async queue for Gemini API calls
4. Neo4j for graph analytics at scale (10K+ merchants)
5. Kafka for event-driven architecture

## Security Considerations

1. **API Keys:**
   - Gemini key stored in environment variable
   - Never committed to git
   - Rotated in production

2. **Database:**
   - PostgreSQL default username/password used locally
   - Change in production
   - Network isolation via Docker

3. **Fraud Detection:**
   - Graph-based fraud ring detection (no false positives for honest merchants)
   - Confidence band prevents over-reliance on incomplete data
   - Psychometric assessment catches dishonest responses

4. **Data Privacy:**
   - No real PII stored (synthetic data for demo)
   - JSONB responses encrypted at rest in production
   - Audit trail in `scored_at` timestamps

---

**For questions, refer to README.md or API docs at `/docs`**
