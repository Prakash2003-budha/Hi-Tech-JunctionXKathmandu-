import { useState } from "react";
import { Brain, Globe } from "lucide-react";

const TRAIT_COLORS = {
  risk_aversion: "#4d9ef7",
  conscientiousness: "#00d4aa",
  social_trust: "#f5a623",
  resilience: "#ff7c40",
  planning: "#a78bfa",
};

const TRAIT_LABELS_NE = {
  risk_aversion: "जोखिम न्यूनीकरण",
  conscientiousness: "कर्तव्यनिष्ठा",
  social_trust: "सामाजिक विश्वास",
  resilience: "लचिलोपन",
  planning: "योजना",
};

const TRAIT_LABELS_EN = {
  risk_aversion: "Risk Aversion",
  conscientiousness: "Conscientiousness",
  social_trust: "Social Trust",
  resilience: "Resilience",
  planning: "Planning",
};

export function PsychometricTab({ questions, onSubmit, submitted }) {
  const [responses, setResponses] = useState({});
  const [lang, setLang] = useState("ne"); // 'ne' | 'en'
  const [showResult, setShowResult] = useState(null);
  const allAnswered =
    questions.length > 0 && Object.keys(responses).length === questions.length;

  const handleSelect = (qId, opt) =>
    setResponses((prev) => ({ ...prev, [qId]: opt }));

  const handleSubmit = () => {
    if (!allAnswered) return;
    const result = onSubmit(responses);
    if (result && typeof result.then === "function") {
      result.then((r) => setShowResult(r));
    }
  };

  const traitLabel = (t) =>
    lang === "ne" ? TRAIT_LABELS_NE[t] || t : TRAIT_LABELS_EN[t] || t;

  return (
    <div className="fade-in">
      {/* Header card */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 10,
          }}
        >
          <div className="card-title" style={{ marginBottom: 0 }}>
            {lang === "ne"
              ? "वित्तीय व्यक्तित्व मूल्याङ्कन"
              : "Financial Personality Assessment"}
          </div>

          {/* Language toggle */}
          <button
            onClick={() => setLang((l) => (l === "ne" ? "en" : "ne"))}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "var(--surface-2)",
              border: "1px solid var(--border-bright)",
              borderRadius: 20,
              padding: "4px 12px",
              cursor: "pointer",
              fontSize: 12,
              color: "var(--text-muted)",
              fontFamily: "var(--font-body)",
            }}
          >
            <Globe size={12} />
            {lang === "ne" ? "English" : "नेपाली"}
          </button>
        </div>

        <p
          style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 0 }}
        >
          {lang === "ne"
            ? "नेपालको अनौपचारिक अर्थव्यवस्थाका लागि ५ परिस्थितिजन्य प्रश्नहरू। Gemini API द्वारा संचालित।"
            : "5 situational questions calibrated for Nepal's informal economy. Powered by Gemini API."}
        </p>
      </div>

      {/* Questions */}
      {questions.map((q, i) => {
        const color = TRAIT_COLORS[q.trait] || "var(--accent)";
        const selected = responses[q.id];
        const opts =
          lang === "ne" ? q.options_ne || q.options : q.options_en || q.options;
        const qText =
          lang === "ne"
            ? q.question_ne || q.question
            : q.question_en || q.question;

        return (
          <div key={q.id} className="card" style={{ marginBottom: 12 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 10,
              }}
            >
              <span
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: "50%",
                  background: `${color}22`,
                  border: `1px solid ${color}44`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 11,
                  fontWeight: 700,
                  fontFamily: "var(--font-mono)",
                  color,
                }}
              >
                {i + 1}
              </span>
              <span
                className="badge"
                style={{
                  background: `${color}18`,
                  color,
                  borderColor: `${color}30`,
                }}
              >
                {traitLabel(q.trait)}
              </span>
            </div>

            <p
              style={{
                fontSize: 14,
                fontWeight: 500,
                color: "var(--text)",
                lineHeight: 1.6,
                marginBottom: 14,
                fontFamily:
                  lang === "ne"
                    ? "'Noto Sans Devanagari', var(--font-body)"
                    : "var(--font-body)",
              }}
            >
              {qText}
            </p>

            {Object.entries(opts || {}).map(([key, text]) => (
              <div
                key={key}
                className={`radio-option ${selected === key ? "selected" : ""}`}
                onClick={() => handleSelect(q.id, key)}
              >
                <div className="radio-dot" />
                <span className="radio-key">{key}</span>
                <span
                  style={{
                    fontSize: 13,
                    color: "var(--text)",
                    fontFamily:
                      lang === "ne"
                        ? "'Noto Sans Devanagari', var(--font-body)"
                        : "var(--font-body)",
                  }}
                >
                  {text}
                </span>
              </div>
            ))}
          </div>
        );
      })}

      {/* Submit */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginTop: 8,
          marginBottom: showResult ? 24 : 0,
        }}
      >
        <button
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={!allAnswered}
        >
          <Brain size={16} />
          {lang === "ne"
            ? "Gemini ले विश्लेषण गर्नुस् →"
            : "Analyze with Gemini →"}
        </button>
        {allAnswered && !submitted && (
          <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
            {lang === "ne"
              ? "सबै प्रश्नहरूको जवाफ दिइयो"
              : "All questions answered"}
          </span>
        )}
        {submitted && (
          <span className="badge badge-green">
            {lang === "ne"
              ? "✓ पेश गरियो — Trust Score ट्याबमा जानुस्"
              : "✓ Submitted — go to Trust Score tab"}
          </span>
        )}
      </div>

      {/* Gamification result panel */}
      {showResult &&
        (showResult.xp_earned > 0 ||
          showResult.badges_unlocked?.length > 0) && (
          <GamificationPanel result={showResult} lang={lang} />
        )}

      {/* Hallucination correction notice (dev/transparency) */}
      {showResult?.hallucination_corrections?.length > 0 && (
        <div
          style={{
            marginTop: 12,
            padding: "10px 14px",
            background: "rgba(245,166,35,0.06)",
            border: "1px solid rgba(245,166,35,0.15)",
            borderRadius: "var(--radius)",
            fontSize: 11,
            color: "var(--amber)",
            fontFamily: "var(--font-mono)",
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 4 }}>
            ⚠ Score validation applied
          </div>
          {showResult.hallucination_corrections.map((c, i) => (
            <div key={i}>{c}</div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Gamification Panel ───────────────────────────────────────────────────────

function GamificationPanel({ result, lang }) {
  const { xp_earned, badges_unlocked } = result;
  const [visible, setVisible] = useState(true);
  if (!visible) return null;

  return (
    <div
      style={{
        background:
          "linear-gradient(135deg, rgba(0,212,170,0.08) 0%, rgba(167,139,250,0.08) 100%)",
        border: "1px solid rgba(0,212,170,0.2)",
        borderRadius: "var(--radius-lg)",
        padding: 20,
        marginTop: 4,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 14,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              fontSize: 28,
              lineHeight: 1,
              filter: "drop-shadow(0 0 8px rgba(0,212,170,0.5))",
            }}
          >
            🎉
          </div>
          <div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 15,
                fontWeight: 700,
                color: "var(--text)",
              }}
            >
              {lang === "ne" ? "मूल्याङ्कन पूरा भयो!" : "Assessment Complete!"}
            </div>
            <div
              style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}
            >
              {lang === "ne"
                ? `+${xp_earned} XP अर्जित`
                : `+${xp_earned} XP earned`}
            </div>
          </div>
        </div>

        {/* XP pill */}
        <div
          style={{
            background: "rgba(0,212,170,0.12)",
            border: "1px solid rgba(0,212,170,0.3)",
            borderRadius: 24,
            padding: "6px 16px",
            fontFamily: "var(--font-display)",
            fontSize: 20,
            fontWeight: 800,
            color: "var(--accent)",
          }}
        >
          +{xp_earned} XP
        </div>
      </div>

      {/* XP progress bar (out of 200 max) */}
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: 11,
            color: "var(--text-muted)",
            marginBottom: 4,
          }}
        >
          <span>{lang === "ne" ? "यो सत्रमा XP" : "XP this session"}</span>
          <span>{xp_earned} / 200</span>
        </div>
        <div
          style={{
            height: 8,
            background: "var(--surface-2)",
            borderRadius: 4,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              borderRadius: 4,
              width: `${Math.min((xp_earned / 200) * 100, 100)}%`,
              background: "linear-gradient(90deg, var(--accent), #a78bfa)",
              transition: "width 1s cubic-bezier(0.34,1.56,0.64,1)",
            }}
          />
        </div>
      </div>

      {/* Badges */}
      {badges_unlocked?.length > 0 && (
        <div>
          <div
            style={{
              fontSize: 11,
              color: "var(--text-muted)",
              fontFamily: "var(--font-mono)",
              textTransform: "uppercase",
              letterSpacing: "0.8px",
              marginBottom: 10,
            }}
          >
            {lang === "ne" ? "ब्याज अनलक" : "Badges Unlocked"}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {badges_unlocked.map((b) => (
              <BadgeCard key={b.id} badge={b} lang={lang} />
            ))}
          </div>
        </div>
      )}

      {/* Credit personality highlight */}
      {result.credit_personality && (
        <div
          style={{
            marginTop: 14,
            padding: "10px 14px",
            background: "var(--surface-2)",
            borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span style={{ fontSize: 22 }}>🧠</span>
          <div>
            <div
              style={{
                fontSize: 12,
                color: "var(--text-muted)",
                marginBottom: 2,
              }}
            >
              {lang === "ne"
                ? "तपाईंको ऋण व्यक्तित्व"
                : "Your Credit Personality"}
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 15,
                fontWeight: 700,
                color: "var(--accent)",
              }}
            >
              {lang === "ne"
                ? result.credit_personality_ne || result.credit_personality
                : result.credit_personality}
            </div>
            {result.insight && (
              <div
                style={{
                  fontSize: 12,
                  color: "var(--text-muted)",
                  marginTop: 4,
                  lineHeight: 1.5,
                }}
              >
                {result.insight}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function BadgeCard({ badge, lang }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "8px 12px",
        background: hover ? "var(--surface-2)" : "var(--surface)",
        border: `1px solid ${hover ? "var(--border-bright)" : "var(--border)"}`,
        borderRadius: 24,
        cursor: "default",
        transition: "all 0.15s",
        transform: hover ? "translateY(-2px)" : "none",
      }}
    >
      <span style={{ fontSize: 18 }}>{badge.icon}</span>
      <div>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>
          {lang === "ne" ? badge.name_ne : badge.name_en}
        </div>
        <div
          style={{
            fontSize: 10,
            color: "var(--accent)",
            fontFamily: "var(--font-mono)",
          }}
        >
          +{badge.xp} XP
        </div>
      </div>

      {/* Tooltip */}
      {hover && (
        <div
          style={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 10,
            background: "var(--surface-2)",
            border: "1px solid var(--border-bright)",
            borderRadius: "var(--radius)",
            padding: "8px 12px",
            fontSize: 11,
            color: "var(--text-muted)",
            whiteSpace: "nowrap",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
            fontFamily:
              lang === "ne"
                ? "'Noto Sans Devanagari', var(--font-body)"
                : "var(--font-body)",
          }}
        >
          {lang === "ne" ? badge.desc_ne : badge.desc_en}
          <div
            style={{
              position: "absolute",
              top: "100%",
              left: "50%",
              transform: "translateX(-50%)",
              width: 0,
              height: 0,
              borderLeft: "6px solid transparent",
              borderRight: "6px solid transparent",
              borderTop: "6px solid var(--border-bright)",
            }}
          />
        </div>
      )}
    </div>
  );
}
