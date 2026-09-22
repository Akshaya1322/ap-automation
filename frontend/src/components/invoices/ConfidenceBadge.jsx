import { AlertCircle, CheckCircle2, TriangleAlert } from 'lucide-react'
import clsx from 'clsx'

const CONFIG = {
  HIGH: { color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2 },
  MEDIUM: { color: 'bg-amber-100 text-amber-700', icon: TriangleAlert },
  LOW: { color: 'bg-red-100 text-red-700', icon: AlertCircle },
}

export default function ConfidenceBadge({ level, score, className }) {
  if (!level) return <span className="text-slate-300 text-xs">—</span>
  const cfg = CONFIG[level] || CONFIG.LOW
  const Icon = cfg.icon
  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', cfg.color, className)}>
      <Icon size={11} />
      {level}
      {score != null && <span className="opacity-70">({Math.round(score)}%)</span>}
    </span>
  )
}
