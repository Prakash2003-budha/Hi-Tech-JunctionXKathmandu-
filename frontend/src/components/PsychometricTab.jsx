import { useState } from 'react'
import { Brain } from 'lucide-react'

const TRAIT_COLORS = {
  risk_aversion:    '#4d9ef7',
  conscientiousness:'#00d4aa',
  social_trust:     '#f5a623',
  resilience:       '#ff7c40',
  planning:         '#a78bfa'
}

export function PsychometricTab({ questions, onSubmit, submitted }) {
  const [responses, setResponses] = useState({})
  const allAnswered = questions.length > 0 && Object.keys(responses).length === questions.length

  const handleSelect = (qId, opt) => {
    setResponses(prev => ({ ...prev, [qId]: opt }))
  }

  const handleSubmit = () => {
    if (allAnswered) onSubmit(responses)
  }

  return (
    <div className="fade-in">
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Financial Personality Assessment</div>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 0 }}>
          5 situational questions calibrated for Nepal's informal economy. Powered by Gemini API.
          Answers determine credit personality type and psychometric score (0–100).
        </p>
      </div>

      {questions.map((q, i) => {
        const color = TRAIT_COLORS[q.trait] || 'var(--accent)'
        return (
          <div key={q.id} className="card" style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14, gap: 12 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{
                    width: 22, height: 22, borderRadius: '50%',
                    background: `${color}22`, border: `1px solid ${color}44`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)', color
                  }}>{i + 1}</span>
                  <span className="badge" style={{ background: `${color}18`, color, borderColor: `${color}30` }}>
                    {q.trait.replace(/_/g, ' ')}
                  </span>
                </div>
                <p style={{ fontSize: 14, fontWeight: 500, color: 'var(--text)', lineHeight: 1.5 }}>{q.question}</p>
              </div>
            </div>

            {Object.entries(q.options).map(([key, text]) => (
              <div
                key={key}
                className={`radio-option ${responses[q.id] === key ? 'selected' : ''}`}
                onClick={() => handleSelect(q.id, key)}
              >
                <div className="radio-dot" />
                <span className="radio-key">{key}</span>
                <span style={{ fontSize: 13, color: 'var(--text)' }}>{text}</span>
              </div>
            ))}
          </div>
        )
      })}

      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 8 }}>
        <button
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={!allAnswered}
        >
          <Brain size={16} />
          Analyze with Gemini →
        </button>
        {allAnswered && !submitted && (
          <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>All questions answered</span>
        )}
        {submitted && (
          <span className="badge badge-green">✓ Submitted — go to Trust Score tab</span>
        )}
      </div>
    </div>
  )
}
