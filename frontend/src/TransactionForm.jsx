import { useState } from 'react'

const PRESETS = [
  { label: 'Normal',    amount: '500',   recipient: 'mom@ybl',       device: 'device_abc',   location: 'Kolkata', user_id: 'user_001' },
  { label: 'Medium',    amount: '6000',  recipient: 'newshop@hdfc',  device: 'device_abc',   location: 'Kolkata', user_id: 'user_001' },
  { label: 'High Risk', amount: '75000', recipient: 'fraud99@ybl',   device: 'new_device_x', location: 'Delhi',   user_id: 'user_001' },
]

export default function TransactionForm({ users, onResult }) {
  const [form, setForm] = useState({
    amount: '', recipient_upi: '', user_id: 'user_001',
    device_id: 'device_abc', location: 'Kolkata',
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const applyPreset = (p) => {
    setForm({ amount: p.amount, recipient_upi: p.recipient, user_id: p.user_id, device_id: p.device, location: p.location })
    setResult(null)
  }

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch('/api/transaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, amount: parseFloat(form.amount) }),
      })
      const data = await res.json()
      setResult({ ok: res.ok, data })
      if (onResult) onResult()
    } catch {
      setResult({ ok: false, data: { error: 'Cannot reach backend.' } })
    } finally {
      setLoading(false)
    }
  }

  const resultBorder = result
    ? result.data?.decision === 'approved'
      ? 'border-green-700 bg-green-50'
      : result.data?.decision === 'otp_challenge'
      ? 'border-yellow-600 bg-yellow-50'
      : 'border-red-700 bg-red-50'
    : ''

  const decisionLabel = {
    approved:      'APPROVED',
    otp_challenge: 'OTP CHALLENGE',
    pending_token: 'SENT TO HARDWARE TOKEN',
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">New Transaction</h2>

      <div className="flex gap-2 flex-wrap">
        {PRESETS.map(p => (
          <button
            key={p.label}
            onClick={() => applyPreset(p)}
            className="text-xs px-3 py-1.5 rounded border border-gray-300 bg-white hover:bg-gray-100 text-gray-700 transition-colors"
          >
            {p.label}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="flex flex-col gap-3">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">User</label>
          <select
            value={form.user_id}
            onChange={e => set('user_id', e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-green-800"
          >
            {users.map(u => (
              <option key={u.user_id} value={u.user_id}>
                {u.name} (avg Rs.{u.avg_amount.toLocaleString()})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs text-gray-500 mb-1 block">Amount (Rs.)</label>
          <input
            type="number" min="1" required
            value={form.amount}
            onChange={e => set('amount', e.target.value)}
            placeholder="e.g. 5000"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-green-800"
          />
        </div>

        <div>
          <label className="text-xs text-gray-500 mb-1 block">Recipient UPI ID</label>
          <input
            type="text" required
            value={form.recipient_upi}
            onChange={e => set('recipient_upi', e.target.value)}
            placeholder="e.g. friend@okaxis"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-green-800"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Device ID</label>
            <input
              type="text" required
              value={form.device_id}
              onChange={e => set('device_id', e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-green-800"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Location</label>
            <input
              type="text" required
              value={form.location}
              onChange={e => set('location', e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-green-800"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 rounded bg-green-800 hover:bg-green-900 disabled:opacity-50 text-white font-semibold text-sm transition-colors"
        >
          {loading ? 'Processing...' : 'Send Transaction'}
        </button>
      </form>

      {result && (
        <div className={`rounded border p-4 ${resultBorder}`}>
          {result.ok ? (
            <>
              <div className="text-sm font-bold text-gray-900 mb-1">
                {decisionLabel[result.data.decision] || result.data.decision}
              </div>
              <div className="text-xs text-gray-600 mb-2">
                Risk Score: <span className="font-mono font-bold">{result.data.score}/100</span>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">{result.data.reason}</p>
              {result.data.factors && (
                <div className="mt-3 grid grid-cols-2 gap-1.5">
                  {Object.entries(result.data.factors).map(([k, v]) => (
                    <div key={k} className="bg-white border border-gray-200 rounded px-2 py-1">
                      <div className="text-[10px] text-gray-400 capitalize">{k.replace(/_/g, ' ')}</div>
                      <div className="text-xs font-mono font-semibold text-gray-800">{v}</div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="text-red-700 text-sm">{result.data?.error || 'Unknown error'}</div>
          )}
        </div>
      )}
    </div>
  )
}
