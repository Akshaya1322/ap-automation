import { ChevronLeft, ChevronRight } from 'lucide-react'
import Button from './Button'

export default function Pagination({ page, pageSize, count, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  const start = count === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(count, page * pageSize)

  return (
    <div className="flex items-center justify-between px-1 py-3 text-sm text-slate-500">
      <p>
        Showing <span className="font-medium text-slate-700">{start}</span>–
        <span className="font-medium text-slate-700">{end}</span> of{' '}
        <span className="font-medium text-slate-700">{count}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" icon={ChevronLeft} disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Prev
        </Button>
        <span className="text-xs text-slate-400">
          Page {page} of {totalPages}
        </span>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Next
          <ChevronRight size={16} />
        </Button>
      </div>
    </div>
  )
}
