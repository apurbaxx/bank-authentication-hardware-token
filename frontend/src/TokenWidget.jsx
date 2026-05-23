import { useEffect, useState } from 'react'

export default function TokenWidget({ onAction }) {
  const [status, setStatus] = useState({ hardware_connected: false, pending_txn_id: null })
  const [pending, setPending] = useState(null)
  const [loading, setLoading] = useState(null)

  const fetchStatus = async () => {
    try {
      const [s, p] = await Promise.all([
        fetch('/api/token/status').then(r => r.json()),
        fetch('/api/token/pending').then(r => r.json()),
      ])
      setStatus(s)
      setPending(p.pending ? p.transaction : null)
    } catch {}
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
    <div className={`rounded-lg border p-4 ${hasPending ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-white'}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-gray-700">Hardware Token</span>
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${status.hardware_connected ? 'bg-green-500' : 'bg-gray-300'}`} />
          <span className="text-xs text-gray-500">
            {status.hardware_connected ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>

      {hasPending ? (
        <div className="space-y-3">
          <div className="text-xs font-semibold text-red-800 uppercase tracking-wide">
            Awaiting Approval
          </div>

          <div className="bg-white border border-gray-200 rounded p-3 font-mono text-xs space-y-1">
            <div className="font-bold text-gray-900">Rs.{Number(pending.amount).toLocaleString()}</div>
            <div className="text-gray-600 truncate">To: {pending.recipient_upi}</div>
            <div className="text-gray-400">Score: {pending.risk_score}/100</div>
          </div>

          <p className="text-xs text-gray-500 leading-relaxed">{pending.reason}</p>

          <div className="flex gap-2">
            <button
              onClick={() => respond('approved')}
              disabled={!!loading}
              className="flex-1 py-2 rounded bg-green-700 hover:bg-green-800 disabled:opacity-50 text-white font-semibold text-sm transition-colors"
            >
              {loading === 'approved' ? '...' : 'Approve'}
            </button>
            <button
              onClick={() => respond('rejected')}
              disabled={!!loading}
              className="flex-1 py-2 rounded bg-red-700 hover:bg-red-800 disabled:opacity-50 text-white font-semibold text-sm transition-colors"
            >
              {loading === 'rejected' ? '...' : 'Reject'}
            </button>
          </div>

          {status.hardware_connected && (
            <p className="text-[10px] text-gray-400 text-center">
              Physical button press will also work
            </p>
          )}
        </div>
      ) : (
        <div className="text-center py-4 text-gray-400 text-sm">
          No pending alerts
        </div>
      )}
    </div>
  )
}
