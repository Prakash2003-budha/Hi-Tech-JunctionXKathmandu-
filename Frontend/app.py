import streamlit as st
import requests
import plotly.graph_objects as go
import json
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="TrustBridge",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 TrustBridge")
st.caption("Alternative Trust Middleware — Financial Inclusion for Unbanked Merchants")
st.divider()

# ---- Sidebar: Merchant selector ----
with st.sidebar:
    st.header("Select Merchant")
    try:
        merchants = requests.get(f"{API_URL}/merchants").json()
        names = {
            f"{m['name']} ({m['merchant_id']})": m["merchant_id"]
            for m in merchants
        }
        selected_label = st.selectbox("Merchant", list(names.keys()))
        merchant_id = names[selected_label]
        selected_merchant = requests.get(f"{API_URL}/merchants/{merchant_id}").json()
    except Exception as e:
        st.error(f"Backend not running or error occurred: {e}")
        st.info("Start with: `uvicorn Backend.main:app --reload`")
        st.stop()

    st.divider()
    st.metric("District", selected_merchant["district"])
    st.metric("Business", selected_merchant["business_type"].replace("_", " ").title())
    st.metric("Digital Footprint", "Yes ✓" if selected_merchant["digital_footprint"] else "No ✗")

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs([
    "📋 Psychometric Assessment",
    "📊 Trust Score",
    "🔗 Social Graph"
])

# ---- Tab 1: Psychometric ----
with tab1:
    st.subheader("Financial Personality Assessment")
    st.info("Answer all 5 situational questions. Powered by Gemini 2.5 Flash-Lite API.")

    try:
        questions = requests.get(f"{API_URL}/psychometric/questions").json()
    except Exception as e:
        st.error(f"Could not fetch questions: {e}")
        st.stop()
    
    responses = {}

    for q in questions:
        st.markdown(f"**{q['question']}**")
        options = q["options"]
        choice = st.radio(
            label=f"_{q['trait'].replace('_', ' ').title()}_",
            options=list(options.keys()),
            format_func=lambda x, opts=options: f"{x}: {opts[x]}",
            horizontal=False,
            key=q["id"]
        )
        responses[q["id"]] = choice
        st.divider()

    if st.button("Submit Assessment →", type="primary"):
        st.session_state["psychometric_responses"] = responses
        st.success("Responses saved. Go to 'Trust Score' tab to compute full score.")

# ---- Tab 2: Trust Score ----
with tab2:
    st.subheader("Compute Trust Score")

    psychometric_responses = st.session_state.get("psychometric_responses", {})
    if not psychometric_responses:
        st.warning("Complete the psychometric assessment first for a full score.")

    if st.button("Compute Full Trust Score ▶", type="primary"):
        with st.spinner("Running all three scoring engines..."):
            try:
                payload = {
                    "merchant_id": merchant_id,
                    "psychometric_responses": psychometric_responses or None
                }
                result = requests.post(
                    f"{API_URL}/score/{merchant_id}",
                    json=payload
                ).json()
                st.session_state["score_result"] = result
            except Exception as e:
                st.error(f"Error computing score: {e}")

    result = st.session_state.get("score_result")
    if result:
        # Main score display
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Trust Score", f"{result['final_score']}/100")
        col2.metric("Confidence", f"{result['confidence_pct']}%")
        col3.metric("Lending Tier", result['lending_tier']['tier'])
        col4.metric(
            "Max Loan",
            f"NPR {result['lending_tier']['max_loan_npr']:,}" if result['lending_tier']['max_loan_npr'] > 0 else "N/A"
        )

        if result.get("fraud_flag"):
            st.error("⚠️ FRAUD FLAG: This merchant appears in a mutual vouching ring.")

        st.divider()

        # Sub-score bar chart
        sub = result["sub_scores"]
        behavioral_detail = result.get("behavioral_detail", {})

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Social", "Psychometric", "Behavioral"],
            y=[sub["social"], sub["psychometric"], sub["behavioral"]],
            marker_color=["#7F77DD", "#1D9E75", "#BA7517"],
            text=[sub["social"], sub["psychometric"], sub["behavioral"]],
            textposition="auto"
        ))
        fig.update_layout(
            title="Three-layer sub-scores",
            yaxis_range=[0, 100],
            height=320,
            margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Behavioral detail
        if behavioral_detail:
            st.subheader("Behavioral breakdown")
            b_cols = st.columns(len(behavioral_detail))
            for i, (k, v) in enumerate(behavioral_detail.items()):
                b_cols[i].metric(k.replace("_", " ").title(), v)

        # Psychometric insight
        if result.get("credit_personality"):
            st.info(
                f"**Credit Personality:** {result['credit_personality']}  \n"
                f"{result.get('psychometric_insight', '')}"
            )

        # Improvement pathway
        st.subheader("Improvement pathway")
        for step in result.get("improvement_pathway", []):
            st.markdown(f"→ {step}")

        # Raw JSON
        with st.expander("Raw score JSON (for API integration)"):
            st.json(result)

# ---- Tab 3: Social Graph ----
with tab3:
    st.subheader("Community Vouching Network")
    try:
        stats = requests.get(f"{API_URL}/graph/stats").json()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Merchants", stats["nodes"])
        c2.metric("Vouch connections", stats["edges"])
        c3.metric("Network density", stats["density"])
        c4.metric("Avg clustering", stats["avg_clustering"])
    except Exception as e:
        st.error(f"Could not fetch graph stats: {e}")

    m_data = requests.get(f"{API_URL}/merchants/{merchant_id}").json()
    vouchers = m_data.get("vouchers", [])

    if vouchers:
        st.markdown(f"**{selected_merchant['name']}** is vouched by {len(vouchers)} merchant(s):")
        for v in vouchers:
            voucher_merchant = next(
                (m for m in merchants if m["merchant_id"] == v["voucher_id"]), None
            )
            name = voucher_merchant["name"] if voucher_merchant else v["voucher_id"]
            st.markdown(
                f"- **{name}** ({v['relationship'].replace('_', ' ')}) "
                f"· {v['months_known']} months · trust score: {v['voucher_trust_score']}"
            )
    else:
        st.info("No vouchers recorded for this merchant yet.")
