const BASE = '/api'

async function request(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  getMerchants: () => request('/merchants'),
  getMerchant: (id) => request(`/merchants/${id}`),
  getQuestions: () => request('/psychometric/questions'),
  getGraphStats: () => request('/graph/stats'),
  getGraphNeighbors: (id) => request(`/graph/neighbors/${id}`),
  computeScore: (id, responses) =>
    request(`/score/${id}`, {
      method: 'POST',
      body: JSON.stringify({ merchant_id: id, psychometric_responses: responses || null })
    }),
  mlScore: (id) => request(`/ml-score/${id}`)
}
