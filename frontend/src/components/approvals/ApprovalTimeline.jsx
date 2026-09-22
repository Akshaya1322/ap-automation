import { Check, Clock, MessageSquare, X } from 'lucide-react'
import clsx from 'clsx'
import { ROLE_LABELS } from '../../utils/navigation'

const STATUS_CONFIG = {
  APPROVED: { icon: Check, color: 'text-emerald-600 bg-emerald-100' },
  REJECTED: { icon: X, color: 'text-red-600 bg-red-100' },
  CHANGES_REQUESTED: { icon: MessageSquare, color: 'text-amber-600 bg-amber-100' },
  PENDING: { icon: Clock, color: 'text-slate-400 bg-slate-100' },
  SKIPPED: { icon: Clock, color: 'text-slate-300 bg-slate-50' },
}

export default function ApprovalTimeline({ steps }) {
  return (
    <ol className="relative border-l border-slate-200 ml-3 space-y-6">
      {steps.map((step) => {
        const cfg = STATUS_CONFIG[step.status] || STATUS_CONFIG.PENDING
        const Icon = cfg.icon
        return (
          <li key={step.id} className="ml-5">
            <span className={clsx('absolute -left-3.5 flex items-center justify-center w-7 h-7 rounded-full', cfg.color)}>
              <Icon size={14} />
            </span>
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-medium text-slate-800">
                Step {step.step_number}: {ROLE_LABELS[step.role_required] || step.role_required}
              </p>
              {step.is_current_step && step.status === 'PENDING' && (
                <span className="text-[10px] font-semibold uppercase tracking-wide text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                  Current
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {step.assigned_user_name ? `Assigned to ${step.assigned_user_name}` : 'Unassigned'} &middot; {step.status}
            </p>
            {step.actions?.map((a) => (
              <div key={a.id} className="mt-2 bg-slate-50 rounded-md px-3 py-2">
                <p className="text-xs font-medium text-slate-700">
                  {a.actor_name} &middot; {a.action.replace('_', ' ')} &middot;{' '}
                  <span className="text-slate-400 font-normal">{new Date(a.created_at).toLocaleString()}</span>
                </p>
                {a.comment && <p className="text-xs text-slate-500 mt-1">{a.comment}</p>}
              </div>
            ))}
          </li>
        )
      })}
    </ol>
  )
}
