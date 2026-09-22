import { useEffect, useState } from 'react'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import ErrorState from '../components/ui/ErrorState'
import Input from '../components/ui/Input'
import LoadingState from '../components/ui/LoadingState'
import Pagination from '../components/ui/Pagination'
import Select from '../components/ui/Select'
import Table from '../components/ui/Table'
import { extractErrorMessage } from '../services/api'
import { auditLogsApi } from '../services/auditLogs'

const PAGE_SIZE = 25

const ACTIONS = [
  'LOGIN', 'LOGOUT', 'UPLOAD', 'OCR_PROCESS', 'FIELD_EDIT', 'VALIDATE',
  'EXCEPTION_CREATE', 'EXCEPTION_RESOLVE', 'PO_MATCH', 'APPROVAL', 'REJECTION',
  'REQUEST_CHANGES', 'VENDOR_CREATE', 'VENDOR_UPDATE', 'PAYMENT_REQUEST',
  'PAYMENT_STATUS_CHANGE', 'CREATE', 'UPDATE', 'DELETE',
]
const ENTITY_TYPES = ['Invoice', 'InvoiceException', 'InvoiceExtractedField', 'Vendor', 'ApprovalWorkflow', 'ApprovalStep', 'PaymentRequest', 'User']

const ACTION_COLOR = {
  LOGIN: 'blue', LOGOUT: 'slate', UPLOAD: 'blue', OCR_PROCESS: 'blue', VALIDATE: 'blue', PO_MATCH: 'blue',
  FIELD_EDIT: 'amber', EXCEPTION_CREATE: 'orange', EXCEPTION_RESOLVE: 'green', APPROVAL: 'green',
  REJECTION: 'red', REQUEST_CHANGES: 'amber', VENDOR_CREATE: 'blue', VENDOR_UPDATE: 'amber',
  PAYMENT_REQUEST: 'blue', PAYMENT_STATUS_CHANGE: 'green', CREATE: 'blue', UPDATE: 'amber', DELETE: 'red',
}

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({ action: '', entity_type: '', date_from: '', date_to: '', search: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: PAGE_SIZE, ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }
      const { data } = await auditLogsApi.list(params)
      setLogs(data.results || data)
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
  }, [page, filters])

  const setFilter = (name, value) => {
    setFilters((prev) => ({ ...prev, [name]: value }))
    setPage(1)
  }

  const columns = [
    { key: 'created_at', header: 'Timestamp', render: (row) => new Date(row.created_at).toLocaleString() },
    { key: 'user_name', header: 'User', render: (row) => row.user_name || 'System' },
    { key: 'action', header: 'Action', render: (row) => <Badge color={ACTION_COLOR[row.action] || 'slate'}>{row.action_display}</Badge> },
    { key: 'entity_type', header: 'Entity', render: (row) => row.entity_type },
    { key: 'entity_id', header: 'Entity ID', render: (row) => <span className="font-mono text-xs">{row.entity_id?.slice(0, 8)}</span> },
    { key: 'description', header: 'Description' },
    { key: 'ip_address', header: 'IP', render: (row) => row.ip_address || '—' },
  ]

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Audit Logs</h1>

      <Card className="mb-5">
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <Select
            label="Action"
            placeholder="All actions"
            value={filters.action}
            onChange={(e) => setFilter('action', e.target.value)}
            options={ACTIONS.map((a) => ({ label: a.replace(/_/g, ' '), value: a }))}
          />
          <Select
            label="Entity Type"
            placeholder="All entities"
            value={filters.entity_type}
            onChange={(e) => setFilter('entity_type', e.target.value)}
            options={ENTITY_TYPES.map((e) => ({ label: e, value: e }))}
          />
          <Input label="From" type="date" value={filters.date_from} onChange={(e) => setFilter('date_from', e.target.value)} />
          <Input label="To" type="date" value={filters.date_to} onChange={(e) => setFilter('date_to', e.target.value)} />
          <Input label="Search" placeholder="Description, user..." value={filters.search} onChange={(e) => setFilter('search', e.target.value)} />
        </div>
      </Card>

      <Card padded={false}>
        {loading ? (
          <LoadingState label="Loading audit logs..." />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : logs.length === 0 ? (
          <EmptyState title="No audit log entries" description="Try adjusting your filters." />
        ) : (
          <>
            <Table columns={columns} data={logs} />
            <div className="px-4">
              <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
