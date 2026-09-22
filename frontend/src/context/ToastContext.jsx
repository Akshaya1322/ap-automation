import { CheckCircle2, Info, TriangleAlert, X, XCircle } from 'lucide-react'
import { createContext, useCallback, useContext, useState } from 'react'

const ToastContext = createContext(null)

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  warning: TriangleAlert,
  info: Info,
}

const STYLES = {
  success: 'bg-white border-l-4 border-emerald-500 text-slate-800',
  error: 'bg-white border-l-4 border-red-500 text-slate-800',
  warning: 'bg-white border-l-4 border-amber-500 text-slate-800',
  info: 'bg-white border-l-4 border-blue-500 text-slate-800',
}

let idCounter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const remove = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (message, type = 'info', duration = 4500) => {
      const id = ++idCounter
      setToasts((prev) => [...prev, { id, message, type }])
      if (duration) setTimeout(() => remove(id), duration)
      return id
    },
    [remove]
  )

  const toast = {
    success: (msg) => push(msg, 'success'),
    error: (msg) => push(msg, 'error'),
    warning: (msg) => push(msg, 'warning'),
    info: (msg) => push(msg, 'info'),
  }

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm pointer-events-none">
        {toasts.map((t) => {
          const Icon = ICONS[t.type]
          return (
            <div
              key={t.id}
              className={`pointer-events-auto shadow-lg rounded-md px-4 py-3 flex items-start gap-3 ${STYLES[t.type]}`}
              role="alert"
            >
              <Icon size={18} className="mt-0.5 shrink-0" />
              <p className="text-sm flex-1">{t.message}</p>
              <button onClick={() => remove(t.id)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
