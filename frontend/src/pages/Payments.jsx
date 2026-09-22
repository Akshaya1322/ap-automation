import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import ErrorState from '../components/ui/ErrorState'
import LoadingState from '../components/ui/LoadingState'
import Pagination from '../components/ui/Pagination'
import StatusBadge from '../components/ui/StatusBadge'
import Table from '../components/ui/Table'
import { extractErrorMessage } from '../services/api'
import { paymentsApi } from '../services/payments'

const PAGE_SIZE = 20

function formatCurrency(amount, currency = 'INR') {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
}

export default function Payments() {
  const navigate = useNavigate()
  const [payments, setPayments] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: PAGE_SIZE }
      if (statusFilter) params.status = statusFilter
      const { data } = await paymentsApi.list(params)
      setPayments(data.results || data)
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

  const columns = [
    { key: 'request_number', header: 'Request #', render: (row) => <span className="font-medium text-slate-800">{row.request_number}</span> },
    { key: 'invoice_number', header: 'Invoice' },
    { key: 'vendor_name', header: 'Vendor' },
    { key: 'amount', header: 'Amount', render: (row) => formatCurrency(row.amount, row.currency) },
    { key: 'method', header: 'Method', render: (row) => row.method.replace('_', ' ') },
    { key: 'due_date', header: 'Due Date' },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
  ]

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Payments</h1>

      <div className="flex items-center gap-2 mb-4">
        {['', 'PAYMENT_PENDING', 'PROCESSING', 'PAID', 'FAILED', 'CANCELLED'].map((s) => (
          <button
            key={s || 'ALL'}
            onClick={() => {
              setStatusFilter(s)
              setPage(1)
            }}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              statusFilter === s ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300'
            }`}
          >
            {s ? s.replace('_', ' ') : 'All'}
          </button>
        ))}
      </div>

      <Card padded={false}>
        {loading ? (
          <LoadingState label="Loading payments..." />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : payments.length === 0 ? (
          <EmptyState title="No payment requests" description="Payment requests raised for approved invoices will appear here." />
        ) : (
          <>
            <Table columns={columns} data={payments} onRowClick={(row) => navigate(`/payments/${row.id}`)} />
            <div className="px-4">
              <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
