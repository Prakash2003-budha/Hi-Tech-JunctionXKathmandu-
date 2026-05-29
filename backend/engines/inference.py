import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from typing import Optional

# Load once at startup
clf: Optional[XGBClassifier] = None
le: Optional[LabelEncoder] = None
iso: Optional[IsolationForest] = None

try:
    with open("outputs/xgb_risk_classifier.pkl", "rb") as f:
        bundle = pickle.load(f)
        clf = bundle["model"]
        le = bundle["label_encoder"]
    with open("outputs/isolation_forest.pkl", "rb") as f:
        iso = pickle.load(f)
except FileNotFoundError:
    pass

FEATURE_COLS = [
    "pagerank",
    "vouches_given",
    "vouches_received",
    "vouch_edge_weight",
    "new_vouches_30d",
    "loyalty_score",
    "repeat_customers",
    "unique_customers",
    "fraud_penalty",
    "is_fraudster",
    "thin_file_collusion",
    "avg_response_time",
    "session_drift",
    "consistency_failed",
    "loss_aversion",
    "in_group_trust",
    "time_discounting",
    "locus_of_control",
    "avg_coverage_ratio",
    "avg_net_flow",
    "consecutive_neg_months",
    "nea_streak",
    "water_streak",
    "topup_regularity",
    "payment_variance",
    "cross_utility_stress",
    "months_active",
    "data_maturity",
    "household_correlated",
    "segment_enc",
    "regime_enc",
]

SEGMENT_MAP = {"Digital Native": 0, "Cash Dominant": 1, "New Merchant": 2}
REGIME_MAP = {"recovery": 0, "stable": 1, "stressed": 2}


def merchant_to_vector(m: dict) -> np.ndarray:
    """Flatten a merchant JSON into the feature vector the model expects."""
    L1 = m["layer_1_social_graph"]
    L2 = m["layer_2_psychometric"]
    L3 = m["layer_3_behavioral"]
    meta = m["business_metadata"]
    fin = L3["financial_telemetry_3mo"]
    prox = L3["proxy_features"]

    features = {
        "pagerank": L1["pagerank_score"],
        "vouches_given": L1["vouch_metrics"]["vouches_given"],
        "vouches_received": L1["vouch_metrics"]["vouches_received"],
        "vouch_edge_weight": L1["vouch_metrics"]["vouch_edge_weight"],
        "new_vouches_30d": L1["vouch_metrics"]["new_vouches_last_30_days"],
        "loyalty_score": L1["network_relationships"][
            "calculated_customer_loyalty_score"
        ],
        "repeat_customers": L1["network_relationships"]["repeat_customers_count"],
        "unique_customers": L1["network_relationships"]["total_unique_customers_30d"],
        "fraud_penalty": L1["fraud_ring_risk"]["fraud_penalty_multiplier"],
        "is_fraudster": int(L1["fraud_ring_risk"]["is_fraud_ring_participant"]),
        "thin_file_collusion": int(L1["fraud_ring_risk"]["thin_file_collusion"]),
        "avg_response_time": L2["telemetry"]["avg_response_time_seconds"],
        "session_drift": L2["telemetry"]["multi_session_score_drift_2w"],
        "consistency_failed": int(L2["telemetry"]["consistency_trap_failed"]),
        "loss_aversion": L2["llm_adjusted_scores"]["loss_aversion_asymmetry"],
        "in_group_trust": L2["llm_adjusted_scores"]["in_group_trust_radius"],
        "time_discounting": L2["llm_adjusted_scores"]["time_discounting"],
        "locus_of_control": L2["llm_adjusted_scores"]["locus_of_control"],
        "avg_coverage_ratio": sum(fin["coverage_ratio"]) / 3,
        "avg_net_flow": sum(fin["net_cash_flow_npr"]) / 3,
        "consecutive_neg_months": fin["consecutive_negative_months"],
        "nea_streak": prox["nea_bill_consecutive_on_time_months"],
        "water_streak": prox["water_bill_consecutive_on_time_months"],
        "topup_regularity": prox["airtime_topup_regularity_index"],
        "payment_variance": prox["days_to_payment_variance"],
        "cross_utility_stress": int(prox["cross_utility_correlation_stress"]),
        "months_active": meta["months_active"],
        "data_maturity": meta["data_maturity_discount_applied"],
        "household_correlated": 0,  # set externally if known
        "segment_enc": SEGMENT_MAP.get(meta["segment"], 0),
        "regime_enc": REGIME_MAP.get(L3["current_regime"], 1),
    }

    return np.array([features[c] for c in FEATURE_COLS]).reshape(1, -1)


def predict(merchant: dict) -> dict:
    if clf is None:
        return {"error": "ML models not loaded. Place .pkl files in backend/outputs/"}
    vec = merchant_to_vector(merchant)

    # Anomaly score
    anomaly_score = float(iso.decision_function(vec)[0])
    is_anomaly = bool(iso.predict(vec)[0] == -1)

    # Add anomaly score as extra feature (matches training)
    vec_with_anomaly = np.append(vec, anomaly_score).reshape(1, -1)

    # Risk prediction
    pred_encoded = clf.predict(vec_with_anomaly)[0]
    probabilities = clf.predict_proba(vec_with_anomaly)[0]
    risk_label = le.inverse_transform([pred_encoded])[0]

    return {
        "repayment_risk": risk_label,
        "confidence": round(float(probabilities.max()), 3),
        "probabilities": {
            label: round(float(prob), 3)
            for label, prob in zip(le.classes_, probabilities)
        },
        "anomaly_flag": is_anomaly,
        "anomaly_score": round(anomaly_score, 4),
    }
