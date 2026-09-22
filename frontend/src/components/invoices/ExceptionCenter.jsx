import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Badge from '../ui/Badge'
import EmptyState from '../ui/EmptyState'
import ErrorState from '../ui/ErrorState'
import LoadingState from '../ui/LoadingState'
import Pagination from '../ui/Pagination'
import Table from '../ui/Table'
import { useToast } from '../../context/ToastContext'
import { extractErrorMessage } from '../../services/api'
import { exceptionsApi } from '../../services/exceptions'
import ExceptionActionModal from './ExceptionActionModal'

const PAGE_SIZE = 20

const SEVERITY_COLOR = { LOW: 'blue', MEDIUM: 'amber', HIGH: 'orange', CRITICAL: 'red' }
const STATUS_COLOR = { OPEN: 'amber', RESOLVED: 'green', REJECTED: 'red', OVERRIDDEN: 'purple' }

export default function ExceptionCenter() {
  const navigate = useNavigate()
  const toast = useToast()
  const [exceptions, setExceptions] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('OPEN')
  const [modalState, setModalState] = useState({ open: false, action: null, exception: null })
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: PAGE_SIZE, ordering: '-severity,-created_at' }
      if (statusFilter) params.status = statusFilter
      const { data } = await exceptionsApi.list(params)
      setExceptions(data.results || data)
      setCount(data.count ?? (data.results || data).length)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter])

  const openModal = (action, exception) => setModalState({ open: true, action, exception })
  const closeModal = () => setModalState({ open: false, action: null, exception: null })

  const handleSubmit = async (comment) => {
    setSubmitting(true)
    try {
      const fn = { resolve: exceptionsApi.resolve, reject: exceptionsApi.reject, override: exceptionsApi.override }[
        modalState.action
      ]
      await fn(modalState.exception.id, comment)
      toast.success(`Exception ${modalState.action}d successfully.`)
      closeModal()
      load()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    { key: 'exception_type_display', header: 'Type' },
    {
      key: 'invoice_number',
      header: 'Invoice',
      render: (row) => (
        <button className="text-blue-600 font-medium hover:underline" onClick={() => navigate(`/invoices/${row.invoice}`)}>
          {row.invoice_number || row.invoice}
        </button>
      ),
    },
    { key: 'vendor_name', header: 'Vendor', render: (row) => row.vendor_name || '—' },
    { key: 'severity', header: 'Severity', render: (row) => <Badge color={SEVERITY_COLOR[row.severity]}>{row.severity}</Badge> },
    { key: 'created_at', header: 'Created', render: (row) => new Date(row.created_at).toLocaleDateString() },
    { key: 'assigned_to_name', header: 'Assigned To', render: (row) => row.assigned_to_name || 'Unassigned' },
    { key: 'status', header: 'Status', render: (row) => <Badge color={STATUS_COLOR[row.status]}>{row.status}</Badge> },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) =>
        row.status === 'OPEN' ? (
          <div className="flex gap-1.5" onClick={(e) => e.stopPropagation()}>
            <button className="text-xs font-medium text-emerald-600 hover:underline" onClick={() => openModal('resolve', row)}>
              Resolve
            </button>
            <button className="text-xs font-medium text-red-600 hover:underline" onClick={() => openModal('reject', row)}>
              Reject
            </button>
            <button className="text-xs font-medium text-slate-500 hover:underline" onClick={() => openModal('override', row)}>
              Override
            </button>
          </div>
        ) : (
          <span className="text-xs text-slate-400">{row.resolution_comment ? 'Actioned' : '—'}</span>
        ),
    },
  ]

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        {['OPEN', 'RESOLVED', 'REJECTED', 'OVERRIDDEN', ''].map((s) => (
          <button
            key={s || 'ALL'}
            onClick={() => {
              setStatusFilter(s)
              setPage(1)
            }}
            className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
              statusFilter === s ? 'bg-slate-800 text-white' : 'bg-white text-slate-500 border border-slate-200'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState label="Loading exceptions..." />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : exceptions.length === 0 ? (
        <EmptyState title="No exceptions" description="Nothing needs review right now." />
      ) : (
        <>
          <Table columns={columns} data={exceptions} />
          <div className="px-1">
            <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
          </div>
        </>
      )}

      <ExceptionActionModal
        open={modalState.open}
        action={modalState.action}
        exception={modalState.exception}
        onClose={closeModal}
        onSubmit={handleSubmit}
        submitting={submitting}
      />
    </div>
  )
}
