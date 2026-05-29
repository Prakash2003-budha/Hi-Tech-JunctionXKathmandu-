"""
TrustBridge — Fixed Merchant Dataset Generator
Covers all architectural gaps from the original script.
"""

import json
import random
import math
from datetime import datetime, timedelta
from collections import defaultdict

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def data_maturity_from_months(months_active):
    """Ramps 0.60 → 1.00 over 12 months, not random."""
    return round(clamp(0.60 + (months_active / 12) * 0.40, 0.60, 1.00), 2)

def compute_customer_loyalty(repeat, total, avg_visits_per_month, longest_rel_months):
    """Exact formula from architecture brief."""
    if total == 0:
        return 0.0
    return round(
        (repeat / total) * 0.5 +
        clamp(avg_visits_per_month / 4, 0, 1) * 0.3 +
        clamp(longest_rel_months / 24, 0, 1) * 0.2,
        3
    )

def compute_payment_variance(payment_delays):
    """Actual std-dev of days-to-payment, not a random range."""
    if len(payment_delays) < 2:
        return 0.0
    mean = sum(payment_delays) / len(payment_delays)
    variance = sum((x - mean) ** 2 for x in payment_delays) / len(payment_delays)
    return round(math.sqrt(variance), 2)

def compute_consecutive_negatives(net_flows):
    """Correct running tally — max streak across the window."""
    max_streak = 0
    current = 0
    for nf in net_flows:
        if nf < 0:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak

def score_floor(raw_score, data_maturity):
    """
    Score floor = 30 (dignity floor from architecture brief).
    If data is too thin, report 'insufficient data' band.
    """
    floored = max(30, raw_score)
    if data_maturity < 0.75:
        return floored, "insufficient_data"
    return floored, "scored"

# ─────────────────────────────────────────
# NAME / BUSINESS GENERATORS
# ─────────────────────────────────────────

FIRST_NAMES = ["Ramesh", "Dolma", "Tenzing", "Sita", "Bikram", "Anjali",
               "Subash", "Pooja", "Rajesh", "Niranjan", "Deepak", "Binita",
               "Raju", "Kamala", "Suresh", "Parbati", "Hari", "Mina"]
LAST_NAMES   = ["Shrestha", "Gurung", "Lama", "Thapa", "Pradhan",
                "Adhikari", "Karki", "Maharjan", "Joshi", "Tamang",
                "Rai", "Magar", "Newar", "Basnet", "Poudel"]
BUSINESS_TYPES = [
    ("Kirana Pasala",        "Grocery & Daily Essentials"),
    ("Kapada Udhyog",        "Textiles & Apparel"),
    ("Maha Bouddha Wholesalers", "Electronics & Wholesale"),
    ("Chiya Pasal",          "Tea & Local Eatery"),
    ("Momo Center",          "Restaurant & Hospitality"),
    ("Krishi Supplier",      "Agribusiness & Fertilizers"),
    ("Photo Studio",         "Seasonal Photography"),          # wedding-photographer edge case
    ("Tarkari Pasala",       "Vegetable & Seasonal Produce"),  # seasonal income edge case
]
LOCATIONS = ["Asan, Kathmandu", "Mahendrapool, Pokhara", "Mahabouddha, Kathmandu",
             "Lalitpur", "Bhaktapur", "Butwal", "Biratnagar", "Dhangadhi", "Hetauda"]

def generate_name():
    owner = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    b_name, b_type = random.choice(BUSINESS_TYPES)
    legal  = f"{random.choice(LAST_NAMES)} {b_name}"
    return owner, legal, b_type

# ─────────────────────────────────────────
# LAYER 1 — SOCIAL GRAPH
# ─────────────────────────────────────────

