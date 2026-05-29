import { useEffect, useState } from 'react'
import { api } from '../lib/api.js'
import { Network } from 'lucide-react'

export function GraphTab({ merchantId, merchantName }) {
  const [stats, setStats] = useState(null)
  const [neighbors, setNeighbors] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.getGraphStats(),
      api.getGraphNeighbors(merchantId)
    ]).then(([s, n]) => {
      setStats(s)
      setNeighbors(n)
    }).finally(() => setLoading(false))
  }, [merchantId])

  if (loading) return (
    <div className="loading-center fade-in">
      <div className="loading-spinner" />
      <span>Loading graph data...</span>
    </div>
  )

  return (
    <div className="fade-in">
      {/* Network stats */}
      {stats && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title">Network Statistics</div>
          <div className="grid-4">
            {[
              { label: 'Total Merchants', value: stats.nodes },
              { label: 'Vouch Connections', value: stats.edges },
              { label: 'Network Density', value: stats.density },
              { label: 'Avg Clustering', value: stats.avg_clustering },
            ].map(s => (
              <div key={s.label} className="stat-banner" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <div style={{ fontSize: 22, fontFamily: 'var(--font-display)', fontWeight: 800 }}>{s.value}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {neighbors && (
        <div className="grid-2">
          {/* Vouched by */}
          <div className="card">
            <div className="card-title">
              Vouched By
              <span style={{ marginLeft: 8, fontSize: 18, fontFamily: 'var(--font-display)', color: 'var(--accent)', verticalAlign: 'middle' }}>
                {neighbors.vouched_by.length}
              </span>
            </div>
            {neighbors.vouched_by.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No vouchers recorded yet.</p>
            ) : neighbors.vouched_by.map(v => (
              <div key={v.id} className="graph-node">
                <div className="node-avatar">{v.name[0]}</div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{v.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{v.id}</div>
                </div>
                <div style={{ marginLeft: 'auto' }}>
                  <span className="badge badge-green">→ vouches</span>
                </div>
              </div>
            ))}
          </div>

          {/* Vouches for */}
          <div className="card">
            <div className="card-title">
              Vouches For
              <span style={{ marginLeft: 8, fontSize: 18, fontFamily: 'var(--font-display)', color: 'var(--amber)', verticalAlign: 'middle' }}>
                {neighbors.vouches_for.length}
              </span>
            </div>
            {neighbors.vouches_for.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Does not vouch for anyone yet.</p>
            ) : neighbors.vouches_for.map(v => (
              <div key={v.id} className="graph-node">
                <div className="node-avatar" style={{ borderColor: 'rgba(245,166,35,0.3)', color: 'var(--amber)' }}>{v.name[0]}</div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{v.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{v.id}</div>
                </div>
                <div style={{ marginLeft: 'auto' }}>
                  <span className="badge badge-amber">vouched →</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Network size={14} /> How Social Scoring Works
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 8 }}>
          {[
            { rel: 'Supplier', weight: '100%', color: 'var(--accent)' },
            { rel: 'Peer Merchant', weight: '80%', color: 'var(--blue)' },
            { rel: 'Community Elder', weight: '60%', color: 'var(--amber)' },
            { rel: 'Family Member', weight: '40%', color: 'var(--text-muted)' },
          ].map(r => (
            <div key={r.rel} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--surface-2)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <span style={{ fontSize: 13 }}>{r.rel}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: r.color, fontWeight: 600 }}>{r.weight}</span>
            </div>
          ))}
        </div>
        <p style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
          Edge weight = relationship_type × voucher_trust_score × min(months_known/24, 1). 
          PageRank (α=0.85) propagates trust across the network. Mutual cliques of 3+ with no external edges are flagged as potential fraud rings.
        </p>
      </div>
    </div>
  )
}
