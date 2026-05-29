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