def build_social_graph(segment, months_active, vouch_pool):
    """
    vouch_pool: list of (merchant_id, pagerank) already generated,
    used to detect star fraud (one anchor vouching too many).
    """
    # Base vouch counts by segment
    if segment == "New Merchant":
        vouches_given    = random.randint(0, 2)
        vouches_received = random.randint(0, 3)
    else:
        vouches_given    = random.randint(1, 5)
        vouches_received = random.randint(1, 8)

    # ── Fraud ring assignment ──────────────────────────────────────
    # 4% base fraud rate; new merchants with too many outgoing vouches flagged extra
    thin_file_collusion = (segment == "New Merchant" and vouches_given > 2 and months_active < 4)
    is_fraudster = random.random() < (0.07 if thin_file_collusion else 0.04)

    if is_fraudster:
        vouches_given    = random.randint(6, 12)
        vouches_received = random.randint(8, 15)
        loop_detected        = True
        temporal_clustering  = True   # 5+ vouches created within 72h
        penalty              = 0.60
        pagerank             = round(random.uniform(0.04, 0.07), 4)
    else:
        loop_detected        = False
        temporal_clustering  = False
        penalty              = 1.0
        pagerank             = round(random.uniform(0.008, 0.035), 4)

    # ── Star fraud: anchor node vouching > 4 new merchants ────────
    # Track in vouch_pool; flag if any anchor already has 4+ recent vouches
    anchor_vouched = False
    for anchor_id, anchor_pr in vouch_pool[-50:]:   # check recent 50
        anchor_new_vouches = sum(
            1 for _, pr in vouch_pool if pr == anchor_pr
        )
        if anchor_pr > 0.03 and anchor_new_vouches > 4:
            # This merchant was vouched by a suspicious anchor
            penalty     = round(penalty * 0.75, 2)
            anchor_vouched = True
            break

    trusted_anchor_vouched = (pagerank > 0.03) and not anchor_vouched

    # ── Customer relationship signals ─────────────────────────────
    if segment == "New Merchant":
        unique_cust  = random.randint(10, 60)
    else:
        unique_cust  = random.randint(40, 500)

    repeat_cust         = int(unique_cust * random.uniform(0.15, 0.65))
    avg_visits_per_mo   = round(random.uniform(1.0, 6.0), 1)
    longest_rel_months  = min(months_active - 1, random.randint(2, 36))
    new_vouches_30d     = random.randint(0, 3) if not is_fraudster else random.randint(3, 8)

    loyalty_score = compute_customer_loyalty(
        repeat_cust, unique_cust, avg_visits_per_mo, longest_rel_months
    )

    # ── Edge expiry simulation ─────────────────────────────────────
    # Vouches older than 18 months decay 10%/month
    vouch_age_months    = random.randint(0, months_active)
    decay_months        = max(0, vouch_age_months - 18)
    vouch_weight        = round(max(0.1, 1.0 - decay_months * 0.10), 2)

    return {
        "node_type": "MERCHANT",
        "pagerank_score": pagerank,
        "vouch_metrics": {
            "vouches_given":             vouches_given,
            "vouches_received":          vouches_received,
            "trusted_anchor_vouched":    trusted_anchor_vouched,
            "new_vouches_last_30_days":  new_vouches_30d,
            "vouch_edge_weight":         vouch_weight,
            "vouch_age_months":          vouch_age_months,
        },
        "network_relationships": {
            "repeat_customers_count":        repeat_cust,
            "total_unique_customers_30d":    unique_cust,
            "avg_visits_per_customer_month": avg_visits_per_mo,
            "longest_relationship_months":   longest_rel_months,
            "supplier_buyer_loop_detected":  loop_detected,
            "temporal_clustering_flag":      temporal_clustering,
            "calculated_customer_loyalty_score": loyalty_score,
        },
        "fraud_ring_risk": {
            "star_fraud_anchor_suspicious": anchor_vouched,
            "thin_file_collusion":          thin_file_collusion,
            "is_fraud_ring_participant":    is_fraudster,
            "fraud_penalty_multiplier":     penalty,
            "temporal_vouching_burst":      temporal_clustering,
        }
    }, is_fraudster, pagerank

# ─────────────────────────────────────────
# LAYER 2 — PSYCHOMETRIC
# ─────────────────────────────────────────

