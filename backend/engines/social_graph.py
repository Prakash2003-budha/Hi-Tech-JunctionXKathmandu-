import networkx as nx
from typing import Dict, List


def build_graph(merchants: List[Dict]) -> nx.DiGraph:
    G = nx.DiGraph()
    for m in merchants:
        meta = m.get("business_metadata", {})
        G.add_node(
            m["merchant_id"],
            name=meta.get("owner_name", m["merchant_id"]),
            business_type=meta.get("business_type", ""),
            district=meta.get("location", "")
        )

    for m in merchants:
        L1 = m.get("layer_1_social_graph", {})
        vouch_metrics = L1.get("vouch_metrics", {})
        vouches_given = vouch_metrics.get("vouches_given", 0)
        vouch_weight  = vouch_metrics.get("vouch_edge_weight", 1.0)
        fraud_penalty = L1.get("fraud_ring_risk", {}).get("fraud_penalty_multiplier", 1.0)

        # Simulate edges: this merchant vouches for `vouches_given` others
        # In real data these would be explicit edge records
        # For now we use the pre-computed pagerank and fraud flags from the data
        if vouches_given > 0 and fraud_penalty < 1.0:
            # Fraudster — add self-loop style signal
            G.add_edge(
                m["merchant_id"],
                m["merchant_id"],
                weight=vouch_weight * 0.1,
                relationship="self"
            )

    return G


def detect_fraud_rings(G: nx.DiGraph) -> List[List[str]]:
    undirected = G.to_undirected()
    cliques = list(nx.find_cliques(undirected))
    suspicious = []
    for clique in cliques:
        if len(clique) >= 3:
            clique_set = set(clique)
            external_edges = sum(
                1 for n in clique
                for neighbor in G.neighbors(n)
                if neighbor not in clique_set
            )
            if external_edges == 0:
                suspicious.append(clique)
    return suspicious


def compute_pagerank_scores(G: nx.DiGraph) -> Dict[str, float]:
    if len(G.nodes) == 0:
        return {}
    try:
        scores = nx.pagerank(G, weight="weight", alpha=0.85, max_iter=200)
    except nx.PowerIterationFailedConvergence:
        scores = {n: 1 / len(G.nodes) for n in G.nodes}
    return scores


def score_merchant_social(merchant_id: str, G: nx.DiGraph, merchant_data: Dict = None) -> Dict:
    # Use pre-computed values from the new schema if available
    if merchant_data:
        L1 = merchant_data.get("layer_1_social_graph", {})
        fraud_flag    = L1.get("fraud_ring_risk", {}).get("is_fraud_ring_participant", False)
        fraud_penalty = L1.get("fraud_ring_risk", {}).get("fraud_penalty_multiplier", 1.0)
        pagerank_raw  = L1.get("pagerank_score", 0.0)
        voucher_count = L1.get("vouch_metrics", {}).get("vouches_received", 0)
        loyalty       = L1.get("network_relationships", {}).get("calculated_customer_loyalty_score", 0)

        pr_normalized  = min(pagerank_raw * 2000, 100)   # scale 0.01–0.05 → 20–100
        loyalty_bonus  = loyalty * 20
        raw_score      = pr_normalized * 0.6 + loyalty_bonus * 0.4
        final_score    = round(min(raw_score * fraud_penalty, 100))

        return {
            "social_score":           final_score,
            "fraud_flag":             fraud_flag,
            "pagerank_raw":           round(pagerank_raw, 6),
            "voucher_count":          voucher_count,
            "relationship_diversity": 1,
            "explanation": (
                f"Vouched by {voucher_count} merchants "
                f"({'FRAUD FLAG' if fraud_flag else 'no fraud detected'}). "
                f"Loyalty score: {loyalty}."
            )
        }

    # Fallback: graph-based scoring (used when no merchant_data passed)
    fraud_rings = detect_fraud_rings(G)
    fraud_flag  = any(merchant_id in ring for ring in fraud_rings)

    pagerank_scores = compute_pagerank_scores(G)
    pr_raw = pagerank_scores.get(merchant_id, 0.0)
    all_scores = list(pagerank_scores.values())
    pr_normalized = (pr_raw / max(all_scores)) * 100 if max(all_scores) > 0 else 0

    in_edges  = list(G.in_edges(merchant_id, data=True))
    voucher_count = len(in_edges)
    rel_types = set(d.get("relationship") for _, _, d in in_edges)
    diversity_bonus = min(len(rel_types) * 5, 15)

    raw_score    = pr_normalized + diversity_bonus
    fraud_pen    = 0.4 if fraud_flag else 0.0
    final_score  = round(min(raw_score * (1 - fraud_pen), 100))

    return {
        "social_score":           final_score,
        "fraud_flag":             fraud_flag,
        "pagerank_raw":           round(pr_raw, 6),
        "voucher_count":          voucher_count,
        "relationship_diversity": len(rel_types),
        "explanation": (
            f"Vouched by {voucher_count} merchants "
            f"({'FRAUD FLAG' if fraud_flag else 'no fraud detected'}). "
            f"Relationship diversity: {len(rel_types)} type(s)."
        )
    }