import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import networkx as nx

from engines.social_graph import build_graph, score_merchant_social
from engines.psychometric import run_psychometric_assessment, get_questions
from engines.behavioral import compute_behavioral_score
from engines.fusion import fuse_scores
from engines.inference import predict


app = FastAPI(
    title="TrustBridge API",
    description="Alternative Trust Middleware for Unbanked Merchants — Nepal",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Load mock data at startup
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "mock_merchants.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    MERCHANTS = json.load(f)

MERCHANT_MAP = {m["merchant_id"]: m for m in MERCHANTS}
GRAPH = build_graph(MERCHANTS)


# ── Pydantic models ──────────────────────────────────────────────────────────


class PsychometricRequest(BaseModel):
    merchant_id: str
    responses: Dict[str, str]


class ScoreRequest(BaseModel):
    merchant_id: str
    psychometric_responses: Optional[Dict[str, str]] = None
    lang: Optional[str] = "ne"


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/")
def root():
    return {
        "name": "TrustBridge",
        "version": "1.0.0",
        "status": "running",
        "merchants_loaded": len(MERCHANTS),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/merchants")
def list_merchants():
    return [
        {
            "merchant_id": m["merchant_id"],
            "name": m["business_metadata"]["owner_name"],
            "legal_name": m["business_metadata"]["legal_name"],
            "district": m["business_metadata"]["location"],
            "business_type": m["business_metadata"]["business_type"],
            "segment": m["business_metadata"]["segment"],
            "months_active": m["business_metadata"]["months_active"],
            "digital_footprint": m["business_metadata"].get("segment", "")
            == "Digital Native",
            "esewa_registered": m["business_metadata"].get("segment", "")
            == "Digital Native",
            "khalti_registered": False,
        }
        for m in MERCHANTS
    ]


@app.get("/merchants/{merchant_id}")
def get_merchant(merchant_id: str):
    m = MERCHANT_MAP.get(merchant_id)
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
def compute_full_score(merchant_id: str, body: ScoreRequest):
    merchant = MERCHANT_MAP.get(merchant_id)
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

    # Attach gamification to final response
    final["xp_earned"] = psychometric_result.get("xp_earned", 0)
    final["badges_unlocked"] = psychometric_result.get("badges_unlocked", [])
    final["hallucination_corrections"] = psychometric_result.get(
        "hallucination_corrections", []
    )
    final["deterministic_baseline"] = psychometric_result.get(
        "deterministic_baseline", {}
    )

    return final


@app.get("/score/{merchant_id}/ml")
def ml_score(merchant_id: str):
    merchant = MERCHANT_MAP.get(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    try:
        return predict(merchant)
    except Exception as e:
        return {
            "repayment_risk": "unknown",
            "confidence": 0,
            "anomaly_flag": False,
            "probabilities": {},
            "error": str(e),
        }


@app.get("/graph/stats")
def graph_stats():
    return {
        "nodes": GRAPH.number_of_nodes(),
        "edges": GRAPH.number_of_edges(),
        "density": round(nx.density(GRAPH), 4),
        "avg_clustering": round(nx.average_clustering(GRAPH.to_undirected()), 4),
    }


@app.get("/graph/neighbors/{merchant_id}")
def get_graph_neighbors(merchant_id: str):
    if merchant_id not in GRAPH:
        raise HTTPException(status_code=404, detail="Merchant not in graph")
    vouchers = list(GRAPH.predecessors(merchant_id))
    vouched_for = list(GRAPH.successors(merchant_id))
    return {
        "merchant_id": merchant_id,
        "vouched_by": [
            {"id": v, "name": MERCHANT_MAP.get(v, {}).get("name", v)} for v in vouchers
        ],
        "vouches_for": [
            {"id": v, "name": MERCHANT_MAP.get(v, {}).get("name", v)}
            for v in vouched_for
        ],
    }


@app.post("/ml-score")
def ml_score_merchant(merchant: dict):
    result = predict(merchant)
    return result


@app.get("/ml-score/{merchant_id}")
def ml_score_by_id(merchant_id: str):
    from engines.inference import predict

    merchant = MERCHANT_MAP.get(merchant_id)
    if not merchant:
        raise HTTPException(404, "Merchant not found")
    return predict(merchant)