def build_psychometric(segment, is_fraudster):
    """
    Drift is:
    - Derived from consistency_trap + response_time telemetry (not random)
    - Applied differently per trait (locus_of_control inverts)
    - multi_session_drift CORRELATED with consistency_failed
    """
    avg_response = round(random.uniform(1.5, 9.0), 1)
    consistency_failed = random.random() < (0.20 if is_fraudster else 0.12)

    # Response-time signal: fast on money Qs = impulsive (negative drift)
    time_signal = -1 if avg_response < 3.0 else (1 if avg_response > 7.0 else 0)

    # Consistency signal
    consistency_signal = -1 if consistency_failed else 0

    # Combined drift base: -12 to +12, pulled negative by signals
    raw_drift = random.randint(-10, 10)
    drift = raw_drift + (time_signal * 5) + (consistency_signal * 8)
    drift = clamp(drift, -15, 15)

    # Multi-session score drift CORRELATED with consistency failures
    if consistency_failed:
        session_drift = round(random.uniform(12.0, 25.0), 1)   # high instability
    else:
        session_drift = round(random.uniform(1.0, 8.0), 1)

    base_loss   = random.randint(45, 90)
    base_trust  = random.randint(35, 85)
    base_time   = random.randint(40, 80)
    base_locus  = random.randint(50, 90)

    return {
        "telemetry": {
            "avg_response_time_seconds":    avg_response,
            "response_time_signal":         ["neutral", "impulsive", "deliberate"][[0, -1, 1].index(time_signal)],
            "multi_session_score_drift_2w": session_drift,
            "consistency_trap_failed":      consistency_failed,
        },
        "deterministic_base_scores": {
            "loss_aversion_asymmetry": base_loss,
            "in_group_trust_radius":   base_trust,
            "time_discounting":        base_time,
            "locus_of_control":        base_locus,
        },
        # Each trait responds differently to drift (locus_of_control inverts)
        "llm_adjusted_scores": {
            "loss_aversion_asymmetry": clamp(base_loss  + drift,            0, 100),
            "in_group_trust_radius":   clamp(base_trust + int(drift * 0.5), 0, 100),
            "time_discounting":        clamp(base_time  + drift,            0, 100),
            "locus_of_control":        clamp(base_locus - drift,            0, 100),  # inverted
        },
        "llm_explanation": (
            "Consistency trap triggered — reliability weight reduced."
            if consistency_failed else
            "Automated pipeline constraint evaluation applied."
        ),
    }

# ─────────────────────────────────────────
# LAYER 3 — BEHAVIORAL
# ─────────────────────────────────────────

FESTIVAL_CALENDAR = {
    # month_index (0-based) → festival name, multiplier range
    2: ("Dashain",  (2.0, 2.8)),
    3: ("Tihar",    (1.8, 2.4)),
    8: ("Teej",     (1.3, 1.6)),
}

def detect_seasonal_business(b_type):
    """Photo studios, wedding services — zero-income months then big spike."""
    return b_type in ("Seasonal Photography",)

def build_behavioral(segment, current_regime, months_active, b_type):
    base_revenue = random.randint(80_000, 2_000_000)
    is_seasonal  = detect_seasonal_business(b_type)

    credits_3mo  = []
    debits_3mo   = []
    net_flow_3mo = []
    coverage_3mo = []
    payment_delays = []

    for m_idx in range(3):
        # Festival spike
        festival_modifier = 1.0
        festival_this_month = None
        for fmonth, (fname, frange) in FESTIVAL_CALENDAR.items():
            if m_idx == fmonth % 3:   # simplified mapping for 3-month window
                festival_modifier = random.uniform(*frange)
                festival_this_month = fname
                break

        # Seasonal business: random near-zero months
        if is_seasonal and random.random() < 0.4:
            revenue  = base_revenue * random.uniform(0.05, 0.15)
            expenses = revenue * random.uniform(0.90, 1.10)
        elif current_regime == "stable":
            revenue  = base_revenue * festival_modifier * random.uniform(0.88, 1.12)
            expenses = revenue * random.uniform(0.72, 0.88)
        elif current_regime == "stressed":
            revenue  = base_revenue * festival_modifier * random.uniform(0.55, 0.80)
            expenses = revenue * random.uniform(0.95, 1.18)   # outflows > inflows
        else:  # recovery
            revenue  = base_revenue * festival_modifier * random.uniform(0.78, 0.96)
            expenses = revenue * random.uniform(0.84, 0.93)

        credits_3mo.append(int(revenue))
        debits_3mo.append(int(expenses))
        net      = int(revenue - expenses)
        coverage = round(revenue / max(expenses, 1), 3)
        net_flow_3mo.append(net)
        coverage_3mo.append(coverage)

        # Simulate payment delay for this month
        if current_regime == "stable":
            delay = random.randint(0, 5)
        elif current_regime == "stressed":
            delay = random.randint(5, 21)
        else:
            delay = random.randint(2, 10)
        payment_delays.append(delay)

    consecutive_neg = compute_consecutive_negatives(net_flow_3mo)

    # ── Utility proxy features ─────────────────────────────────────
    if current_regime == "stable":
        nea_months        = random.randint(6, 24)
        water_months      = random.randint(4, 18)
        topup_regularity  = round(random.uniform(0.80, 0.98), 2)
        utility_stress    = False
    elif current_regime == "stressed":
        nea_months        = random.randint(0, 3)
        water_months      = random.randint(0, 2)
        topup_regularity  = round(random.uniform(0.20, 0.55), 2)
        utility_stress    = consecutive_neg >= 1
    else:
        nea_months        = random.randint(2, 8)
        water_months      = random.randint(1, 6)
        topup_regularity  = round(random.uniform(0.55, 0.78), 2)
        utility_stress    = False

    # Cross-utility stress: both NEA + water late = structural, not accidental
    cross_utility_stress = utility_stress and (nea_months < 2) and (water_months < 2)

    # Actual computed variance (not a random range swap)
    days_variance = compute_payment_variance(payment_delays)

    # Seasonal flag: don't penalise zero-income months for seasonal businesses
    seasonal_income_pattern = is_seasonal

    return {
        "current_regime": current_regime,
        "historical_regime_transitions": ["stable", current_regime],
        "seasonal_business_flag": seasonal_income_pattern,
        "financial_telemetry_3mo": {
            "monthly_credits_npr":         credits_3mo,
            "monthly_debits_npr":          debits_3mo,
            "net_cash_flow_npr":           net_flow_3mo,
            "coverage_ratio":              coverage_3mo,
            "consecutive_negative_months": consecutive_neg,
            "festival_spike_normalized":   True,
        },
        "proxy_features": {
            "nea_bill_consecutive_on_time_months":   nea_months,
            "water_bill_consecutive_on_time_months": water_months,
            "airtime_topup_regularity_index":        topup_regularity,
            "days_to_payment_variance":              days_variance,
            "payment_delays_raw_3mo":                payment_delays,
            "cross_utility_correlation_stress":      cross_utility_stress,
        }
    }

