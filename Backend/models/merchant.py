from pydantic import BaseModel
from typing import Optional, Dict, List


class MerchantBase(BaseModel):
    merchant_id: str
    name: str
    district: str
    business_type: str
    phone: str
    digital_footprint: bool = False
    esewa_registered: bool = False
    khalti_registered: bool = False


class MerchantCreate(MerchantBase):
    pass


class Merchant(MerchantBase):
    id: int

    class Config:
        from_attributes = True


class ScoreSubScores(BaseModel):
    social: int
    psychometric: int
    behavioral: int


class LendingTier(BaseModel):
    tier: str
    label: str
    max_loan_npr: int
    interest_rate: str
    color: str


class TrustScore(BaseModel):
    merchant_id: str
    merchant_name: str
    final_score: int
    confidence: float
    confidence_pct: int
    segment: str
    sub_scores: ScoreSubScores
    lending_tier: LendingTier
    fraud_flag: bool
    credit_personality: str
    psychometric_insight: str
    improvement_pathway: List[str]
    data_sources_used: int
