import clsx from 'clsx'

const TONES = {
  slate: 'bg-slate-50 text-slate-600',
  blue: 'bg-blue-50 text-blue-600',
  amber: 'bg-amber-50 text-amber-600',
  green: 'bg-emerald-50 text-emerald-600',
  red: 'bg-red-50 text-red-600',
  orange: 'bg-orange-50 text-orange-600',
}

export default function KpiCard({ label, value, icon: Icon, tone = 'blue', hint, trend }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 flex items-start justify-between gap-3">
      <div className="min-w-0">
        <p className="text-xs font-medium text-slate-500 truncate">{label}</p>
        <p className="text-2xl font-semibold text-slate-900 mt-1 truncate">{value}</p>
        {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
        {trend != null && (
          <p className={clsx('text-xs mt-1 font-medium', trend >= 0 ? 'text-emerald-600' : 'text-red-600')}>
            {trend >= 0 ? '▲' : '▼'} {Math.abs(trend)}%
          </p>
        )}
      </div>
      {Icon && (
        <div className={clsx('p-2.5 rounded-lg shrink-0', TONES[tone])}>
          <Icon size={20} />
        </div>
      )}
    </div>
  )
}
