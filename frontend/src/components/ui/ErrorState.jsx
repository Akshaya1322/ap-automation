import { AlertTriangle, RotateCw } from 'lucide-react'
import Button from './Button'

export default function ErrorState({ message = 'Something went wrong.', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center px-4">
      <div className="p-3 rounded-full bg-red-50 text-red-500 mb-3">
        <AlertTriangle size={24} />
      </div>
      <p className="text-sm font-medium text-slate-700">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" icon={RotateCw} onClick={onRetry} className="mt-4">
          Retry
        </Button>
      )}
    </div>
  )
}
