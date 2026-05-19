/**
 * App.jsx — BankGuard main layout
 * Left sidebar: TransactionForm + TokenWidget
 * Main area: Dashboard
 */

import { useEffect, useState } from 'react'
import TransactionForm from './TransactionForm.jsx'
import Dashboard from './Dashboard.jsx'
import TokenWidget from './TokenWidget.jsx'

export default function App() {
  const [users, setUsers]           = useState([])
  const [refreshTick, setRefreshTick] = useState(0)

  useEffect(() => {
    fetch('/api/users')
      .then(r => r.json())
      .then(setUsers)
      .catch(() => {})
  }, [])

  const triggerRefresh = () => setRefreshTick(t => t + 1)

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top nav */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-screen-2xl mx-auto px-6 py-3 flex items-center gap-3">
          <span className="text-xl">🛡️</span>
          <span className="font-bold text-lg tracking-tight">BankGuard</span>
          <span className="text-slate-600 text-sm">|</span>
          <span className="text-slate-400 text-sm">Fraud Prevention System</span>
          <span className="ml-auto text-xs text-slate-600 font-mono">finVerse · NIT Allahabad</span>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 max-w-screen-2xl mx-auto w-full px-6 py-6 flex gap-6">
        {/* Left sidebar */}
        <aside className="w-80 shrink-0 flex flex-col gap-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <TransactionForm users={users} onResult={triggerRefresh} />
          </div>
          <TokenWidget onAction={triggerRefresh} />
        </aside>

        {/* Main dashboard */}
        <main className="flex-1 min-w-0">
          <Dashboard refreshTick={refreshTick} />
        </main>
      </div>
    </div>
  )
}
