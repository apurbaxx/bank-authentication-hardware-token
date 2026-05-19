/**
 * Dashboard.jsx — Live transaction table with stats bar.
 * Auto-refreshes every 3 seconds.
 */

import { useEffect, useState } from 'react'
import RiskBadge from './RiskBadge.jsx'

const STATUS_STYLE = {
  approved:      'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  rejected:      'text-red-400 bg-red-500/10 border-red-500/30',
  pending:       'text-amber-400 bg-amber-500/10 border-amber-500/30',
  otp_challenge: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
}

const STATUS_LABEL = {
  approved:      '✅ Approved',
  rejected:      '🚫 Blocked',
  pending:       '⏳ Pending Token',
  otp_challenge: '🔐 OTP Challenge',
}

function StatCard({ label, value, color }) {
  return (
    <div className={`flex-1 rounded-xl border bg-slate-900 p-4 ${color}`}>
      <div className="text-2xl font-bold font-mono">{value ?? '—'}</div>
      <div className="text-xs text-slate-400 mt-0.5 uppercase tracking-wider">{label}</div>
    </div>
  )
}

export default function Dashboard({ refreshTick }) {
  const [txns, setTxns]   = useState([])
  const [stats, setStats] = useState({})
  const [expanded, setExpanded] = useState(null)

  const fetchAll = async () => {
    try {
      const [t, s] = await Promise.all([
        fetch('/api/transactions').then(r => r.json()),
        fetch('/api/dashboard/stats').then(r => r.json()),
      ])
      setTxns(t)
      setStats(s)
    } catch { /* backend not ready yet */ }
  }

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, 3000)
    return () => clearInterval(id)
  }, [])

  // Re-fetch immediately when parent signals a new transaction
  useEffect(() => { if (refreshTick) fetchAll() }, [refreshTick])

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Stats bar */}
      <div className="flex gap-3">
        <StatCard label="Total"    value={stats.total}    color="border-slate-700" />
        <StatCard label="Approved" value={stats.approved} color="border-emerald-800" />
        <StatCard label="Blocked"  value={stats.blocked}  color="border-red-800" />
        <StatCard label="Pending"  value={stats.pending}  color="border-amber-800" />
        <StatCard label="OTP"      value={stats.otp}      color="border-blue-800" />
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto rounded-xl border border-slate-800 scrollbar-thin">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-900 border-b border-slate-800">
            <tr className="text-xs text-slate-400 uppercase tracking-wider">
              <th className="text-left px-4 py-3">Time</th>
              <th className="text-left px-4 py-3">Amount</th>
              <th className="text-left px-4 py-3">Recipient</th>
              <th className="text-left px-4 py-3">Risk</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Reason</th>
            </tr>
          </thead>
          <tbody>
            {txns.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-12 text-slate-500">
                  No transactions yet. Send one using the form.
                </td>
              </tr>
            )}
            {txns.map(txn => (
              <>
                <tr
                  key={txn.transaction_id}
                  onClick={() => setExpanded(expanded === txn.transaction_id ? null : txn.transaction_id)}
                  className={`border-b border-slate-800/50 hover:bg-slate-800/40 cursor-pointer transition-colors
                    ${txn.status === 'pending' ? 'bg-amber-500/5' : ''}`}
                >
                  <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap font-mono">
                    {txn.created_at?.slice(11, 19)}
                  </td>
                  <td className="px-4 py-3 font-semibold whitespace-nowrap">
                    ₹{Number(txn.amount).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-slate-300 font-mono text-xs max-w-[140px] truncate">
                    {txn.recipient_upi}
                  </td>
                  <td className="px-4 py-3">
                    <RiskBadge score={txn.risk_score} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full border font-medium ${STATUS_STYLE[txn.status] || 'text-slate-400 border-slate-700'}`}>
                      {STATUS_LABEL[txn.status] || txn.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400 max-w-[220px]">
                    <span className="line-clamp-2">{txn.reason}</span>
                  </td>
                </tr>

                {/* Expanded row — factor breakdown */}
                {expanded === txn.transaction_id && (
                  <tr key={`${txn.transaction_id}-exp`} className="bg-slate-900/80">
                    <td colSpan={6} className="px-6 py-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                        {txn.factors && Object.entries(txn.factors).map(([k, v]) => (
                          <div key={k} className="bg-slate-800 rounded-lg p-3">
                            <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                              {k.replace(/_/g, ' ')}
                            </div>
                            <div className="text-lg font-mono font-bold">{v}</div>
                            <div className="w-full bg-slate-700 rounded-full h-1 mt-1.5">
                              <div
                                className={`h-1 rounded-full ${v <= 40 ? 'bg-emerald-500' : v <= 70 ? 'bg-amber-500' : 'bg-red-500'}`}
                                style={{ width: `${v}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{txn.reason}</p>
                      <div className="text-[10px] text-slate-500 mt-2 font-mono">
                        ID: {txn.transaction_id} · Device: {txn.device_id} · Location: {txn.location}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
