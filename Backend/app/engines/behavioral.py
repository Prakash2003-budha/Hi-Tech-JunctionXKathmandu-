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
