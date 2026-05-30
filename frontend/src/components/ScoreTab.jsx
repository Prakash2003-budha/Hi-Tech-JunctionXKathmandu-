import { useState, useEffect } from "react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { Zap, AlertTriangle, TrendingUp, Shield } from "lucide-react";
import { ScoreRing } from "./ScoreRing.jsx";
import { api } from "../lib/api.js";

const TIER_STYLES = {
  A: { color: "var(--accent)", bg: "var(--accent-dim)" },
  B: { color: "var(--amber)", bg: "var(--amber-dim)" },
  C: { color: "var(--orange)", bg: "var(--orange-dim)" },
  D: { color: "var(--red)", bg: "var(--red-dim)" },
};
const SEGMENT_LABELS = {
  digital_native: "Digital Native",
  cash_merchant: "Cash Merchant",
  new_merchant: "New Merchant",
};

function SubScoreBar({ label, value, color }) {
  return (
    <div className="trait-row">
      <div className="trait-name">{label}</div>
      <div className="trait-bar-wrap">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${value}%`, background: color }}
          />
        </div>
      </div>
      <div className="trait-score" style={{ color }}>
        {value}
      </div>
    </div>
  );
}

function BadgePill({ badge }) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "5px 12px",
        borderRadius: 24,
        background: "rgba(0,212,170,0.08)",
        border: "1px solid rgba(0,212,170,0.2)",
        fontSize: 12,
        color: "var(--accent)",
      }}
    >
      <span style={{ fontSize: 16 }}>{badge.icon}</span>
      <span style={{ fontWeight: 600 }}>{badge.name_en}</span>
      <span
        style={{ opacity: 0.6, fontFamily: "var(--font-mono)", fontSize: 10 }}
      >
        +{badge.xp}XP
      </span>
    </div>
  );
}

export function ScoreTab({ merchant, psychometricResponses, onCompute }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!merchant?.merchant_id) return;
    api
      .getLatestScore(merchant.merchant_id)
      .then((data) => {
        if (data?.history?.length > 0) {
          const last = data.history[0];
          if (last.full_result) setResult(last.full_result);
        }
      })
      .catch(() => {});
  }, [merchant?.merchant_id]);

  const handleCompute = async () => {
    setLoading(true);
    setError(null);
    try {
      const fusionData = await onCompute(psychometricResponses);
      let mlData = null;
      try {
        mlData = await api.mlScore(merchant.merchant_id);
      } catch (_) {}
      setResult({ ...fusionData, ml: mlData });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const tierStyle = result ? TIER_STYLES[result.lending_tier.tier] : null;
  const radarData = result
    ? [
        { subject: "Social", A: result.sub_scores.social },
        { subject: "Psychometric", A: result.sub_scores.psychometric },
        { subject: "Behavioral", A: result.sub_scores.behavioral },
      ]
    : [];
  const behaviorData = result
    ? Object.entries(result.behavioral_detail || {}).map(([k, v]) => ({
        name: k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        value: v,
      }))
    : [];

  return (
    <div className="fade-in">
      {!psychometricResponses && (
        <div className="alert alert-warning" style={{ marginBottom: 16 }}>
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
          Psychometric not yet assessed — complete Tab 1 for a full score.
        </div>
      )}

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <button
          className="btn btn-primary"
          onClick={handleCompute}
          disabled={loading}
        >
          <Zap size={15} />
          {loading ? "Computing..." : "Compute Full Trust Score ▶"}
        </button>
        {result && <span className="badge badge-green">Score computed</span>}
      </div>

      {loading && (
        <div className="loading-center">
          <div className="loading-spinner" />
          <span>Running all 3 scoring engines...</span>
        </div>
      )}
      {error && (
        <div className="alert alert-error">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {result && !loading && (
        <>
          {result.fraud_flag && (
            <div className="alert alert-error">
              <AlertTriangle size={16} style={{ flexShrink: 0 }} />
              FRAUD FLAG: This merchant appears in a mutual vouching ring. Score
              penalized by 40%.
            </div>
          )}

          {/* ── Badges row ── */}
          {result.badges_unlocked?.length > 0 && (
            <div
              style={{
                marginBottom: 16,
                padding: "14px 16px",
                background:
                  "linear-gradient(135deg,rgba(0,212,170,0.06),rgba(167,139,250,0.06))",
                border: "1px solid rgba(0,212,170,0.15)",
                borderRadius: "var(--radius-lg)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 10,
                }}
              >
                <span style={{ fontSize: 18 }}>🏅</span>
                <span
                  style={{
                    fontSize: 12,
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.8px",
                  }}
                >
                  Badges earned
                </span>
                <span
                  style={{
                    marginLeft: "auto",
                    fontFamily: "var(--font-display)",
                    fontSize: 18,
                    fontWeight: 800,
                    color: "var(--accent)",
                  }}
                >
                  +{result.xp_earned} XP
                </span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {result.badges_unlocked.map((b) => (
                  <BadgePill key={b.id} badge={b} />
                ))}
              </div>
            </div>
          )}

          {/* ── Main score row ── */}
          <div
            className="grid-2"
            style={{ marginBottom: 16, alignItems: "start" }}
          >
            <div
              className="card"
              style={{ display: "flex", alignItems: "center", gap: 32 }}
            >
              <ScoreRing
                score={result.final_score}
                confidence={result.confidence}
              />
              <div>
                <div className="metric-label" style={{ marginBottom: 12 }}>
                  Lending Tier
                </div>
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "10px 20px",
                    borderRadius: 10,
                    background: tierStyle.bg,
                    border: `1px solid ${tierStyle.color}40`,
                  }}
                >
                  <span
                    style={{
                      fontSize: 32,
                      fontFamily: "var(--font-display)",
                      fontWeight: 800,
                      color: tierStyle.color,
                    }}
                  >
                    {result.lending_tier.tier}
                  </span>
                  <div>
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: tierStyle.color,
                      }}
                    >
                      {result.lending_tier.label}
                    </div>
                    {result.lending_tier.max_loan_npr > 0 && (
                      <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                        Up to NPR{" "}
                        {result.lending_tier.max_loan_npr.toLocaleString()}
                      </div>
                    )}
                    <div
                      style={{
                        fontSize: 11,
                        color: "var(--text-muted)",
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {result.lending_tier.interest_rate}
                    </div>
                  </div>
                </div>
                <div
                  style={{
                    marginTop: 16,
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 8,
                  }}
                >
                  <span className="tag">
                    {SEGMENT_LABELS[result.segment] || result.segment}
                  </span>
                  <span className="tag">
                    {result.data_sources_used} data sources
                  </span>
                  {result.credit_personality && (
                    <span className="tag">🧠 {result.credit_personality}</span>
                  )}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-title">Layer Breakdown</div>
              <SubScoreBar
                label="Social Graph"
                value={result.sub_scores.social}
                color="#a78bfa"
              />
              <SubScoreBar
                label="Psychometric"
                value={result.sub_scores.psychometric}
                color="var(--accent)"
              />
              <SubScoreBar
                label="Behavioral"
                value={result.sub_scores.behavioral}
                color="var(--amber)"
              />
              <div style={{ marginTop: 16 }}>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--text-dim)",
                    fontFamily: "var(--font-mono)",
                    marginBottom: 8,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  Weights ({result.segment})
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {Object.entries(result.weights_used).map(([k, v]) => (
                    <div
                      key={k}
                      style={{
                        flex: 1,
                        textAlign: "center",
                        padding: "6px 4px",
                        background: "var(--surface-2)",
                        borderRadius: 6,
                        border: "1px solid var(--border)",
                      }}
                    >
                      <div
                        style={{
                          fontSize: 16,
                          fontFamily: "var(--font-display)",
                          fontWeight: 700,
                        }}
                      >
                        {Math.round(v * 100)}%
                      </div>
                      <div
                        style={{
                          fontSize: 10,
                          color: "var(--text-muted)",
                          textTransform: "capitalize",
                        }}
                      >
                        {k}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ── Charts ── */}
          <div className="grid-2" style={{ marginBottom: 16 }}>
            <div className="card">
              <div className="card-title">Behavioral Breakdown</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart
                  data={behaviorData}
                  margin={{ top: 0, right: 0, bottom: 0, left: -20 }}
                >
                  <XAxis
                    dataKey="name"
                    tick={{
                      fontSize: 10,
                      fill: "var(--text-muted)",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface-2)",
                      border: "1px solid var(--border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    cursor={{ fill: "rgba(255,255,255,0.03)" }}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {behaviorData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={
                          [
                            "#00d4aa",
                            "#4d9ef7",
                            "#f5a623",
                            "#ff7c40",
                            "#a78bfa",
                          ][i % 5]
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div className="card-title">3-Layer Radar</div>
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="var(--border)" />
                  <PolarAngleAxis
                    dataKey="subject"
                    tick={{
                      fontSize: 11,
                      fill: "var(--text-muted)",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Radar
                    name="Score"
                    dataKey="A"
                    stroke="var(--accent)"
                    fill="var(--accent)"
                    fillOpacity={0.18}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ── Gemini insight ── */}
          {result.psychometric_insight && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-title">Gemini Insight</div>
              <p
                style={{ fontSize: 14, color: "var(--text)", lineHeight: 1.6 }}
              >
                "{result.psychometric_insight}"
              </p>
            </div>
          )}

          {/* ── Hallucination corrections (transparent) ── */}
          {result.hallucination_corrections?.length > 0 && (
            <div
              style={{
                marginBottom: 16,
                padding: "10px 14px",
                background: "rgba(245,166,35,0.06)",
                border: "1px solid rgba(245,166,35,0.15)",
                borderRadius: "var(--radius)",
                fontSize: 11,
                color: "var(--amber)",
                fontFamily: "var(--font-mono)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 4,
                }}
              >
                <Shield size={12} /> Score validation corrections applied
              </div>
              {result.hallucination_corrections.map((c, i) => (
                <div key={i}>{c}</div>
              ))}
            </div>
          )}

          {/* ── ML Risk ── */}
          {result.ml && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-title">ML Risk Assessment</div>
              <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                <span
                  style={{
                    fontSize: 20,
                    fontWeight: 700,
                    color:
                      result.ml.repayment_risk === "low"
                        ? "var(--accent)"
                        : result.ml.repayment_risk === "medium"
                          ? "var(--amber)"
                          : "var(--red)",
                  }}
                >
                  {(result.ml.repayment_risk || "unknown").toUpperCase()} RISK
                </span>
                <span className="tag">
                  confidence {Math.round((result.ml.confidence || 0) * 100)}%
                </span>
                {result.ml.anomaly_flag && (
                  <span className="badge badge-red">⚠ Anomaly detected</span>
                )}
              </div>
              {result.ml.probabilities &&
                Object.keys(result.ml.probabilities).length > 0 && (
                  <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                    {Object.entries(result.ml.probabilities).map(
                      ([label, prob]) => (
                        <div
                          key={label}
                          style={{
                            flex: 1,
                            textAlign: "center",
                            padding: "6px 4px",
                            background: "var(--surface-2)",
                            borderRadius: 6,
                            border: "1px solid var(--border)",
                          }}
                        >
                          <div style={{ fontSize: 16, fontWeight: 700 }}>
                            {Math.round(prob * 100)}%
                          </div>
                          <div
                            style={{
                              fontSize: 10,
                              color: "var(--text-muted)",
                              textTransform: "capitalize",
                            }}
                          >
                            {label}
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                )}
            </div>
          )}

          {/* ── Improvement pathway ── */}
          <div className="card">
            <div
              className="card-title"
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <TrendingUp size={14} /> Improvement Pathway
            </div>
            {result.improvement_pathway.map((step, i) => (
              <div key={i} className="step-item">
                <div className="step-num">{i + 1}</div>
                <span style={{ fontSize: 13, color: "var(--text)" }}>
                  {step}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
