export function ScoreRing({ score, confidence, size = 160 }) {
  const r = 56
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r
  const pct = Math.max(0, Math.min(score, 100)) / 100
  const dash = pct * circumference

  const color =
    score >= 70 ? '#00d4aa' :
    score >= 50 ? '#f5a623' :
    score >= 30 ? '#ff7c40' : '#e05252'

  const tierLabel =
    score >= 70 ? 'A' :
    score >= 50 ? 'B' :
    score >= 30 ? 'C' : 'D'

  return (
    <div className="score-ring-container">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--surface-2)" strokeWidth="10" />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={`${dash} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: 'stroke-dasharray 0.8s cubic-bezier(0.34,1.2,0.64,1)', filter: `drop-shadow(0 0 8px ${color}88)` }}
        />
        <text x={cx} y={cy - 8} textAnchor="middle" fill="var(--text)" fontSize="28" fontWeight="800" fontFamily="'Syne', sans-serif">{score}</text>
        <text x={cx} y={cy + 12} textAnchor="middle" fill="var(--text-muted)" fontSize="11" fontFamily="'DM Mono', monospace">/100</text>
        <text x={cx} y={cy + 30} textAnchor="middle" fill={color} fontSize="13" fontWeight="700" fontFamily="'Syne', sans-serif">Tier {tierLabel}</text>
      </svg>
      {confidence !== undefined && (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.8px' }}>Confidence</div>
          <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text)' }}>{Math.round(confidence * 100)}%</div>
        </div>
      )}
    </div>
  )
}
