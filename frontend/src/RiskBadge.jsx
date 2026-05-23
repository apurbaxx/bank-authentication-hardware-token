export default function RiskBadge({ score }) {
  const s = Number(score) || 0

  const config =
    s <= 40
      ? { label: 'LOW',    text: 'text-green-800', bg: 'bg-green-50', border: 'border-green-200' }
      : s <= 70
      ? { label: 'MED',    text: 'text-yellow-800', bg: 'bg-yellow-50', border: 'border-yellow-200' }
      : { label: 'HIGH',   text: 'text-red-800', bg: 'bg-red-50', border: 'border-red-200' }

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded border ${config.bg} ${config.border} ${config.text}`}>
      {config.label}
      <span className="font-mono">{s}</span>
    </span>
  )
}
