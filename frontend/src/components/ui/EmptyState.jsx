import { Inbox } from 'lucide-react'
import Button from './Button'

export default function EmptyState({ icon: Icon = Inbox, title = 'Nothing here yet', description, action, actionLabel, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center px-4">
      <div className="p-3 rounded-full bg-slate-100 text-slate-400 mb-3">
        <Icon size={24} />
      </div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {description && <p className="text-xs text-slate-400 mt-1 max-w-sm">{description}</p>}
      {(action || (actionLabel && onAction)) && (
        <div className="mt-4">{action || <Button onClick={onAction}>{actionLabel}</Button>}</div>
      )}
    </div>
  )
}
