/**
 * TokenWidget.jsx — ESP32 hardware token status panel.
 *
 * Hardware integration: When ESP32 is connected and polling /api/token/pending,
 * hardware_connected flips to true and the "Simulate" buttons become secondary.
 * Without hardware, the Simulate buttons are the primary interaction path.
 */

import { useEffect, useState } from 'react'

export default function TokenWidget({ onAction }) {
  const [status, setStatus]   = useState({ hardware_connected: false, pending_txn_id: null })
  const [pending, setPending] = useState(null)
  const [loading, setLoading] = useState(null) // 'approved' | 'rejected'

  const fetchStatus = async () => {
    try {
      const [s, p] = await Promise.all([
        fetch('/api/token/status').then(r => r.json()),
        fetch('/api/token/pending').then(r => r.json()),
      ])
      setStatus(s)
      setPending(p.pending ? p.transaction : null)
    } catch { /* backend not ready */ }
  }

  useEffect(() => {
    fetchStatus()
    const id = setInterval(fetchStatus, 2000)
    return () => clearInterval(id)
  }, [])

  const respond = async (decision) => {
    if (!pending) return
    setLoading(decision)
    try {
      await fetch('/api/token/response', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transaction_id: pending.transaction_id, decision }),
      })
      setPending(null)
      if (onAction) onAction()
    } finally {
      setLoading(null)
    }
  }

  const hasPending = !!pending

  return (
    <div className={`rounded-xl border p-4 transition-all duration-300
      ${hasPending
        ? 'border-red-500 bg-red-500/5 shadow-[0_0_20px_rgba(239,68,68,0.15)]'
        : 'border-slate-700 bg-slate-900'}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-base">🔐</span>
          <span className="text-sm font-semibold">Hardware Token</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${status.hardware_connected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
          <span className="text-xs text-slate-400">
            {/* [HARDWARE] This label flips to "ESP32 Online" when device polls */}
            {status.hardware_connected ? 'ESP32 Online' : 'No Hardware'}
          </span>
        </div>
      </div>

      {hasPending ? (
        <div className="space-y-3">
          {/* Pulsing alert */}
          <div className="flex items-center gap-2 text-red-400 animate-pulse">
            <span className="text-lg">⚠️</span>
            <span className="text-sm font-bold">AWAITING PHYSICAL APPROVAL</span>
          </div>

          {/* Transaction details — mirrors what OLED shows on ESP32 */}
          <div className="bg-slate-950 rounded-lg p-3 font-mono text-xs space-y-1 border border-red-500/20">
            <div className="text-red-400 font-bold">!! ALERT !!</div>
            <div>Rs.{Number(pending.amount).toLocaleString()}</div>
            <div className="truncate">To: {pending.recipient_upi?.slice(0, 20)}</div>
            <div className="text-slate-500">Score: {pending.risk_score}/100</div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">{pending.reason}</p>

          {/* Simulate buttons — primary when no hardware, secondary when ESP32 connected */}
          <div className="flex gap-2">
            <button
              onClick={() => respond('approved')}
              disabled={!!loading}
              className="flex-1 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 font-bold text-sm transition-colors"
            >
              {loading === 'approved' ? '...' : '✅ YES — Approve'}
            </button>
            <button
              onClick={() => respond('rejected')}
              disabled={!!loading}
              className="flex-1 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 font-bold text-sm transition-colors"
            >
              {loading === 'rejected' ? '...' : '🚫 NO — Block'}
            </button>
          </div>

          {status.hardware_connected && (
            <p className="text-[10px] text-slate-500 text-center">
              Hardware token is active — physical button press will also work
            </p>
          )}
        </div>
      ) : (
        <div className="text-center py-4 text-slate-500 text-sm">
          <div className="text-2xl mb-2">🛡️</div>
          No pending alerts
        </div>
      )}
    </div>
  )
}
