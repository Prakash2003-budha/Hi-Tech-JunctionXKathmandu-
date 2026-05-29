import { useEffect, useState } from "react";
import { Brain, BarChart2, Network, User } from "lucide-react";
import { api } from "./lib/api.js";
import { Sidebar } from "./components/Sidebar.jsx";
import { PsychometricTab } from "./components/PsychometricTab.jsx";
import { ScoreTab } from "./components/ScoreTab.jsx";
import { GraphTab } from "./components/GraphTab.jsx";

const BIZ_LABELS = {
  vegetables: "🥦",
  tea_shop: "🍵",
  clothing: "👗",
  hardware: "🔧",
  dairy: "🥛",
  pharmacy: "💊",
};

const TABS = [
  { id: "psychometric", label: "Psychometric", icon: Brain },
  { id: "score", label: "Trust Score", icon: BarChart2 },
  { id: "graph", label: "Social Graph", icon: Network },
];

export default function App() {
  const [merchants, setMerchants] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedMerchant, setSelectedMerchant] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [activeTab, setActiveTab] = useState("psychometric");
  const [psychResponses, setPsychResponses] = useState(null);
  const [psychSubmitted, setPsychSubmitted] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.getMerchants(), api.getQuestions()])
      .then(([ms, qs]) => {
        setMerchants(ms);
        setQuestions(qs);
        if (ms.length > 0) setSelectedId(ms[0].merchant_id);
      })
      .catch((e) => setError("Cannot reach API — start the backend first."));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api
      .getMerchant(selectedId)
      .then(setSelectedMerchant)
      .catch(() => {});
    // Reset psychometric when merchant changes
    setPsychResponses(null);
    setPsychSubmitted(false);
  }, [selectedId]);

  const handlePsychSubmit = (responses) => {
    setPsychResponses(responses);
    setPsychSubmitted(true);
    setActiveTab("score");
  };

  const handleComputeScore = (responses) => {
    return api.computeScore(selectedId, responses);
  };

  if (error)
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <div style={{ fontSize: 40 }}>⚡</div>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 22,
            fontWeight: 700,
          }}
        >
          Backend not running
        </div>
        <div style={{ color: "var(--text-muted)", fontSize: 14 }}>{error}</div>
        <code
          style={{
            background: "var(--surface)",
            padding: "12px 20px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            fontFamily: "var(--font-mono)",
            fontSize: 13,
          }}
        >
          cd backend && uv run uvicorn main:app --reload --port 8000
        </code>
      </div>
    );

  return (
    <div className="app">
      <Sidebar
        merchants={merchants}
        selectedId={selectedId}
        onSelect={(id) => {
          setSelectedId(id);
          setActiveTab("psychometric");
        }}
      />

      <div className="main">
        {selectedMerchant && (
          <>
            <div className="page-header">
              <div className="page-header-info">
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    marginBottom: 6,
                  }}
                >
                  <div
                    style={{
                      width: 42,
                      height: 42,
                      borderRadius: "50%",
                      background: "var(--surface-2)",
                      border: "1px solid var(--border-bright)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 20,
                    }}
                  >
                    {BIZ_LABELS[selectedMerchant.business_type] || "🏪"}
                  </div>
                  <div>
                    <h2>
                      {selectedMerchant.name || selectedMerchant.legal_name}
                    </h2>
                    <p>
                      {selectedMerchant.business_type} ·{" "}
                      {selectedMerchant.district} ·{" "}
                      {selectedMerchant.months_active} months active
                    </p>
                  </div>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap",
                  alignItems: "flex-start",
                }}
              >
                <span
                  className="badge badge-gray"
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  {selectedMerchant.merchant_id}
                </span>
                {selectedMerchant.digital_footprint && (
                  <span className="badge badge-green">Digital</span>
                )}
                {selectedMerchant.esewa_registered && (
                  <span className="badge badge-blue">eSewa</span>
                )}
                {selectedMerchant.khalti_registered && (
                  <span className="badge badge-blue">Khalti</span>
                )}
              </div>
            </div>

            <div className="tabs">
              {TABS.map((t) => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.id}
                    className={`tab-btn ${activeTab === t.id ? "active" : ""}`}
                    onClick={() => setActiveTab(t.id)}
                  >
                    <Icon size={14} /> {t.label}
                    {t.id === "score" && psychSubmitted && (
                      <span
                        className="badge badge-green"
                        style={{
                          marginLeft: 4,
                          padding: "1px 6px",
                          fontSize: 9,
                        }}
                      >
                        ready
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="page-content">
              {activeTab === "psychometric" && (
                <PsychometricTab
                  questions={questions}
                  onSubmit={handlePsychSubmit}
                  submitted={psychSubmitted}
                />
              )}
              {activeTab === "score" && (
                <ScoreTab
                  merchant={selectedMerchant}
                  psychometricResponses={psychResponses}
                  onCompute={handleComputeScore}
                />
              )}
              {activeTab === "graph" && (
                <GraphTab
                  merchantId={selectedId}
                  merchantName={selectedMerchant.name}
                />
              )}
            </div>
          </>
        )}

        {!selectedMerchant && merchants.length > 0 && (
          <div className="loading-center">
            <div className="loading-spinner" />
          </div>
        )}
      </div>
    </div>
  );
}
