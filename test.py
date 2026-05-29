"""
TrustBridge — Training Script
Run after generate_merchants.py produces large_merchants.json

Steps:
  1. Load + flatten JSON → feature matrix
  2. Anomaly detection (IsolationForest) — unsupervised
  3. Risk classification (XGBoost) — supervised on generated labels
  4. Evaluation + feature importance
  5. Save model

Install once:
  pip install xgboost scikit-learn pandas matplotlib
"""

import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix, ConfusionMatrixDisplay
)
from xgboost import XGBClassifier
import pickle, os

# ─────────────────────────────────────────
# 1. LOAD + FLATTEN
# ─────────────────────────────────────────

def load_and_flatten(path="large_merchants.json"):
    with open(path, encoding="utf-8") as f:
        records = json.load(f)

    rows = []
    for m in records:
        L1 = m["layer_1_social_graph"]
        L2 = m["layer_2_psychometric"]
        L3 = m["layer_3_behavioral"]
        sc = m["trust_score"]
        meta = m["business_metadata"]

        row = {
            # --- identifiers (dropped before training)
            "merchant_id": m["merchant_id"],
            "segment":     meta["segment"],

            # --- Layer 1 features
            "pagerank":           L1["pagerank_score"],
            "vouches_given":      L1["vouch_metrics"]["vouches_given"],
            "vouches_received":   L1["vouch_metrics"]["vouches_received"],
            "vouch_edge_weight":  L1["vouch_metrics"]["vouch_edge_weight"],
            "new_vouches_30d":    L1["vouch_metrics"]["new_vouches_last_30_days"],
            "loyalty_score":      L1["network_relationships"]["calculated_customer_loyalty_score"],
            "repeat_customers":   L1["network_relationships"]["repeat_customers_count"],
            "unique_customers":   L1["network_relationships"]["total_unique_customers_30d"],
            "fraud_penalty":      L1["fraud_ring_risk"]["fraud_penalty_multiplier"],
            "is_fraudster":       int(L1["fraud_ring_risk"]["is_fraud_ring_participant"]),
            "thin_file_collusion":int(L1["fraud_ring_risk"]["thin_file_collusion"]),

            # --- Layer 2 features
            "avg_response_time":  L2["telemetry"]["avg_response_time_seconds"],
            "session_drift":      L2["telemetry"]["multi_session_score_drift_2w"],
            "consistency_failed": int(L2["telemetry"]["consistency_trap_failed"]),
            "loss_aversion":      L2["llm_adjusted_scores"]["loss_aversion_asymmetry"],
            "in_group_trust":     L2["llm_adjusted_scores"]["in_group_trust_radius"],
            "time_discounting":   L2["llm_adjusted_scores"]["time_discounting"],
            "locus_of_control":   L2["llm_adjusted_scores"]["locus_of_control"],

            # --- Layer 3 features
            "regime":             L3["current_regime"],
            "seasonal_business":  int(L3["seasonal_business_flag"]),
            "avg_coverage_ratio": sum(L3["financial_telemetry_3mo"]["coverage_ratio"]) / 3,
            "avg_net_flow":       sum(L3["financial_telemetry_3mo"]["net_cash_flow_npr"]) / 3,
            "consecutive_neg_months": L3["financial_telemetry_3mo"]["consecutive_negative_months"],
            "nea_streak":         L3["proxy_features"]["nea_bill_consecutive_on_time_months"],
            "water_streak":       L3["proxy_features"]["water_bill_consecutive_on_time_months"],
            "topup_regularity":   L3["proxy_features"]["airtime_topup_regularity_index"],
            "payment_variance":   L3["proxy_features"]["days_to_payment_variance"],
            "cross_utility_stress": int(L3["proxy_features"]["cross_utility_correlation_stress"]),

            # --- Meta
            "months_active":      meta["months_active"],
            "data_maturity":      meta["data_maturity_discount_applied"],
            "household_correlated": int(m["household_correlation"]["correlated_risk_flag"]),

            # --- Score (for reference only, not a training feature)
            "trust_score":        sc["final_trust_score"],
            "confidence":         sc["confidence_multiplier"],

            # --- Ground truth label
            "repayment_risk":     sc["ml_label"]["repayment_risk"],  # low/medium/high
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Encode categoricals
    df["segment_enc"] = LabelEncoder().fit_transform(df["segment"])
    df["regime_enc"]  = LabelEncoder().fit_transform(df["regime"])

    print(f"Loaded {len(df)} records")
    print(df["repayment_risk"].value_counts().to_string())
    return df


# ─────────────────────────────────────────
# 2. FEATURE MATRIX
# ─────────────────────────────────────────

FEATURE_COLS = [
    "pagerank", "vouches_given", "vouches_received", "vouch_edge_weight",
    "new_vouches_30d", "loyalty_score", "repeat_customers", "unique_customers",
    "fraud_penalty", "is_fraudster", "thin_file_collusion",
    "avg_response_time", "session_drift", "consistency_failed",
    "loss_aversion", "in_group_trust", "time_discounting", "locus_of_control",
    "avg_coverage_ratio", "avg_net_flow", "consecutive_neg_months",
    "nea_streak", "water_streak", "topup_regularity", "payment_variance",
    "cross_utility_stress", "months_active", "data_maturity",
    "household_correlated", "segment_enc", "regime_enc",
]


# ─────────────────────────────────────────
# 3. ANOMALY DETECTION (unsupervised)
# ─────────────────────────────────────────

def run_anomaly_detection(df):
    X = df[FEATURE_COLS].values
    iso = IsolationForest(
        n_estimators=200,
        contamination=0.05,   # expect ~5% outliers
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X)
    df = df.copy()
    df["anomaly_score"]    = iso.decision_function(X)   # higher = more normal
    df["is_anomaly"]       = (iso.predict(X) == -1).astype(int)

    n_anomalies = df["is_anomaly"].sum()
    fraud_caught = df[df["is_anomaly"] == 1]["is_fraudster"].mean()
    print(f"\n[Anomaly detection]")
    print(f"  Flagged {n_anomalies} anomalies ({n_anomalies/len(df)*100:.1f}%)")
    print(f"  Of anomalies, {fraud_caught*100:.1f}% are actual fraudsters")
    return df, iso


# ─────────────────────────────────────────
# 4. SUPERVISED RISK CLASSIFICATION
# ─────────────────────────────────────────

def run_risk_classifier(df):
    feature_cols = FEATURE_COLS + ["anomaly_score"]

    X = df[feature_cols].values
    le = LabelEncoder()
    y  = le.fit_transform(df["repayment_risk"])   # high=0, low=1, medium=2

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    clf = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    y_pred = clf.predict(X_test)

    print(f"\n[Risk classifier — test set]")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Cross-validation
    cv_scores = cross_val_score(clf, X, y, cv=StratifiedKFold(5), scoring="f1_weighted")
    print(f"  5-fold CV weighted F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    return clf, le, feature_cols, X_test, y_test, y_pred


# ─────────────────────────────────────────
# 5. PLOTS
# ─────────────────────────────────────────

def plot_outputs(clf, le, feature_cols, X_test, y_test, y_pred):
    os.makedirs("outputs", exist_ok=True)

    # Confusion matrix
    fig, ax = plt.subplots(figsize=(6, 5))
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(cm, display_labels=le.classes_)
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Confusion matrix — repayment risk")
    plt.tight_layout()
    plt.savefig("outputs/confusion_matrix.png", dpi=150)
    plt.close()
    print("  Saved outputs/confusion_matrix.png")

    # Feature importance (top 15)
    importance = clf.feature_importances_
    indices    = np.argsort(importance)[-15:]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(
        [feature_cols[i] for i in indices],
        importance[indices],
        color="#1D9E75",
    )
    ax.set_xlabel("Importance score")
    ax.set_title("Top 15 features — XGBoost")
    plt.tight_layout()
    plt.savefig("outputs/feature_importance.png", dpi=150)
    plt.close()
    print("  Saved outputs/feature_importance.png")


# ─────────────────────────────────────────
# 6. SAVE MODEL
# ─────────────────────────────────────────

def save_model(iso, clf, le):
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/isolation_forest.pkl", "wb") as f:
        pickle.dump(iso, f)
    with open("outputs/xgb_risk_classifier.pkl", "wb") as f:
        pickle.dump({"model": clf, "label_encoder": le}, f)
    print("\n  Models saved to outputs/")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    df             = load_and_flatten("large_merchants.json")
    df, iso        = run_anomaly_detection(df)
    clf, le, fcols, X_test, y_test, y_pred = run_risk_classifier(df)
    plot_outputs(clf, le, fcols, X_test, y_test, y_pred)
    save_model(iso, clf, le)
    print("\nDone.")