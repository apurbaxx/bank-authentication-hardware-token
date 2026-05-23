import { useEffect, useState } from 'react'
import TransactionForm from './TransactionForm.jsx'
import Dashboard from './Dashboard.jsx'
import TokenWidget from './TokenWidget.jsx'

export default function App() {
  const [users, setUsers] = useState([])
  const [refreshTick, setRefreshTick] = useState(0)

  useEffect(() => {
    fetch('/api/users').then(r => r.json()).then(setUsers).catch(() => {})
  }, [])

  const triggerRefresh = () => setRefreshTick(t => t + 1)

  return (
    <div className="min-h-screen flex">
      {/* Left sidebar */}
      <aside className="w-80 shrink-0 border-r border-gray-200 bg-white p-5 flex flex-col gap-5 overflow-y-auto">
        <TransactionForm users={users} onResult={triggerRefresh} />
        <TokenWidget onAction={triggerRefresh} />
      </aside>

      {/* Main dashboard */}
      <main className="flex-1 min-w-0 p-6">
        <Dashboard refreshTick={refreshTick} />
      </main>
    </div>
  )
}
