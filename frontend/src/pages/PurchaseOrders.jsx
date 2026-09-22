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
import { purchaseOrdersApi } from '../services/purchaseOrders'

const PAGE_SIZE = 20

function formatCurrency(amount, currency = 'INR') {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
}

export default function PurchaseOrders() {
  const navigate = useNavigate()
  const [pos, setPos] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await purchaseOrdersApi.list({ page, page_size: PAGE_SIZE })
      setPos(data.results || data)
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
  }, [page])

  const columns = [
    { key: 'po_number', header: 'PO Number', render: (row) => <span className="font-medium text-slate-800">{row.po_number}</span> },
    { key: 'vendor_name', header: 'Vendor' },
    { key: 'order_date', header: 'Order Date' },
    { key: 'department', header: 'Department', render: (row) => row.department || '—' },
    { key: 'total_amount', header: 'Total', render: (row) => formatCurrency(row.total_amount, row.currency) },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    { key: 'invoice_count', header: 'Invoices', render: (row) => row.invoice_count },
  ]

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Purchase Orders</h1>
      <Card padded={false}>
        {loading ? (
          <LoadingState label="Loading purchase orders..." />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : pos.length === 0 ? (
          <EmptyState title="No purchase orders" description="Purchase orders created in the system will appear here." />
        ) : (
          <>
            <Table columns={columns} data={pos} onRowClick={(row) => navigate(`/purchase-orders/${row.id}`)} />
            <div className="px-4">
              <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
