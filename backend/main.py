import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
import networkx as nx

from db import (
    init_db, seed_merchants, get_all_merchants, get_all_merchants_full,
    get_merchant_full, save_trust_score, save_psychometric,
    get_score_history, get_vouch_neighbors, get_graph_data_for_d3
)
from engines.social_graph import build_graph_from_edges, score_merchant_social
from engines.psychometric import run_psychometric_assessment, get_questions
from engines.behavioral import compute_behavioral_score
from engines.fusion import fuse_scores
from engines.inference import predict

# ── Startup ───────────────────────────────────────────────────────────────────

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "seed_merchants.json")

GRAPH: nx.DiGraph = nx.DiGraph()
MERCHANT_CACHE: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global GRAPH, MERCHANT_CACHE
    await init_db()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        seed_data = json.load(f)
    await seed_merchants(seed_data)

    # Load all merchants into in-memory cache for graph + scoring
    merchants = await get_all_merchants_full()
    MERCHANT_CACHE = {m["merchant_id"]: m for m in merchants}

    # Build graph from DB edges
    graph_data = await get_graph_data_for_d3()
    GRAPH = build_graph_from_edges(merchants, graph_data["edges"])
    print(f"✅ Graph: {GRAPH.number_of_nodes()} nodes, {GRAPH.number_of_edges()} edges")
    yield
    from db import close_pool
    await close_pool()


app = FastAPI(
    title="TrustBridge API",
    description="Alternative Trust Middleware for Unbanked Merchants — Nepal",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# ── Pydantic models ───────────────────────────────────────────────────────────

class ScoreRequest(BaseModel):
    merchant_id: str
    psychometric_responses: Optional[Dict[str, str]] = None
    lang: Optional[str] = "ne"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "TrustBridge",
        "version": "2.0.0",
        "status": "running",
        "merchants_loaded": len(MERCHANT_CACHE),
        "graph_nodes": GRAPH.number_of_nodes(),
        "graph_edges": GRAPH.number_of_edges(),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/merchants")
async def list_merchants():
    rows = await get_all_merchants()
    return [
        {
            "merchant_id": r["merchant_id"],
            "name": r["owner_name"],
            "legal_name": r["legal_name"],
            "district": r["location"],
            "business_type": r["business_type"],
            "segment": r["segment"],
            "months_active": r["months_active"],
            "digital_footprint": r["digital_footprint"],
            "esewa_registered": r["esewa_registered"],
            "khalti_registered": r["khalti_registered"],
        }
        for r in rows
    ]


@app.get("/merchants/{merchant_id}")
async def get_merchant(merchant_id: str):
    m = await get_merchant_full(merchant_id)
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found")
    meta = m["business_metadata"]
    return {
        **m,
        "name": meta["owner_name"],
        "district": meta["location"],
        "business_type": meta["business_type"],
        "months_active": meta["months_active"],
        "digital_footprint": meta.get("segment", "") == "Digital Native",
        "esewa_registered": meta.get("segment", "") == "Digital Native",
        "khalti_registered": False,
    }


@app.get("/psychometric/questions")
def psychometric_questions(merchant_id: str = None, lang: str = "ne"):
    return get_questions(lang=lang, seed=merchant_id)


@app.post("/score/{merchant_id}")
async def compute_full_score(merchant_id: str, body: ScoreRequest):
    merchant = MERCHANT_CACHE.get(merchant_id)
    if not merchant:
        merchant = await get_merchant_full(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    # Layer 1: Social graph
    social_result = score_merchant_social(merchant_id, GRAPH, merchant)

    # Layer 2: Psychometric
    responses = body.psychometric_responses or {}
    if responses:
        psychometric_result = run_psychometric_assessment(
            merchant_id,
            merchant["business_metadata"]["owner_name"],
            responses,
            lang=body.lang or "ne",
        )
    else:
        psychometric_result = {
            "psychometric_score": 0,
            "credit_personality": "Not assessed",
            "credit_personality_ne": "मूल्याङ्कन गरिएको छैन",
            "insight": "",
            "red_flags": "none",
            "strengths": "",
            "xp_earned": 0,
            "badges_unlocked": [],
        }

    # Layer 3: Behavioral
    behavioral_result = compute_behavioral_score(merchant)

    # Fusion
    final = fuse_scores(merchant, social_result, psychometric_result, behavioral_result)

    # Attach gamification
    final["xp_earned"] = psychometric_result.get("xp_earned", 0)
    final["badges_unlocked"] = psychometric_result.get("badges_unlocked", [])
    final["hallucination_corrections"] = psychometric_result.get("hallucination_corrections", [])
    final["deterministic_baseline"] = psychometric_result.get("deterministic_baseline", {})

    # Persist to PostgreSQL
    await save_trust_score(merchant_id, final)
    if responses:
        await save_psychometric(merchant_id, responses, psychometric_result)

    # Attach score history
    history = await get_score_history(merchant_id)
    final["score_history"] = [
        {
            "score": h["final_score"],
            "tier": h["lending_tier"],
            "date": h["scored_at"].isoformat() if h.get("scored_at") else None,
        }
        for h in history
    ]

    return final


@app.get("/score/{merchant_id}/history")
async def score_history(merchant_id: str):
    history = await get_score_history(merchant_id, limit=10)
    return {
        "merchant_id": merchant_id,
        "history": [
            {
                "final_score": h["final_score"],
                "confidence": float(h["confidence"]) if h["confidence"] else None,
                "lending_tier": h["lending_tier"],
                "fraud_flag": h["fraud_flag"],
                "social_score": h["social_score"],
                "psychometric_score": h["psychometric_score"],
                "behavioral_score": h["behavioral_score"],
                "scored_at": h["scored_at"].isoformat() if h.get("scored_at") else None,
            }
            for h in history
        ],
    }


@app.get("/score/{merchant_id}/ml")
def ml_score(merchant_id: str):
    merchant = MERCHANT_CACHE.get(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    try:
        return predict(merchant)
    except Exception as e:
        return {"repayment_risk": "unknown", "confidence": 0, "anomaly_flag": False, "probabilities": {}, "error": str(e)}


@app.get("/graph/stats")
def graph_stats():
    return {
        "nodes": GRAPH.number_of_nodes(),
        "edges": GRAPH.number_of_edges(),
        "density": round(nx.density(GRAPH), 4),
        "avg_clustering": round(nx.average_clustering(GRAPH.to_undirected()), 4),
    }


@app.get("/graph/neighbors/{merchant_id}")
async def get_graph_neighbors(merchant_id: str):
    data = await get_vouch_neighbors(merchant_id)
    return data


@app.get("/graph/d3")
async def graph_d3():
    """Full graph data for D3 force visualization."""
    return await get_graph_data_for_d3()


@app.post("/ml-score")
def ml_score_merchant(merchant: dict):
    result = predict(merchant)
    return result

@app.get("/ml-score/{merchant_id}")
def ml_score_by_id(merchant_id: str):
    merchant = MERCHANT_CACHE.get(merchant_id)
    if not merchant:
        raise HTTPException(404, "Merchant not found")
    return predict(merchant)

@app.get("/score/{merchant_id}/latest")
async def get_latest_score(merchant_id: str):
    history = await get_score_history(merchant_id, limit=1)
    if not history:
        return None
    return history[0]["full_result"] if "full_result" in history[0] else None