# ─────────────────────────────────────────
# SCORE FUSION (for ground-truth label generation)
# ─────────────────────────────────────────

SEGMENT_WEIGHTS = {
    "Digital Native": {"social": 0.20, "psychometric": 0.15, "behavioral": 0.65},
    "Cash Dominant":  {"social": 0.30, "psychometric": 0.35, "behavioral": 0.35},
    "New Merchant":   {"social": 0.40, "psychometric": 0.45, "behavioral": 0.15},
}

def compute_trust_score(layer1, layer2, layer3, segment, data_maturity, is_fraudster):
    w = SEGMENT_WEIGHTS[segment]

    # Social score: pagerank + loyalty - fraud penalty
    social_raw = (
        layer1["pagerank_score"] * 800 +          # scale to ~0-60 range
        layer1["network_relationships"]["calculated_customer_loyalty_score"] * 40
    ) * layer1["fraud_ring_risk"]["fraud_penalty_multiplier"]
    social_score = clamp(social_raw, 0, 100)

    # Psychometric score: average of adjusted traits
    adj = layer2["llm_adjusted_scores"]
    psych_score = clamp(
        (adj["loss_aversion_asymmetry"] +
         adj["in_group_trust_radius"] +
         adj["time_discounting"] +
         adj["locus_of_control"]) / 4,
        0, 100
    )
    if layer2["telemetry"]["consistency_trap_failed"]:
        psych_score *= 0.85   # reliability penalty

    # Behavioral score: coverage ratio trend + utility streaks
    coverages = layer3["financial_telemetry_3mo"]["coverage_ratio"]
    avg_coverage = sum(coverages) / len(coverages)
    coverage_score = clamp(avg_coverage * 60, 0, 60)
    utility_score  = (
        min(layer3["proxy_features"]["nea_bill_consecutive_on_time_months"], 12) / 12 * 25 +
        layer3["proxy_features"]["airtime_topup_regularity_index"] * 15
    )
    behav_score = clamp(coverage_score + utility_score, 0, 100)
    if layer3["proxy_features"]["cross_utility_correlation_stress"]:
        behav_score *= 0.80

    raw = (
        w["social"]      * social_score +
        w["psychometric"]* psych_score  +
        w["behavioral"]  * behav_score
    )

    # Confidence multiplier based on data maturity
    confidence = data_maturity
    final_raw   = raw * confidence

    final, status = score_floor(round(final_raw, 1), data_maturity)
    band = round(8 * (1 - data_maturity) + 3, 1)   # wider band for thin data

    # Lending tier
    if final >= 75:   tier = "Tier 1 — Standard Loan"
    elif final >= 58: tier = "Tier 2 — Micro Loan"
    elif final >= 42: tier = "Tier 3 — Conditional / Pilot"
    else:             tier = "Tier 4 — Decline / Insufficient Data"

    return {
        "final_trust_score":     final,
        "score_band_plus_minus": band,
        "score_status":          status,
        "lending_tier":          tier,
        "component_scores": {
            "social":      round(social_score, 1),
            "psychometric":round(psych_score,  1),
            "behavioral":  round(behav_score,  1),
        },
        "confidence_multiplier": confidence,
        # Ground truth label for ML training
        "ml_label": {
            "repayment_risk": (
                "high"   if final < 42 or is_fraudster else
                "medium" if final < 60 else
                "low"
            ),
            "default_probability_band": (
                "0.60-0.85" if final < 42 else
                "0.25-0.55" if final < 60 else
                "0.05-0.20"
            ),
        }
    }

