/**
 * TransactionForm.jsx — Demo transaction trigger form.
 * Left panel of the dashboard.
 */

import { useState } from 'react'

const PRESETS = [
  { label: '✅ Normal',    amount: '500',   recipient: 'mom@ybl',       device: 'device_abc',   location: 'Kolkata', user_id: 'user_001' },
  { label: '⚠️ Medium',   amount: '6000',  recipient: 'newshop@hdfc',  device: 'device_abc',   location: 'Kolkata', user_id: 'user_001' },
  { label: '🔴 High Risk', amount: '75000', recipient: 'fraud99@ybl',   device: 'new_device_x', location: 'Delhi',   user_id: 'user_001' },
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
      setResult({ ok: false, data: { error: 'Cannot reach backend. Is Flask running?' } })
    } finally {
      setLoading(false)
    }
  }

  const resultStyle = result
    ? result.data?.decision === 'approved'
      ? 'border-emerald-500 bg-emerald-500/10'
      : result.data?.decision === 'otp_challenge'
      ? 'border-amber-500 bg-amber-500/10'
      : 'border-red-500 bg-red-500/10 animate-pulse'
    : ''

  const decisionLabel = {
    approved:      '✅ APPROVED',
    otp_challenge: '⚠️ OTP CHALLENGE',
    pending_token: '🔴 SENT TO HARDWARE TOKEN',
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">Send Transaction</h2>

      {/* Presets */}
      <div className="flex gap-2 flex-wrap">
        {PRESETS.map(p => (
          <button
            key={p.label}
            onClick={() => applyPreset(p)}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
          >
            {p.label}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="flex flex-col gap-3">
        <div>
          <label className="text-xs text-slate-400 mb-1 block">User</label>
          <select
            value={form.user_id}
            onChange={e => set('user_id', e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          >
            {users.map(u => (
              <option key={u.user_id} value={u.user_id}>
                {u.name} (avg ₹{u.avg_amount.toLocaleString()})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs text-slate-400 mb-1 block">Amount (₹)</label>
          <input
            type="number" min="1" required
            value={form.amount}
            onChange={e => set('amount', e.target.value)}
            placeholder="e.g. 5000"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="text-xs text-slate-400 mb-1 block">Recipient UPI ID</label>
          <input
            type="text" required
            value={form.recipient_upi}
            onChange={e => set('recipient_upi', e.target.value)}
            placeholder="e.g. friend@okaxis"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Device ID</label>
            <input
              type="text" required
              value={form.device_id}
              onChange={e => set('device_id', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Location</label>
            <input
              type="text" required
              value={form.location}
              onChange={e => set('location', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 font-semibold text-sm transition-colors"
        >
          {loading ? 'Analyzing...' : 'SEND TRANSACTION'}
        </button>
      </form>

      {/* Result card */}
      {result && (
        <div className={`rounded-xl border p-4 transition-all ${resultStyle}`}>
          {result.ok ? (
            <>
              <div className="text-lg font-bold mb-1">
                {decisionLabel[result.data.decision] || result.data.decision}
              </div>
              <div className="text-xs text-slate-400 mb-2">
                Risk Score: <span className="font-mono font-bold text-white">{result.data.score}/100</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{result.data.reason}</p>
              {result.data.factors && (
                <div className="mt-3 grid grid-cols-2 gap-1.5">
                  {Object.entries(result.data.factors).map(([k, v]) => (
                    <div key={k} className="bg-slate-900/60 rounded px-2 py-1">
                      <div className="text-[10px] text-slate-500 capitalize">{k.replace(/_/g, ' ')}</div>
                      <div className="text-xs font-mono font-semibold">{v}</div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="text-red-400 text-sm">{result.data?.error || 'Unknown error'}</div>
          )}
        </div>
      )}
    </div>
  )
}
