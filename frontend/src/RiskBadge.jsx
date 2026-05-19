/**
 * RiskBadge.jsx — Displays a risk score as a colored badge with label.
 */

export default function RiskBadge({ score }) {
  const s = Number(score) || 0

  const config =
    s <= 40
      ? { label: 'LOW',    bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/40', bar: 'bg-emerald-500' }
      : s <= 70
      ? { label: 'MEDIUM', bg: 'bg-amber-500/20',   text: 'text-amber-400',   border: 'border-amber-500/40',   bar: 'bg-amber-500'   }
      : { label: 'HIGH',   bg: 'bg-red-500/20',     text: 'text-red-400',     border: 'border-red-500/40',     bar: 'bg-red-500'     }

  return (
    <div className={`inline-flex flex-col items-center gap-1 px-2 py-1 rounded-lg border ${config.bg} ${config.border} min-w-[64px]`}>
      <span className={`text-xs font-bold tracking-widest ${config.text}`}>{config.label}</span>
      <div className="w-full bg-slate-700 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full transition-all ${config.bar}`}
          style={{ width: `${s}%` }}
        />
      </div>
      <span className={`text-xs font-mono font-semibold ${config.text}`}>{s}/100</span>
    </div>
  )
}
