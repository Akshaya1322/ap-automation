import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import ErrorState from '../components/ui/ErrorState'
import LoadingState from '../components/ui/LoadingState'
import Pagination from '../components/ui/Pagination'
import Table from '../components/ui/Table'
import { extractErrorMessage } from '../services/api'
import { approvalsApi } from '../services/approvals'
import { ROLE_LABELS } from '../utils/navigation'

const PAGE_SIZE = 20

function formatCurrency(amount, currency = 'INR') {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
}

export default function Approvals() {
  const navigate = useNavigate()
  const [steps, setSteps] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('PENDING')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: PAGE_SIZE }
      if (statusFilter) params.status = statusFilter
      const { data } = await approvalsApi.list(params)
      setSteps(data.results || data)
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
    { key: 'invoice_number', header: 'Invoice', render: (row) => <span className="font-medium text-slate-800">{row.invoice_number}</span> },
    { key: 'vendor_name', header: 'Vendor', render: (row) => row.vendor_name || '—' },
    { key: 'amount', header: 'Amount', render: (row) => formatCurrency(row.amount, row.currency) },
    { key: 'role_required', header: 'Approver Role', render: (row) => ROLE_LABELS[row.role_required] || row.role_required },
    { key: 'assigned_user_name', header: 'Assigned To', render: (row) => row.assigned_user_name || 'Unassigned' },
    {
      key: 'is_current_step',
      header: 'Sequence',
      render: (row) =>
        row.is_current_step ? (
          <Badge color="blue">Current step</Badge>
        ) : (
          <span className="text-slate-400 text-xs">Step {row.step_number}</span>
        ),
    },
    { key: 'status', header: 'Status', render: (row) => <Badge color={row.status === 'PENDING' ? 'amber' : 'slate'}>{row.status}</Badge> },
  ]

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Approvals</h1>

      <div className="flex items-center gap-2 mb-4">
        {['PENDING', 'APPROVED', 'REJECTED', 'CHANGES_REQUESTED', ''].map((s) => (
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
          <LoadingState label="Loading approvals..." />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : steps.length === 0 ? (
          <EmptyState title="Nothing to approve" description="You're all caught up." />
        ) : (
          <>
            <Table columns={columns} data={steps} onRowClick={(row) => navigate(`/approvals/${row.id}`)} />
            <div className="px-4">
              <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