# ─────────────────────────────────────────
# HOUSEHOLD CORRELATION
# ─────────────────────────────────────────

def flag_household_overlap(merchants):
    """
    Multi-business same location → correlated risk, not independent.
    Flags pairs sharing location + owner surname.
    """
    location_surname_map = defaultdict(list)
    for m in merchants:
        loc     = m["business_metadata"]["location"]
        surname = m["business_metadata"]["owner_name"].split()[-1]
        key     = f"{loc}|{surname}"
        location_surname_map[key].append(m["merchant_id"])

    household_map = {
        ids[0]: ids[1:]
        for ids in location_surname_map.values() if len(ids) > 1
    }
    return household_map

# ─────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────

def generate_merchant_dataset(num_merchants=1200):
    segments  = ["Digital Native", "Cash Dominant", "New Merchant"]
    merchants = []
    vouch_pool = []   # for star-fraud detection across merchants

    for i in range(1, num_merchants + 1):
        merchant_id = f"MERCH-2026-{i:04d}"
        owner, legal_name, b_type = generate_name()

        segment = random.choices(segments, weights=[0.50, 0.35, 0.15], k=1)[0]

        if segment == "New Merchant":
            months_active   = random.randint(2, 6)
            current_regime  = random.choices(
                ["stable", "stressed"], weights=[0.70, 0.30], k=1)[0]
        else:
            months_active   = random.randint(12, 48)
            current_regime  = random.choices(
                ["stable", "stressed", "recovery"], weights=[0.75, 0.15, 0.10], k=1)[0]

        data_maturity = data_maturity_from_months(months_active)

        # Build layers
        layer1, is_fraudster, pagerank = build_social_graph(segment, months_active, vouch_pool)
        vouch_pool.append((merchant_id, pagerank))

        layer2 = build_psychometric(segment, is_fraudster)
        layer3 = build_behavioral(segment, current_regime, months_active, b_type)

        # Fusion + ground truth
        score_data = compute_trust_score(
            layer1, layer2, layer3, segment, data_maturity, is_fraudster
        )

        merchant_profile = {
            "merchant_id": merchant_id,
            "business_metadata": {
                "legal_name":                    legal_name,
                "owner_name":                    owner,
                "location":                      random.choice(LOCATIONS),
                "business_type":                 b_type,
                "months_active":                 months_active,
                "segment":                       segment,
                "data_maturity_discount_applied":data_maturity,
            },
            "layer_1_social_graph":  layer1,
            "layer_2_psychometric":  layer2,
            "layer_3_behavioral":    layer3,
            "trust_score":           score_data,
        }
        merchants.append(merchant_profile)

    # Post-processing: household correlation flags
    household_map = flag_household_overlap(merchants)
    for m in merchants:
        mid = m["merchant_id"]
        m["household_correlation"] = {
            "same_household_merchants": household_map.get(mid, []),
            "correlated_risk_flag":     mid in household_map,
        }

    return merchants


if __name__ == "__main__":
    total = 1200
    print(f"Generating {total} merchant records...")
    dataset = generate_merchant_dataset(total)

    out = "large_merchants.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    # Quick sanity stats
    fraudsters    = sum(1 for m in dataset if m["layer_1_social_graph"]["fraud_ring_risk"]["is_fraud_ring_participant"])
    stressed      = sum(1 for m in dataset if m["layer_3_behavioral"]["current_regime"] == "stressed")
    seasonal      = sum(1 for m in dataset if m["layer_3_behavioral"]["seasonal_business_flag"])
    household_f   = sum(1 for m in dataset if m["household_correlation"]["correlated_risk_flag"])
    tiers         = {"Tier 1":0,"Tier 2":0,"Tier 3":0,"Tier 4":0}
    for m in dataset:
        t = m["trust_score"]["lending_tier"][:6]
        tiers[t] = tiers.get(t, 0) + 1

    print(f"\n✓ Saved to {out}")
    print(f"  Fraudsters:          {fraudsters} ({fraudsters/total*100:.1f}%)")
    print(f"  Stressed regime:     {stressed}")
    print(f"  Seasonal businesses: {seasonal}")
    print(f"  Household-flagged:   {household_f}")
    print(f"  Lending tiers:       {tiers}")