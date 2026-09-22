import clsx from 'clsx'

export default function Card({ children, className, title, actions, padded = true }) {
  return (
    <div className={clsx('bg-white rounded-lg border border-slate-200 shadow-sm', className)}>
      {(title || actions) && (
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-100">
          {title && <h3 className="text-sm font-semibold text-slate-800">{title}</h3>}
          {actions}
        </div>
      )}
      <div className={padded ? 'p-5' : ''}>{children}</div>
    </div>
  )
}
