# TrustBridge — Full Build Documentation
### The Alternative Trust Layer for Financial Inclusion
**Hackathon Edition | May 2026**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Folder Structure](#2-folder-structure)
3. [Environment Setup](#3-environment-setup)
4. [API Keys & Configuration](#4-api-keys--configuration)
5. [Synthetic Data Generator](#5-synthetic-data-generator)
6. [Layer 1 — Social Graph Engine](#6-layer-1--social-graph-engine)
7. [Layer 2 — Psychometric Profiler (Gemini API)](#7-layer-2--psychometric-profiler-gemini-api)
8. [Layer 3 — Behavioral Proxy Engine](#8-layer-3--behavioral-proxy-engine)
9. [Score Fusion Engine](#9-score-fusion-engine)
10. [FastAPI Backend](#10-fastapi-backend)
11. [PostgreSQL Database Schema](#11-postgresql-database-schema)
12. [Streamlit Frontend](#12-streamlit-frontend)
13. [Running the Full Application](#13-running-the-full-application)
14. [Demo Script (Hackathon Presentation)](#14-demo-script-hackathon-presentation)
15. [Deployment on Render.com (Free)](#15-deployment-on-rendercom-free)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Project Overview

TrustBridge is an open-source alternative trust middleware that generates credit scores for unbanked merchants using three non-traditional data layers:

| Layer | What it measures | Tech used |
|---|---|---|
| Social Graph | Community vouching, reputation, fraud rings | NetworkX, Neo4j |
| Psychometric | Conscientiousness, risk aversion, resilience | Gemini 2.5 Flash-Lite API |
| Behavioral | Utility payments, airtime top-ups, seasonality | Synthetic data + NEA scrape |

**Final output:** A unified trust score (0–100) with confidence band, lending tier, and improvement pathway — stored as a merchant trust passport.

**Tech stack:** Python 3.11 · FastAPI · PostgreSQL · NetworkX · Gemini API · Streamlit

**Total cost: NPR 0 / $0**

---

## 2. Folder Structure

```
trustbridge/
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── routers/
│   │   ├── merchant.py          # Merchant CRUD endpoints
│   │   ├── score.py             # Scoring trigger endpoints
│   │   └── graph.py             # Graph query endpoints
│   ├── engines/
│   │   ├── social_graph.py      # Layer 1: NetworkX graph engine
│   │   ├── psychometric.py      # Layer 2: Gemini API engine
│   │   ├── behavioral.py        # Layer 3: Behavioral proxy engine
│   │   └── fusion.py            # Score fusion + confidence
│   ├── models/
│   │   ├── merchant.py          # Pydantic models
│   │   └── score.py             # Score models
│   ├── db/
│   │   ├── connection.py        # PostgreSQL connection
│   │   └── schema.sql           # Database schema
│   └── data/
│       ├── generate_mock.py     # Synthetic data generator
│       └── mock_merchants.json  # Generated mock data
│
├── frontend/
│   └── app.py                   # Streamlit dashboard
│
├── .env                         # API keys (never commit this)
├── .env.example                 # Template for .env
├── requirements.txt
└── README.md
```

---

## 3. Environment Setup

### Step 1 — Prerequisites

Make sure you have these installed:

```bash
# Check Python version (need 3.11+)
python --version

# Check pip
pip --version

# Check PostgreSQL
psql --version
```

If PostgreSQL is not installed:
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Step 2 — Clone and create virtual environment

```bash
# Create project folder
mkdir trustbridge && cd trustbridge

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3 — Install dependencies

Create `requirements.txt`:

```txt
fastapi==0.115.0
uvicorn==0.30.0
pydantic==2.7.0
python-dotenv==1.0.1
psycopg2-binary==2.9.9
sqlalchemy==2.0.30
networkx==3.3
google-generativeai==0.8.0
faker==25.0.0
numpy==1.26.4
scikit-learn==1.5.0
xgboost==2.0.3
requests==2.32.3
beautifulsoup4==4.12.3
streamlit==1.35.0
plotly==5.22.0
pandas==2.2.2
python-jose==3.3.0
httpx==0.27.0
```

Install everything:

```bash
pip install -r requirements.txt
```

---

## 4. API Keys & Configuration

### Step 1 — Get Gemini API key (free, no card needed)

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with any Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy the key — it looks like `AIzaSy...`

Free limits: **1,000 requests/day** on Flash-Lite — more than enough for a demo.

### Step 2 — Create your `.env` file

```bash
# In your project root
touch .env
```

Contents of `.env`:

```env
# Gemini API
GEMINI_API_KEY=AIzaSy_your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

# PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/trustbridge

# App config
APP_ENV=development
SECRET_KEY=your_random_secret_key_here
```

Create `.env.example` (safe to commit):

```env
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
DATABASE_URL=postgresql://user:password@localhost:5432/trustbridge
APP_ENV=development
SECRET_KEY=your_secret_key_here
```

Add `.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
```

---

## 5. Synthetic Data Generator

This generates realistic Nepali merchant data for all three scoring layers. Run this once before anything else.

**File: `backend/data/generate_mock.py`**

```python
import json
import random
import math
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("ne_NP")  # Nepali locale
random.seed(42)

DISTRICTS = ["Kathmandu", "Lalitpur", "Bhaktapur", "Pokhara", "Butwal", "Biratnagar"]
BUSINESS_TYPES = ["vegetables", "tea_shop", "clothing", "hardware", "dairy", "pharmacy"]
RELATIONSHIP_TYPES = ["supplier", "peer_merchant", "community_elder", "family_member"]

# Agricultural harvest calendar for Nepal (month numbers)
HARVEST_CALENDAR = {
    "vegetables": [1, 2, 3, 9, 10, 11],
    "dairy":      [4, 5, 6, 10, 11, 12],
    "tea_shop":   list(range(1, 13)),  # year-round
    "clothing":   [10, 11, 12, 1, 2],  # festival season
    "hardware":   [3, 4, 5, 9, 10],
    "pharmacy":   list(range(1, 13)),
}


def generate_monthly_revenue(business_type, months=18):
    """Generate realistic monthly revenue with seasonal patterns."""
    base = random.uniform(15000, 80000)
    harvest_months = HARVEST_CALENDAR.get(business_type, list(range(1, 13)))
    revenue = []
    today = datetime.now()

    for i in range(months, 0, -1):
        month_date = today - timedelta(days=i * 30)
        month_num = month_date.month
        seasonal_boost = 1.4 if month_num in harvest_months else 0.85
        noise = random.uniform(0.85, 1.15)
        revenue.append({
            "month": month_date.strftime("%Y-%m"),
            "amount": round(base * seasonal_boost * noise, 2)
        })
    return revenue


def generate_utility_payments(months=18):
    """Generate NEA + water bill payment history."""
    payments = []
    today = datetime.now()
    for i in range(months, 0, -1):
        month_date = today - timedelta(days=i * 30)
        on_time = random.random() > 0.15  # 85% on-time rate for good merchants
        partial = (not on_time) and random.random() > 0.5
        payments.append({
            "month": month_date.strftime("%Y-%m"),
            "utility": "NEA",
            "amount_due": random.randint(300, 1200),
            "paid_on_time": on_time,
            "partial_payment": partial,
            "days_late": 0 if on_time else random.randint(3, 45)
        })
    return payments


def generate_airtime_topups(months=18):
    """Generate Ncell/NTC top-up patterns."""
    topups = []
    today = datetime.now()
    for i in range(months, 0, -1):
        month_date = today - timedelta(days=i * 30)
        count = random.randint(2, 8)
        topups.append({
            "month": month_date.strftime("%Y-%m"),
            "provider": random.choice(["Ncell", "NTC"]),
            "topup_count": count,
            "total_amount": count * random.randint(50, 200)
        })
    return topups


def generate_khata_entries(months=6):
    """Generate USSD khata (ledger) entries for cash-only merchants."""
    entries = []
    today = datetime.now()
    for i in range(random.randint(8, 25)):
        entry_date = today - timedelta(days=random.randint(0, months * 30))
        amount = random.randint(200, 5000)
        repaid = random.random() > 0.2
        entries.append({
            "date": entry_date.strftime("%Y-%m-%d"),
            "counterparty": fake.name(),
            "type": random.choice(["credit_given", "debt_taken"]),
            "amount": amount,
            "repaid": repaid,
            "days_to_repay": random.randint(1, 60) if repaid else None
        })
    return entries


def generate_vouchers(merchant_id, all_ids, count=3):
    """Generate social vouching connections."""
    available = [m for m in all_ids if m != merchant_id]
    chosen = random.sample(available, min(count, len(available)))
    return [
        {
            "voucher_id": vid,
            "relationship": random.choice(RELATIONSHIP_TYPES),
            "months_known": random.randint(3, 60),
            "voucher_trust_score": random.randint(40, 90)
        }
        for vid in chosen
    ]


def generate_merchants(n=30):
    """Generate n synthetic Nepali merchants."""
    merchants = []
    ids = [f"M{str(i).zfill(3)}" for i in range(1, n + 1)]

    for mid in ids:
        btype = random.choice(BUSINESS_TYPES)
        digital = random.random() > 0.4  # 60% have some digital footprint

        merchant = {
            "merchant_id": mid,
            "name": fake.name(),
            "district": random.choice(DISTRICTS),
            "business_type": btype,
            "business_name": f"{fake.last_name()} {btype.replace('_', ' ').title()}",
            "phone": f"98{random.randint(10000000, 99999999)}",
            "years_in_business": round(random.uniform(0.5, 15), 1),
            "digital_footprint": digital,
            "esewa_registered": digital and random.random() > 0.3,
            "khalti_registered": digital and random.random() > 0.4,
            "vouchers": [],  # filled after all IDs exist
            "revenue_history": generate_monthly_revenue(btype),
            "utility_payments": generate_utility_payments(),
            "airtime_topups": generate_airtime_topups(),
            "khata_entries": generate_khata_entries() if not digital else [],
            "created_at": datetime.now().isoformat()
        }
        merchants.append(merchant)

    # Now add vouchers (needs all IDs to exist first)
    for merchant in merchants:
        merchant["vouchers"] = generate_vouchers(
            merchant["merchant_id"], ids, count=random.randint(1, 4)
        )

    return merchants


if __name__ == "__main__":
    data = generate_merchants(30)
    with open("backend/data/mock_merchants.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(data)} merchants → backend/data/mock_merchants.json")
```

Run it:

```bash
python backend/data/generate_mock.py
```

---

## 6. Layer 1 — Social Graph Engine

**File: `backend/engines/social_graph.py`**

```python
import networkx as nx
import math
from typing import Dict, List


def build_graph(merchants: List[Dict]) -> nx.DiGraph:
    """Build a directed weighted graph from merchant vouching data."""
    G = nx.DiGraph()

    for m in merchants:
        G.add_node(
            m["merchant_id"],
            name=m["name"],
            business_type=m["business_type"],
            district=m["district"]
        )

    relationship_weights = {
        "supplier":        1.0,
        "peer_merchant":   0.8,
        "community_elder": 0.6,
        "family_member":   0.4
    }

    for m in merchants:
        for v in m.get("vouchers", []):
            weight = (
                relationship_weights.get(v["relationship"], 0.5)
                * (v["voucher_trust_score"] / 100)
                * min(v["months_known"] / 24, 1.0)
            )
            G.add_edge(
                v["voucher_id"],
                m["merchant_id"],
                weight=weight,
                relationship=v["relationship"],
                months_known=v["months_known"]
            )

    return G


def detect_fraud_rings(G: nx.DiGraph) -> List[List[str]]:
    """
    Detect potential collusion: mutual vouch loops among 3+ merchants
    with no external connections. Uses clique detection on undirected view.
    """
    undirected = G.to_undirected()
    cliques = list(nx.find_cliques(undirected))
    # Flag cliques of 3+ with no outside edges
    suspicious = []
    for clique in cliques:
        if len(clique) >= 3:
            clique_set = set(clique)
            external_edges = sum(
                1 for n in clique
                for neighbor in G.neighbors(n)
                if neighbor not in clique_set
            )
            if external_edges == 0:
                suspicious.append(clique)
    return suspicious


def compute_pagerank_scores(G: nx.DiGraph) -> Dict[str, float]:
    """Compute weighted PageRank for all merchants."""
    if len(G.nodes) == 0:
        return {}
    try:
        scores = nx.pagerank(G, weight="weight", alpha=0.85, max_iter=200)
    except nx.PowerIterationFailedConvergence:
        scores = {n: 1 / len(G.nodes) for n in G.nodes}
    return scores


def score_merchant_social(merchant_id: str, G: nx.DiGraph) -> Dict:
    """
    Compute social trust score for a single merchant.

    Returns:
        social_score:      0-100
        fraud_flag:        bool
        pagerank_raw:      float
        voucher_count:     int
        explanation:       str
    """
    fraud_rings = detect_fraud_rings(G)
    fraud_flag = any(merchant_id in ring for ring in fraud_rings)

    pagerank_scores = compute_pagerank_scores(G)
    pr_raw = pagerank_scores.get(merchant_id, 0.0)

    # Normalize PageRank to 0-100
    all_scores = list(pagerank_scores.values())
    if max(all_scores) > 0:
        pr_normalized = (pr_raw / max(all_scores)) * 100
    else:
        pr_normalized = 0

    # Incoming edges = people who vouched FOR this merchant
    in_edges = list(G.in_edges(merchant_id, data=True))
    voucher_count = len(in_edges)

    # Diversity bonus: more relationship types = stronger signal
    rel_types = set(d.get("relationship") for _, _, d in in_edges)
    diversity_bonus = min(len(rel_types) * 5, 15)

    raw_score = pr_normalized + diversity_bonus
    fraud_penalty = 0.4 if fraud_flag else 0.0
    final_score = round(min(raw_score * (1 - fraud_penalty), 100))

    explanation = (
        f"Vouched by {voucher_count} merchants "
        f"({'FRAUD FLAG — mutual ring detected' if fraud_flag else 'no fraud detected'}). "
        f"Relationship diversity: {len(rel_types)} type(s)."
    )

    return {
        "social_score": final_score,
        "fraud_flag": fraud_flag,
        "pagerank_raw": round(pr_raw, 6),
        "voucher_count": voucher_count,
        "relationship_diversity": len(rel_types),
        "explanation": explanation
    }
```

---

## 7. Layer 2 — Psychometric Profiler (Gemini API)

**File: `backend/engines/psychometric.py`**

```python
import os
import json
import re
from typing import Dict, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Localized situational questions (Nepali business context)
PSYCHOMETRIC_QUESTIONS = [
    {
        "id": "q1",
        "trait": "risk_aversion",
        "question": "Raju runs a tea shop. His supplier offers double stock at half price, but payment is due in 3 days. He only has 60% of the money. What should he do?",
        "options": {
            "A": "Take the full deal and borrow the rest immediately",
            "B": "Take only what he can afford right now",
            "C": "Wait until next month when he has full payment",
            "D": "Negotiate a 2-week payment plan with the supplier"
        },
        "scoring": {"A": 20, "B": 60, "C": 80, "D": 70}
    },
    {
        "id": "q2",
        "trait": "conscientiousness",
        "question": "Sita's vegetable business had a bad month due to flooding. Her NEA electricity bill is due. She has just enough money for either the bill or restocking vegetables. What does she do?",
        "options": {
            "A": "Pay the electricity bill first — obligations come first",
            "B": "Restock vegetables — without stock there is no income",
            "C": "Pay half the electricity bill and use rest for stock",
            "D": "Borrow from a neighbor to pay the bill, restock with savings"
        },
        "scoring": {"A": 90, "B": 30, "C": 50, "D": 80}
    },
    {
        "id": "q3",
        "trait": "social_trust",
        "question": "A new merchant moves next to your shop and asks to borrow NPR 2,000 for one week. You know nothing about them. What do you do?",
        "options": {
            "A": "Lend the full amount — community helps community",
            "B": "Lend half and see if they repay before lending more",
            "C": "Politely decline — you don't know them yet",
            "D": "Ask a mutual acquaintance to vouch for them first"
        },
        "scoring": {"A": 60, "B": 70, "C": 50, "D": 90}
    },
    {
        "id": "q4",
        "trait": "resilience",
        "question": "Your main supplier suddenly increases prices by 20% due to fuel costs. Your margins will drop significantly. What is your first action?",
        "options": {
            "A": "Absorb the cost for now and hope prices drop",
            "B": "Immediately find an alternative supplier",
            "C": "Gradually increase your own prices while finding alternatives",
            "D": "Talk to other merchants and negotiate collectively with the supplier"
        },
        "scoring": {"A": 30, "B": 60, "C": 70, "D": 90}
    },
    {
        "id": "q5",
        "trait": "planning",
        "question": "You earn well during Dashain/Tihar festival season. What do you do with the extra income?",
        "options": {
            "A": "Spend it — the family deserves a good festival",
            "B": "Save all of it for slow months",
            "C": "Reinvest most in stock, save some for emergencies",
            "D": "Pay off any debts first, then save the rest"
        },
        "scoring": {"A": 20, "B": 60, "C": 80, "D": 90}
    }
]


def get_questions() -> List[Dict]:
    """Return questions for the frontend to display."""
    return [
        {
            "id": q["id"],
            "trait": q["trait"],
            "question": q["question"],
            "options": q["options"]
        }
        for q in PSYCHOMETRIC_QUESTIONS
    ]


def score_responses_deterministic(responses: Dict[str, str]) -> Dict:
    """
    Fast deterministic scoring (no API call needed for basic scoring).
    Used as fallback or for rapid prototyping.
    """
    trait_scores = {
        "risk_aversion": 0,
        "conscientiousness": 0,
        "social_trust": 0,
        "resilience": 0,
        "planning": 0
    }
    trait_counts = {k: 0 for k in trait_scores}

    for q in PSYCHOMETRIC_QUESTIONS:
        answer = responses.get(q["id"])
        if answer and answer in q["scoring"]:
            trait = q["trait"]
            trait_scores[trait] += q["scoring"][answer]
            trait_counts[trait] += 1

    # Normalize each trait to 0-100
    for trait in trait_scores:
        if trait_counts[trait] > 0:
            trait_scores[trait] = round(
                trait_scores[trait] / trait_counts[trait]
            )

    return trait_scores


def analyze_with_gemini(
    merchant_name: str,
    responses: Dict[str, str],
    trait_scores: Dict[str, int]
) -> Dict:
    """
    Use Gemini to provide deeper analysis and natural language explanation.
    Falls back gracefully if API is unavailable.
    """
    model = genai.GenerativeModel(
        os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    )

    # Build response summary for Gemini
    response_summary = []
    for q in PSYCHOMETRIC_QUESTIONS:
        answer = responses.get(q["id"], "no answer")
        option_text = q["options"].get(answer, "unknown")
        response_summary.append(
            f"Q ({q['trait']}): {q['question'][:80]}... → {answer}: {option_text}"
        )

    prompt = f"""You are a financial inclusion specialist scoring a merchant's psychometric profile for micro-credit assessment in Nepal.

Merchant: {merchant_name}

Their situational responses:
{chr(10).join(response_summary)}

Initial trait scores (0-100):
{json.dumps(trait_scores, indent=2)}

Analyze these responses and return ONLY a valid JSON object. No preamble, no markdown, no explanation outside the JSON.

Return exactly this structure:
{{
  "conscientiousness": <integer 0-100>,
  "risk_aversion": <integer 0-100>,
  "social_trust": <integer 0-100>,
  "resilience": <integer 0-100>,
  "planning": <integer 0-100>,
  "psychometric_score": <weighted average integer 0-100>,
  "credit_personality": "<one of: Cautious Planner, Community Builder, Risk Taker, Resilient Adapter, Conservative Saver>",
  "insight": "<1 sentence insight about this merchant's financial personality in context of Nepal>",
  "red_flags": "<any concerning patterns, or 'none'>",
  "strengths": "<key strength for lending decisions>"
}}"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Clean any markdown fences
        raw = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)

        # Validate required fields exist
        required = [
            "conscientiousness", "risk_aversion", "social_trust",
            "resilience", "planning", "psychometric_score"
        ]
        for field in required:
            if field not in result:
                result[field] = trait_scores.get(field, 50)

        return result

    except Exception as e:
        # Graceful fallback: use deterministic scores + placeholder text
        weighted = round(
            trait_scores.get("conscientiousness", 50) * 0.30 +
            trait_scores.get("risk_aversion", 50) * 0.25 +
            trait_scores.get("social_trust", 50) * 0.20 +
            trait_scores.get("resilience", 50) * 0.15 +
            trait_scores.get("planning", 50) * 0.10
        )
        return {
            **trait_scores,
            "psychometric_score": weighted,
            "credit_personality": "Cautious Planner",
            "insight": "Profile computed from deterministic scoring (Gemini unavailable).",
            "red_flags": "none",
            "strengths": "Consistent responses across situational questions.",
            "error": str(e)
        }


def run_psychometric_assessment(
    merchant_id: str,
    merchant_name: str,
    responses: Dict[str, str]
) -> Dict:
    """Main function called by the API endpoint."""
    trait_scores = score_responses_deterministic(responses)
    gemini_result = analyze_with_gemini(merchant_name, responses, trait_scores)

    return {
        "merchant_id": merchant_id,
        "trait_scores": {
            "conscientiousness": gemini_result.get("conscientiousness", trait_scores["conscientiousness"]),
            "risk_aversion": gemini_result.get("risk_aversion", trait_scores["risk_aversion"]),
            "social_trust": gemini_result.get("social_trust", trait_scores["social_trust"]),
            "resilience": gemini_result.get("resilience", trait_scores["resilience"]),
            "planning": gemini_result.get("planning", trait_scores["planning"])
        },
        "psychometric_score": gemini_result.get("psychometric_score", 50),
        "credit_personality": gemini_result.get("credit_personality", "Unknown"),
        "insight": gemini_result.get("insight", ""),
        "red_flags": gemini_result.get("red_flags", "none"),
        "strengths": gemini_result.get("strengths", "")
    }
```

---

## 8. Layer 3 — Behavioral Proxy Engine

**File: `backend/engines/behavioral.py`**

```python
import math
from typing import Dict, List
from datetime import datetime


# Harvest calendar: month numbers when revenue should peak
HARVEST_CALENDAR = {
    "vegetables": [1, 2, 3, 9, 10, 11],
    "dairy":      [4, 5, 6, 10, 11, 12],
    "tea_shop":   list(range(1, 13)),
    "clothing":   [10, 11, 12, 1, 2],
    "hardware":   [3, 4, 5, 9, 10],
    "pharmacy":   list(range(1, 13)),
}


def score_transactional_consistency(revenue_history: List[Dict]) -> int:
    """
    Scores revenue consistency using coefficient of variation.
    Low variance relative to mean = high score.
    Formula: score = 100 * e^(-CV) where CV = std_dev / mean
    """
    if not revenue_history:
        return 0

    amounts = [r["amount"] for r in revenue_history]
    mean = sum(amounts) / len(amounts)
    if mean == 0:
        return 0

    variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean

    score = 100 * math.exp(-cv)
    return round(min(score, 100))


def score_obligation_fulfillment(utility_payments: List[Dict]) -> int:
    """
    Scores bill payment reliability.
    Penalizes late and partial payments.
    """
    if not utility_payments:
        return 0

    total = len(utility_payments)
    on_time_count = sum(1 for p in utility_payments if p.get("paid_on_time"))
    partial_count = sum(1 for p in utility_payments if p.get("partial_payment"))

    base_rate = on_time_count / total
    partial_penalty = (partial_count / total) * 0.3

    score = (base_rate - partial_penalty) * 100
    return round(max(score, 0))


def score_airtime_consistency(airtime_topups: List[Dict]) -> int:
    """
    Scores telecom top-up regularity.
    Regular, moderate top-ups indicate stable income.
    """
    if not airtime_topups:
        return 30  # Neutral score if no data

    monthly_amounts = [t["total_amount"] for t in airtime_topups]
    mean = sum(monthly_amounts) / len(monthly_amounts)
    if mean == 0:
        return 0

    variance = sum((x - mean) ** 2 for x in monthly_amounts) / len(monthly_amounts)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean

    # Regular top-up pattern = positive signal
    score = 100 * math.exp(-cv * 0.8)
    return round(min(score, 100))


def score_cash_flow_seasonality(
    revenue_history: List[Dict],
    business_type: str
) -> int:
    """
    Scores how well revenue aligns with expected harvest/business cycles.
    A vegetable vendor with revenue spikes in harvest months
    is behaving as expected — positive signal.
    Unexpected spikes may indicate anomaly.
    """
    if not revenue_history:
        return 50

    harvest_months = HARVEST_CALENDAR.get(business_type, list(range(1, 13)))

    expected_high = []
    actual_amounts = []

    for entry in revenue_history:
        try:
            month_num = datetime.strptime(entry["month"], "%Y-%m").month
        except ValueError:
            continue
        is_harvest = 1 if month_num in harvest_months else 0
        expected_high.append(is_harvest)
        actual_amounts.append(entry["amount"])

    if not actual_amounts:
        return 50

    mean_amount = sum(actual_amounts) / len(actual_amounts)
    correct_peaks = 0
    total_comparisons = len(actual_amounts)

    for i, amount in enumerate(actual_amounts):
        is_high = amount > mean_amount
        expected = expected_high[i] == 1
        if is_high == expected:
            correct_peaks += 1

    alignment_rate = correct_peaks / total_comparisons
    return round(alignment_rate * 100)


def score_khata_repayment(khata_entries: List[Dict]) -> int:
    """
    Scores physical ledger repayment behavior.
    Used for cash-only merchants with no digital footprint.
    """
    if not khata_entries:
        return 0  # No data, not scored (different from zero)

    debt_taken = [e for e in khata_entries if e.get("type") == "debt_taken"]
    if not debt_taken:
        return 50

    repaid = [e for e in debt_taken if e.get("repaid")]
    repayment_rate = len(repaid) / len(debt_taken)

    # Speed of repayment bonus
    repay_days = [e["days_to_repay"] for e in repaid if e.get("days_to_repay")]
    if repay_days:
        avg_days = sum(repay_days) / len(repay_days)
        speed_factor = math.exp(-0.1 * avg_days / 30)
    else:
        speed_factor = 0.5

    score = repayment_rate * 100 * (0.7 + 0.3 * speed_factor)
    return round(min(score, 100))


def compute_behavioral_score(merchant: Dict) -> Dict:
    """
    Compute all behavioral sub-scores and combine into behavioral_score.
    """
    tc = score_transactional_consistency(merchant.get("revenue_history", []))
    ofs = score_obligation_fulfillment(merchant.get("utility_payments", []))
    ats = score_airtime_consistency(merchant.get("airtime_topups", []))
    css = score_cash_flow_seasonality(
        merchant.get("revenue_history", []),
        merchant.get("business_type", "tea_shop")
    )
    krs = score_khata_repayment(merchant.get("khata_entries", []))

    # If no khata data (digital merchant), redistribute weight
    has_khata = len(merchant.get("khata_entries", [])) > 0

    if has_khata:
        weights = {"tc": 0.25, "ofs": 0.25, "ats": 0.15, "css": 0.15, "krs": 0.20}
    else:
        weights = {"tc": 0.35, "ofs": 0.30, "ats": 0.20, "css": 0.15, "krs": 0.00}

    behavioral_score = round(
        tc * weights["tc"] +
        ofs * weights["ofs"] +
        ats * weights["ats"] +
        css * weights["css"] +
        krs * weights["krs"]
    )

    return {
        "behavioral_score": behavioral_score,
        "sub_scores": {
            "transactional_consistency": tc,
            "obligation_fulfillment": ofs,
            "airtime_consistency": ats,
            "cash_flow_seasonality": css,
            "khata_repayment": krs
        },
        "has_khata_data": has_khata
    }
```

---

## 9. Score Fusion Engine

**File: `backend/engines/fusion.py`**

```python
import math
from typing import Dict


def detect_segment(merchant: Dict, behavioral_data_points: int) -> str:
    """Classify merchant into scoring segment."""
    has_digital = merchant.get("esewa_registered") or merchant.get("khalti_registered")
    has_khata = len(merchant.get("khata_entries", [])) > 0

    if has_digital and behavioral_data_points > 12:
        return "digital_native"
    elif has_khata and not has_digital:
        return "cash_merchant"
    else:
        return "new_merchant"


def get_segment_weights(segment: str) -> Dict[str, float]:
    """Dynamic weights per merchant segment."""
    weights = {
        "digital_native": {
            "social": 0.25,
            "psychometric": 0.20,
            "behavioral": 0.55
        },
        "cash_merchant": {
            "social": 0.35,
            "psychometric": 0.30,
            "behavioral": 0.35
        },
        "new_merchant": {
            "social": 0.45,
            "psychometric": 0.40,
            "behavioral": 0.15
        }
    }
    return weights.get(segment, weights["new_merchant"])


def compute_confidence(
    data_points: int,
    source_count: int,
    fraud_flag: bool,
    psychometric_complete: bool
) -> float:
    """
    Confidence = how much we trust the score itself.
    Lower confidence = wider error band, lower eligible loan amount.

    Factors:
    - data_points:           more history = more confidence
    - source_count:          how many distinct data sources contributed
    - fraud_flag:            social graph fraud detection
    - psychometric_complete: did merchant complete all questions?
    """
    # Data recency weight (more data points = higher base)
    data_confidence = min(data_points / 18, 1.0)  # 18 months = full confidence

    # Source diversity (max 4 sources: social, psychometric, utility, wallet)
    source_confidence = min(source_count / 4, 1.0)

    # Psychometric bonus
    psychometric_bonus = 0.1 if psychometric_complete else 0.0

    # Fraud penalty
    fraud_penalty = 0.3 if fraud_flag else 0.0

    confidence = (
        data_confidence * 0.5 +
        source_confidence * 0.4 +
        psychometric_bonus
    ) * (1 - fraud_penalty)

    return round(min(max(confidence, 0.1), 1.0), 2)


def get_lending_tier(final_score: int, confidence: float) -> Dict:
    """Map score + confidence to a lending tier."""
    # Adjust effective score by confidence
    effective = final_score * confidence

    if effective >= 65:
        return {
            "tier": "A",
            "label": "Full credit eligible",
            "max_loan_npr": 50000,
            "interest_rate": "12% per annum",
            "color": "green"
        }
    elif effective >= 45:
        return {
            "tier": "B",
            "label": "Small loan eligible",
            "max_loan_npr": 15000,
            "interest_rate": "16% per annum",
            "color": "amber"
        }
    elif effective >= 28:
        return {
            "tier": "C",
            "label": "Building profile",
            "max_loan_npr": 0,
            "interest_rate": "N/A",
            "color": "orange"
        }
    else:
        return {
            "tier": "D",
            "label": "Insufficient data",
            "max_loan_npr": 0,
            "interest_rate": "N/A",
            "color": "red"
        }


def generate_improvement_pathway(
    tier: str,
    social_score: int,
    psychometric_score: int,
    behavioral_score: int,
    behavioral_sub: Dict
) -> list:
    """Generate actionable next steps for the merchant."""
    steps = []

    if tier in ["C", "D"]:
        steps.append("Record at least 10 khata (ledger) entries via USSD *333#")

    if behavioral_sub.get("obligation_fulfillment", 100) < 70:
        steps.append("Pay NEA electricity bill on time for next 3 months")

    if behavioral_sub.get("transactional_consistency", 100) < 60:
        steps.append("Maintain consistent monthly sales volume — avoid large gaps")

    if social_score < 50:
        steps.append("Ask 2 trusted suppliers to vouch for you in the app")

    if psychometric_score < 50:
        steps.append("Complete the full 5-question financial personality assessment")

    if not steps:
        steps.append("Maintain current habits — your score updates monthly")

    return steps


def fuse_scores(
    merchant: Dict,
    social_result: Dict,
    psychometric_result: Dict,
    behavioral_result: Dict
) -> Dict:
    """
    Main fusion function. Combines all three layers into a final score.
    """
    social_score = social_result.get("social_score", 0)
    psychometric_score = psychometric_result.get("psychometric_score", 0)
    behavioral_score = behavioral_result.get("behavioral_score", 0)
    fraud_flag = social_result.get("fraud_flag", False)

    # Count data points (months of behavioral history)
    data_points = len(merchant.get("revenue_history", []))

    # Count distinct source types contributing
    sources = 0
    if social_result.get("voucher_count", 0) > 0: sources += 1
    if psychometric_score > 0: sources += 1
    if behavioral_result.get("sub_scores", {}).get("obligation_fulfillment", 0) > 0:
        sources += 1
    if merchant.get("esewa_registered") or merchant.get("khalti_registered"):
        sources += 1

    segment = detect_segment(merchant, data_points)
    weights = get_segment_weights(segment)

    raw_score = (
        weights["social"] * social_score +
        weights["psychometric"] * psychometric_score +
        weights["behavioral"] * behavioral_score
    )

    confidence = compute_confidence(
        data_points=data_points,
        source_count=sources,
        fraud_flag=fraud_flag,
        psychometric_complete=psychometric_score > 0
    )

    final_score = round(min(raw_score, 100))
    lending_tier = get_lending_tier(final_score, confidence)

    improvement = generate_improvement_pathway(
        tier=lending_tier["tier"],
        social_score=social_score,
        psychometric_score=psychometric_score,
        behavioral_score=behavioral_score,
        behavioral_sub=behavioral_result.get("sub_scores", {})
    )

    return {
        "merchant_id": merchant["merchant_id"],
        "merchant_name": merchant["name"],
        "final_score": final_score,
        "confidence": confidence,
        "confidence_pct": round(confidence * 100),
        "segment": segment,
        "weights_used": weights,
        "sub_scores": {
            "social": social_score,
            "psychometric": psychometric_score,
            "behavioral": behavioral_score
        },
        "behavioral_detail": behavioral_result.get("sub_scores", {}),
        "lending_tier": lending_tier,
        "fraud_flag": fraud_flag,
        "improvement_pathway": improvement,
        "credit_personality": psychometric_result.get("credit_personality", ""),
        "psychometric_insight": psychometric_result.get("insight", ""),
        "data_sources_used": sources
    }
```

---

## 10. FastAPI Backend

**File: `backend/main.py`**

```python
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import networkx as nx

from engines.social_graph import build_graph, score_merchant_social
from engines.psychometric import run_psychometric_assessment, get_questions
from engines.behavioral import compute_behavioral_score
from engines.fusion import fuse_scores

app = FastAPI(
    title="TrustBridge API",
    description="Alternative Trust Middleware for Unbanked Merchants",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Load mock data and build graph once at startup
with open("data/mock_merchants.json", "r", encoding="utf-8") as f:
    MERCHANTS = json.load(f)

MERCHANT_MAP = {m["merchant_id"]: m for m in MERCHANTS}
GRAPH = build_graph(MERCHANTS)


# ---- Pydantic Models ----

class PsychometricRequest(BaseModel):
    merchant_id: str
    responses: Dict[str, str]  # {"q1": "A", "q2": "D", ...}


class ScoreRequest(BaseModel):
    merchant_id: str
    psychometric_responses: Optional[Dict[str, str]] = None


# ---- Endpoints ----

@app.get("/")
def root():
    return {
        "name": "TrustBridge",
        "version": "1.0.0",
        "status": "running",
        "merchants_loaded": len(MERCHANTS)
    }


@app.get("/merchants")
def list_merchants():
    return [
        {
            "merchant_id": m["merchant_id"],
            "name": m["name"],
            "district": m["district"],
            "business_type": m["business_type"],
            "digital_footprint": m["digital_footprint"]
        }
        for m in MERCHANTS
    ]


@app.get("/merchants/{merchant_id}")
def get_merchant(merchant_id: str):
    m = MERCHANT_MAP.get(merchant_id)
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return m


@app.get("/psychometric/questions")
def psychometric_questions():
    return get_questions()


@app.post("/score/{merchant_id}")
def compute_full_score(merchant_id: str, body: ScoreRequest):
    merchant = MERCHANT_MAP.get(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    # Layer 1: Social graph
    social_result = score_merchant_social(merchant_id, GRAPH)

    # Layer 2: Psychometric (use provided responses or defaults)
    responses = body.psychometric_responses or {}
    if responses:
        psychometric_result = run_psychometric_assessment(
            merchant_id, merchant["name"], responses
        )
    else:
        psychometric_result = {"psychometric_score": 0, "credit_personality": "Not assessed"}

    # Layer 3: Behavioral
    behavioral_result = compute_behavioral_score(merchant)

    # Fusion
    final = fuse_scores(merchant, social_result, psychometric_result, behavioral_result)

    return final


@app.get("/graph/stats")
def graph_stats():
    return {
        "nodes": GRAPH.number_of_nodes(),
        "edges": GRAPH.number_of_edges(),
        "density": round(nx.density(GRAPH), 4),
        "avg_clustering": round(nx.average_clustering(GRAPH.to_undirected()), 4)
    }


@app.get("/health")
def health():
    return {"status": "ok"}
```

---

## 11. PostgreSQL Database Schema

**File: `backend/db/schema.sql`**

```sql
-- Create database
CREATE DATABASE trustbridge;
\c trustbridge;

-- Merchants table
CREATE TABLE merchants (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    district VARCHAR(50),
    business_type VARCHAR(50),
    phone VARCHAR(15),
    digital_footprint BOOLEAN DEFAULT FALSE,
    esewa_registered BOOLEAN DEFAULT FALSE,
    khalti_registered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trust scores (time-series — one row per scoring event)
CREATE TABLE trust_scores (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(10) REFERENCES merchants(merchant_id),
    final_score INTEGER CHECK (final_score BETWEEN 0 AND 100),
    confidence DECIMAL(4,2),
    segment VARCHAR(20),
    social_score INTEGER,
    psychometric_score INTEGER,
    behavioral_score INTEGER,
    lending_tier VARCHAR(2),
    fraud_flag BOOLEAN DEFAULT FALSE,
    full_result JSONB,  -- stores the complete score object
    scored_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast merchant lookup
CREATE INDEX idx_trust_scores_merchant ON trust_scores(merchant_id);
CREATE INDEX idx_trust_scores_time ON trust_scores(scored_at DESC);

-- Psychometric responses
CREATE TABLE psychometric_responses (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(10) REFERENCES merchants(merchant_id),
    responses JSONB NOT NULL,
    trait_scores JSONB,
    credit_personality VARCHAR(50),
    assessed_at TIMESTAMP DEFAULT NOW()
);
```

Run it:

```bash
psql -U postgres -f backend/db/schema.sql
```

---

## 12. Streamlit Frontend

**File: `frontend/app.py`**

```python
import streamlit as st
import requests
import plotly.graph_objects as go
import json

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="TrustBridge",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 TrustBridge")
st.caption("Alternative Trust Middleware — Financial Inclusion for Unbanked Merchants")
st.divider()

# ---- Sidebar: Merchant selector ----
with st.sidebar:
    st.header("Select Merchant")
    try:
        merchants = requests.get(f"{API_URL}/merchants").json()
        names = {
            f"{m['name']} ({m['merchant_id']})": m["merchant_id"]
            for m in merchants
        }
        selected_label = st.selectbox("Merchant", list(names.keys()))
        merchant_id = names[selected_label]
        selected_merchant = requests.get(f"{API_URL}/merchants/{merchant_id}").json()
    except Exception:
        st.error("Backend not running. Start with: uvicorn main:app --reload")
        st.stop()

    st.divider()
    st.metric("District", selected_merchant["district"])
    st.metric("Business", selected_merchant["business_type"].replace("_", " ").title())
    st.metric("Digital Footprint", "Yes ✓" if selected_merchant["digital_footprint"] else "No ✗")

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs([
    "📋 Psychometric Assessment",
    "📊 Trust Score",
    "🔗 Social Graph"
])

# ---- Tab 1: Psychometric ----
with tab1:
    st.subheader("Financial Personality Assessment")
    st.info("Answer all 5 situational questions. Powered by Gemini 2.5 Flash-Lite API.")

    questions = requests.get(f"{API_URL}/psychometric/questions").json()
    responses = {}

    for q in questions:
        st.markdown(f"**{q['question']}**")
        options = q["options"]
        choice = st.radio(
            label=f"_{q['trait'].replace('_', ' ').title()}_",
            options=list(options.keys()),
            format_func=lambda x, opts=options: f"{x}: {opts[x]}",
            horizontal=False,
            key=q["id"]
        )
        responses[q["id"]] = choice
        st.divider()

    if st.button("Submit Assessment →", type="primary"):
        st.session_state["psychometric_responses"] = responses
        st.success("Responses saved. Go to 'Trust Score' tab to compute full score.")

# ---- Tab 2: Trust Score ----
with tab2:
    st.subheader("Compute Trust Score")

    psychometric_responses = st.session_state.get("psychometric_responses", {})
    if not psychometric_responses:
        st.warning("Complete the psychometric assessment first for a full score.")

    if st.button("Compute Full Trust Score ▶", type="primary"):
        with st.spinner("Running all three scoring engines..."):
            payload = {
                "merchant_id": merchant_id,
                "psychometric_responses": psychometric_responses or None
            }
            result = requests.post(
                f"{API_URL}/score/{merchant_id}",
                json=payload
            ).json()
            st.session_state["score_result"] = result

    result = st.session_state.get("score_result")
    if result:
        # Main score display
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Trust Score", f"{result['final_score']}/100")
        col2.metric("Confidence", f"{result['confidence_pct']}%")
        col3.metric("Lending Tier", result['lending_tier']['tier'])
        col4.metric(
            "Max Loan",
            f"NPR {result['lending_tier']['max_loan_npr']:,}" if result['lending_tier']['max_loan_npr'] > 0 else "N/A"
        )

        if result.get("fraud_flag"):
            st.error("⚠️ FRAUD FLAG: This merchant appears in a mutual vouching ring.")

        st.divider()

        # Sub-score radar chart
        sub = result["sub_scores"]
        behavioral_detail = result.get("behavioral_detail", {})

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Social", "Psychometric", "Behavioral"],
            y=[sub["social"], sub["psychometric"], sub["behavioral"]],
            marker_color=["#7F77DD", "#1D9E75", "#BA7517"],
            text=[sub["social"], sub["psychometric"], sub["behavioral"]],
            textposition="auto"
        ))
        fig.update_layout(
            title="Three-layer sub-scores",
            yaxis_range=[0, 100],
            height=320,
            margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Behavioral detail
        if behavioral_detail:
            st.subheader("Behavioral breakdown")
            b_cols = st.columns(len(behavioral_detail))
            for i, (k, v) in enumerate(behavioral_detail.items()):
                b_cols[i].metric(k.replace("_", " ").title(), v)

        # Psychometric insight
        if result.get("credit_personality"):
            st.info(
                f"**Credit Personality:** {result['credit_personality']}  \n"
                f"{result.get('psychometric_insight', '')}"
            )

        # Improvement pathway
        st.subheader("Improvement pathway")
        for step in result.get("improvement_pathway", []):
            st.markdown(f"→ {step}")

        # Raw JSON
        with st.expander("Raw score JSON (for API integration)"):
            st.json(result)

# ---- Tab 3: Social Graph ----
with tab3:
    st.subheader("Community Vouching Network")
    stats = requests.get(f"{API_URL}/graph/stats").json()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Merchants", stats["nodes"])
    c2.metric("Vouch connections", stats["edges"])
    c3.metric("Network density", stats["density"])
    c4.metric("Avg clustering", stats["avg_clustering"])

    m_data = requests.get(f"{API_URL}/merchants/{merchant_id}").json()
    vouchers = m_data.get("vouchers", [])

    if vouchers:
        st.markdown(f"**{selected_merchant['name']}** is vouched by {len(vouchers)} merchant(s):")
        for v in vouchers:
            voucher_merchant = next(
                (m for m in merchants if m["merchant_id"] == v["voucher_id"]), None
            )
            name = voucher_merchant["name"] if voucher_merchant else v["voucher_id"]
            st.markdown(
                f"- **{name}** ({v['relationship'].replace('_', ' ')}) "
                f"· {v['months_known']} months · trust score: {v['voucher_trust_score']}"
            )
    else:
        st.info("No vouchers recorded for this merchant yet.")
```

---

## 13. Running the Full Application

### Terminal 1 — Start the backend

```bash
# From project root, activate venv
source venv/bin/activate

# Move into backend folder
cd backend

# Start FastAPI
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete.
```

Test it's working: open [http://localhost:8000/docs](http://localhost:8000/docs) — this gives you the full interactive Swagger UI.

### Terminal 2 — Start the frontend

```bash
# From project root, new terminal
source venv/bin/activate

# Start Streamlit
streamlit run frontend/app.py
```

Streamlit will open automatically at [http://localhost:8501](http://localhost:8501).

### Terminal 3 — Generate mock data (one time only)

```bash
source venv/bin/activate
python backend/data/generate_mock.py
```

---

## 14. Demo Script (Hackathon Presentation)

Follow this exact 5-minute flow during your demo:

**Minute 1 — The problem (talk, no demo)**
> "Over 90% of Nepal's economic backbone is MSMEs. Sita is a vegetable vendor in Bhaktapur. She's been paying her NEA bill on time for 3 years, buying from the same suppliers every week. But eSewa sees zero. The bank sees zero. She's credit-invisible."

**Minute 2 — Onboarding (show Streamlit sidebar)**
> Select Sita's merchant profile. Point out: district, business type, no digital footprint.
> "Three ways to onboard: digital wallet API, USSD khata entry, or agent visit. Sita used USSD."

**Minute 3 — Psychometric assessment (show Tab 1)**
> Walk through 2–3 questions live. Choose answers that reflect a cautious, community-oriented merchant. Submit.
> "This runs against Gemini 2.5 Flash-Lite API in real time — no paid subscription required."

**Minute 4 — Full score (show Tab 2)**
> Click "Compute Full Trust Score". Show the three sub-scores populating.
> "Three engines fired: social graph via NetworkX PageRank, psychometric via Gemini, behavioral via bill payment and seasonality analysis."
> Point to lending tier: "Sita qualifies for NPR 12,000 working capital. First time in her life."

**Minute 5 — Architecture + vision**
> Show the improvement pathway. 
> "This score updates dynamically — every khata entry, every bill payment, moves the number. The score is portable. Sita owns it. She can show it to Khalti, to an insurance company, to any fintech that plugs into TrustBridge's open API."

---

## 15. Deployment on Render.com (Free)

### Step 1 — Create `render.yaml` in project root

```yaml
services:
  - type: web
    name: trustbridge-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false  # Enter manually in Render dashboard
      - key: GEMINI_MODEL
        value: gemini-2.5-flash-lite
```

### Step 2 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial TrustBridge commit"
git remote add origin https://github.com/yourusername/trustbridge.git
git push -u origin main
```

### Step 3 — Deploy on Render

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your GitHub repo
3. Set environment variable: `GEMINI_API_KEY` = your key
4. Click **Deploy**

Free tier gives you a live URL like `https://trustbridge-api.onrender.com` within 5 minutes.

Update your Streamlit `API_URL` to this URL for the live demo.

---

## 16. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError` | venv not activated | Run `source venv/bin/activate` |
| `429 Too Many Requests` from Gemini | Hit free rate limit | Switch to `gemini-2.5-flash-lite` in `.env`, or add `time.sleep(1)` between calls |
| `Connection refused` on port 8000 | Backend not running | Start `uvicorn main:app --reload` in Terminal 1 |
| PostgreSQL connection error | DB not running | Run `brew services start postgresql` (macOS) or `sudo systemctl start postgresql` (Linux) |
| Graph has no nodes | Mock data not generated | Run `python backend/data/generate_mock.py` first |
| Gemini returns non-JSON | Model preamble in response | Already handled by `re.sub` cleanup in `psychometric.py` |
| Streamlit shows old score | Cached state | Click the three dots → Clear cache, or add `?v=2` to URL |

---

*Built for the Alternative Trust Layer for Financial Inclusion Hackathon Challenge · May 2026*
*Stack: FastAPI · NetworkX · Gemini API · PostgreSQL · Streamlit · Open Source · NPR 0 cost*
