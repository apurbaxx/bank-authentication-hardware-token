import { useEffect, useState } from 'react'
import RiskBadge from './RiskBadge.jsx'

const STATUS_STYLE = {
  approved:      'text-green-800 bg-green-50 border-green-200',
  rejected:      'text-red-800 bg-red-50 border-red-200',
  pending:       'text-yellow-800 bg-yellow-50 border-yellow-200',
  otp_challenge: 'text-blue-800 bg-blue-50 border-blue-200',
}

const STATUS_LABEL = {
  approved:      'Approved',
  rejected:      'Blocked',
  pending:       'Pending',
  otp_challenge: 'OTP',
}

function StatCard({ label, value }) {
  return (
    <div className="flex-1 bg-white border border-gray-200 rounded-lg p-4">
      <div className="text-2xl font-bold font-mono text-gray-900">{value ?? '-'}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  )
}

export default function Dashboard({ refreshTick }) {
  const [txns, setTxns] = useState([])
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
    } catch {}
  }

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, 3000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => { if (refreshTick) fetchAll() }, [refreshTick])

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Stats */}
      <div className="flex gap-3">
        <StatCard label="Total" value={stats.total} />
        <StatCard label="Approved" value={stats.approved} />
        <StatCard label="Blocked" value={stats.blocked} />
        <StatCard label="Pending" value={stats.pending} />
        <StatCard label="OTP" value={stats.otp} />
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto bg-white border border-gray-200 rounded-lg">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-gray-50 border-b border-gray-200">
            <tr className="text-xs text-gray-500 uppercase tracking-wide">
              <th className="text-left px-4 py-3 font-medium">Time</th>
              <th className="text-left px-4 py-3 font-medium">Amount</th>
              <th className="text-left px-4 py-3 font-medium">Recipient</th>
              <th className="text-left px-4 py-3 font-medium">Risk</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Reason</th>
            </tr>
          </thead>
          <tbody>
            {txns.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-12 text-gray-400">
                  No transactions yet.
                </td>
              </tr>
            )}
            {txns.map(txn => (
              <>
                <tr
                  key={txn.transaction_id}
                  onClick={() => setExpanded(expanded === txn.transaction_id ? null : txn.transaction_id)}
                  className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono whitespace-nowrap">
                    {txn.created_at?.slice(11, 19)}
                  </td>
                  <td className="px-4 py-3 font-semibold text-gray-900 whitespace-nowrap">
                    Rs.{Number(txn.amount).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-gray-600 font-mono text-xs max-w-[140px] truncate">
                    {txn.recipient_upi}
                  </td>
                  <td className="px-4 py-3">
                    <RiskBadge score={txn.risk_score} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded border font-medium ${STATUS_STYLE[txn.status] || 'text-gray-500 border-gray-200'}`}>
                      {STATUS_LABEL[txn.status] || txn.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 max-w-[220px]">
                    <span className="line-clamp-2">{txn.reason}</span>
                  </td>
                </tr>

                {expanded === txn.transaction_id && (
                  <tr key={`${txn.transaction_id}-exp`} className="bg-gray-50">
                    <td colSpan={6} className="px-6 py-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                        {txn.factors && Object.entries(txn.factors).map(([k, v]) => (
                          <div key={k} className="bg-white border border-gray-200 rounded p-3">
                            <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">
                              {k.replace(/_/g, ' ')}
                            </div>
                            <div className="text-lg font-mono font-bold text-gray-900">{v}</div>
                            <div className="w-full bg-gray-200 rounded-full h-1 mt-1.5">
                              <div
                                className={`h-1 rounded-full ${v <= 40 ? 'bg-green-600' : v <= 70 ? 'bg-yellow-500' : 'bg-red-600'}`}
                                style={{ width: `${v}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-gray-600 leading-relaxed">{txn.reason}</p>
                      <div className="text-[10px] text-gray-400 mt-2 font-mono">
                        ID: {txn.transaction_id} | Device: {txn.device_id} | Location: {txn.location}
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
