"""TrustBridge FastAPI application factory."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional

from .config import get_settings
from .dependencies import get_app_state, AppStateDep, SettingsDep
from .engines.social_graph import score_merchant_social
from .engines.psychometric import run_psychometric_assessment, get_questions
from .engines.behavioral import compute_behavioral_score
from .engines.fusion import fuse_scores


class PsychometricRequest(BaseModel):
    merchant_id: str
    responses: Dict[str, str]  # {"q1": "A", "q2": "D", ...}


class ScoreRequest(BaseModel):
    merchant_id: str
    psychometric_responses: Optional[Dict[str, str]] = None


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        debug=settings.DEBUG
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Load merchants at startup
    @app.on_event("startup")
    def load_data():
        """Load mock data at startup."""
        state = get_app_state()
        if not state.merchants:
            state.load_merchants()

    # ---- Routes ----

    @app.get("/")
    def root():
        """Root endpoint."""
        state = get_app_state()
        return {
            "name": "TrustBridge",
            "version": settings.API_VERSION,
            "status": "running",
            "merchants_loaded": len(state.merchants)
        }

    @app.get("/merchants")
    def list_merchants(state: AppStateDep):
        """List all merchants."""
        if not state.merchants:
            raise HTTPException(
                status_code=503,
                detail="Mock data not loaded. Please run generate_mock.py"
            )

        return [
            {
                "merchant_id": m["merchant_id"],
                "name": m["name"],
                "district": m["district"],
                "business_type": m["business_type"],
                "digital_footprint": m["digital_footprint"]
            }
            for m in state.merchants
        ]

    @app.get("/merchants/{merchant_id}")
    def get_merchant(merchant_id: str, state: AppStateDep):
        """Get merchant details."""
        m = state.merchant_map.get(merchant_id)
        if not m:
            raise HTTPException(status_code=404, detail="Merchant not found")
        return m

    @app.get("/psychometric/questions")
    def psychometric_questions():
        """Get psychometric assessment questions."""
        return get_questions()

    @app.post("/score/{merchant_id}")
    def compute_full_score(
        merchant_id: str,
        body: Optional[ScoreRequest] = None,
        state: AppStateDep = None
    ):
        """Compute full trust score for a merchant."""
        if not state.merchant_map:
            raise HTTPException(
                status_code=503,
                detail="Backend not ready. Please run generate_mock.py"
            )

        merchant = state.merchant_map.get(merchant_id)
        if not merchant:
            raise HTTPException(status_code=404, detail="Merchant not found")

        # Layer 1: Social graph
        social_result = score_merchant_social(merchant_id, state.graph)

        # Layer 2: Psychometric
        responses = body.psychometric_responses if body else None
        if responses:
            psychometric_result = run_psychometric_assessment(
                merchant_id, merchant["name"], responses
            )
        else:
            psychometric_result = {
                "psychometric_score": 0,
                "credit_personality": "Not assessed",
                "insight": "Please complete psychometric assessment",
                "red_flags": "none",
                "strengths": ""
            }

        # Layer 3: Behavioral
        behavioral_result = compute_behavioral_score(merchant)

        # Fusion
        final = fuse_scores(merchant, social_result, psychometric_result, behavioral_result)

        return final

    @app.get("/graph/stats")
    def graph_stats(state: AppStateDep):
        """Get graph statistics."""
        if not state.graph:
            raise HTTPException(status_code=503, detail="Backend not ready")

        import networkx as nx
        return {
            "nodes": state.graph.number_of_nodes(),
            "edges": state.graph.number_of_edges(),
            "density": round(nx.density(state.graph), 4),
            "avg_clustering": round(nx.average_clustering(state.graph.to_undirected()), 4)
        }

    @app.get("/health")
    def health(state: AppStateDep):
        """Health check endpoint."""
        return {"status": "ok", "merchants_loaded": len(state.merchants)}

    return app
