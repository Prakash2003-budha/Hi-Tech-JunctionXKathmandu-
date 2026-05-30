import math
from typing import Dict, List
from datetime import datetime

HARVEST_CALENDAR = {
    "vegetables": [1, 2, 3, 9, 10, 11],
    "dairy":      [4, 5, 6, 10, 11, 12],
    "tea_shop":   list(range(1, 13)),
    "clothing":   [10, 11, 12, 1, 2],
    "hardware":   [3, 4, 5, 9, 10],
    "pharmacy":   list(range(1, 13)),
}


def score_transactional_consistency(revenue_history: List[Dict]) -> int:
    if not revenue_history:
        return 0
    amounts = [r["amount"] for r in revenue_history]
    mean = sum(amounts) / len(amounts)
    if mean == 0:
        return 0
    variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean
    return round(min(100 * math.exp(-cv), 100))


def score_obligation_fulfillment(utility_payments: List[Dict]) -> int:
    if not utility_payments:
        return 0
    total = len(utility_payments)
    on_time_count = sum(1 for p in utility_payments if p.get("paid_on_time"))
    partial_count = sum(1 for p in utility_payments if p.get("partial_payment"))
    base_rate = on_time_count / total
    partial_penalty = (partial_count / total) * 0.3
    return round(max((base_rate - partial_penalty) * 100, 0))


def score_airtime_consistency(airtime_topups: List[Dict]) -> int:
    if not airtime_topups:
        return 30
    monthly_amounts = [t["total_amount"] for t in airtime_topups]
    mean = sum(monthly_amounts) / len(monthly_amounts)
    if mean == 0:
        return 0
    variance = sum((x - mean) ** 2 for x in monthly_amounts) / len(monthly_amounts)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean
    return round(min(100 * math.exp(-cv * 0.8), 100))


def score_cash_flow_seasonality(revenue_history: List[Dict], business_type: str) -> int:
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
        expected_high.append(1 if month_num in harvest_months else 0)
        actual_amounts.append(entry["amount"])

    if not actual_amounts:
        return 50

    mean_amount = sum(actual_amounts) / len(actual_amounts)
    correct_peaks = sum(
        1 for i, amount in enumerate(actual_amounts)
        if (amount > mean_amount) == (expected_high[i] == 1)
    )
    return round((correct_peaks / len(actual_amounts)) * 100)


def score_khata_repayment(khata_entries: List[Dict]) -> int:
    if not khata_entries:
        return 0
    debt_taken = [e for e in khata_entries if e.get("type") == "debt_taken"]
    if not debt_taken:
        return 50
    repaid = [e for e in debt_taken if e.get("repaid")]
    repayment_rate = len(repaid) / len(debt_taken)
    repay_days = [e["days_to_repay"] for e in repaid if e.get("days_to_repay")]
    speed_factor = math.exp(-0.1 * (sum(repay_days) / len(repay_days)) / 30) if repay_days else 0.5
    return round(min(repayment_rate * 100 * (0.7 + 0.3 * speed_factor), 100))


def compute_behavioral_score(merchant: Dict) -> Dict:
    # New schema path
    if "layer_3_behavioral" in merchant:
        L3   = merchant["layer_3_behavioral"]
        fin  = L3["financial_telemetry_3mo"]
        prox = L3["proxy_features"]

        avg_coverage  = sum(fin["coverage_ratio"]) / 3
        tc  = round(min(avg_coverage * 80, 100))

        nea    = prox["nea_bill_consecutive_on_time_months"]
        water  = prox["water_bill_consecutive_on_time_months"]
        ofs = round(min((nea + water) / 24 * 100, 100))

        ats = round(prox["airtime_topup_regularity_index"] * 100)

        neg = fin["consecutive_negative_months"]
        css = round(max(100 - neg * 30, 0))

        # Phase 4 fix: derive khata proxy from payment delay variance
        delay_variance = prox.get("days_to_payment_variance", 5.0)
        raw_delays = prox.get("payment_delays_raw_3mo", [])
        if raw_delays:
            avg_delay = sum(raw_delays) / len(raw_delays)
            krs = round(max(100 - avg_delay * 8 - delay_variance * 3, 0))
        else:
            krs = round(max(100 - delay_variance * 5, 0))

        behavioral_score = round(
            tc  * 0.30 +
            ofs * 0.28 +
            ats * 0.18 +
            css * 0.12 +
            krs * 0.12
        )

        return {
            "behavioral_score": behavioral_score,
            "sub_scores": {
                "transactional_consistency": tc,
                "obligation_fulfillment":    ofs,
                "airtime_consistency":       ats,
                "cash_flow_seasonality":     css,
                "khata_repayment":           krs,
            },
            "has_khata_data": False
        }

    # Old schema fallback
    tc  = score_transactional_consistency(merchant.get("revenue_history", []))
    ofs = score_obligation_fulfillment(merchant.get("utility_payments", []))
    ats = score_airtime_consistency(merchant.get("airtime_topups", []))
    css = score_cash_flow_seasonality(merchant.get("revenue_history", []), merchant.get("business_type", "tea_shop"))
    krs = score_khata_repayment(merchant.get("khata_entries", []))
    has_khata = len(merchant.get("khata_entries", [])) > 0

    if has_khata:
        weights = {"tc": 0.25, "ofs": 0.25, "ats": 0.15, "css": 0.15, "krs": 0.20}
    else:
        weights = {"tc": 0.35, "ofs": 0.30, "ats": 0.20, "css": 0.15, "krs": 0.00}

    behavioral_score = round(
        tc * weights["tc"] + ofs * weights["ofs"] +
        ats * weights["ats"] + css * weights["css"] + krs * weights["krs"]
    )

    return {
        "behavioral_score": behavioral_score,
        "sub_scores": {
            "transactional_consistency": tc,
            "obligation_fulfillment":    ofs,
            "airtime_consistency":       ats,
            "cash_flow_seasonality":     css,
            "khata_repayment":           krs,
        },
        "has_khata_data": has_khata
    }