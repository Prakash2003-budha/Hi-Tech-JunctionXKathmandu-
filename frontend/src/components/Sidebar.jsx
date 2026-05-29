import { useState } from 'react'

const BIZ_LABELS = {
  vegetables: '🥦', tea_shop: '🍵', clothing: '👗',
  hardware: '🔧', dairy: '🥛', pharmacy: '💊'
}

export function Sidebar({ merchants, selectedId, onSelect }) {
  const [search, setSearch] = useState('')

  const filtered = merchants.filter(m =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.district.toLowerCase().includes(search.toLowerCase()) ||
    m.business_type.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>Trust<span>Bridge</span></h1>
        <p>Alternative Trust Layer · Nepal</p>
      </div>

      <div className="sidebar-search">
        <input
          type="text"
          placeholder="Search merchants..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="sidebar-label">{filtered.length} merchants</div>

      <div className="merchant-list">
        {filtered.map(m => (
          <div
            key={m.merchant_id}
            className={`merchant-item ${selectedId === m.merchant_id ? 'active' : ''}`}
            onClick={() => onSelect(m.merchant_id)}
          >
            <div className="merchant-item-name">
              {BIZ_LABELS[m.business_type] || '🏪'} {m.name}
            </div>
            <div className="merchant-item-meta">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-dim)' }}>
                {m.merchant_id}
              </span>
              <span>·</span>
              <span>{m.district}</span>
              {m.digital_footprint && (
                <span style={{ color: 'var(--accent)', fontSize: 10 }}>● digital</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}
