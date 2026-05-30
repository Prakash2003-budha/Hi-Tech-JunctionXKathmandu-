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
            district=meta.get("location", ""),
            fraud_flag=m.get("layer_1_social_graph", {}).get("fraud_ring_risk", {}).get("is_fraud_ring_participant", False)
        )

    # Build REAL directed edges from vouch_edges_to field
    for m in merchants:
        mid = m["merchant_id"]
        L1 = m.get("layer_1_social_graph", {})
        vouch_weight = L1.get("vouch_metrics", {}).get("vouch_edge_weight", 1.0)
        
        # Real edges from seeded data
        for target_id in L1.get("vouch_edges_to", []):
            if target_id in G and target_id != mid:
                G.add_edge(mid, target_id, weight=vouch_weight, relationship="vouch")

    return G


def build_graph_from_edges(merchants: List[Dict], edges: List[Dict]) -> nx.DiGraph:
    """Build graph using DB edge records."""
    G = nx.DiGraph()
    for m in merchants:
        meta = m.get("business_metadata", {})
        G.add_node(
            m["merchant_id"],
            name=meta.get("owner_name", m["merchant_id"]),
            business_type=meta.get("business_type", ""),
            district=meta.get("location", ""),
            fraud_flag=m.get("layer_1_social_graph", {}).get("fraud_ring_risk", {}).get("is_fraud_ring_participant", False)
        )
    for e in edges:
        src = e.get("source") or e.get("from_merchant_id")
        tgt = e.get("target") or e.get("to_merchant_id")
        w = e.get("weight") or e.get("edge_weight", 1.0)
        if src in G and tgt in G:
            G.add_edge(src, tgt, weight=w, relationship="vouch")
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
    # Use pre-computed values from the schema if available
    if merchant_data:
        L1 = merchant_data.get("layer_1_social_graph", {})
        fraud_flag    = L1.get("fraud_ring_risk", {}).get("is_fraud_ring_participant", False)
        fraud_penalty = L1.get("fraud_ring_risk", {}).get("fraud_penalty_multiplier", 1.0)
        pagerank_raw  = L1.get("pagerank_score", 0.0)

        # Count REAL graph edges for this merchant
        in_edges = list(G.in_edges(merchant_id, data=True)) if merchant_id in G else []
        voucher_count = len(in_edges)
        loyalty = L1.get("network_relationships", {}).get("calculated_customer_loyalty_score", 0)

        pr_normalized  = min(pagerank_raw * 2000, 100)
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

    # Fallback: graph-based scoring
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
