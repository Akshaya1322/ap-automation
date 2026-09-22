import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import ErrorState from '../components/ui/ErrorState'
import Input from '../components/ui/Input'
import LoadingState from '../components/ui/LoadingState'
import Pagination from '../components/ui/Pagination'
import StatusBadge from '../components/ui/StatusBadge'
import Table from '../components/ui/Table'
import { extractErrorMessage } from '../services/api'
import { vendorsApi } from '../services/vendors'

const PAGE_SIZE = 20

function formatCurrency(amount) {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
}

export default function Vendors() {
  const navigate = useNavigate()
  const [vendors, setVendors] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: PAGE_SIZE }
      if (search) params.search = search
      const { data } = await vendorsApi.list(params)
      setVendors(data.results || data)
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
  }, [page, search])

  const columns = [
    { key: 'name', header: 'Vendor', render: (row) => <span className="font-medium text-slate-800">{row.name}</span> },
    { key: 'code', header: 'Code' },
    { key: 'gstin', header: 'GSTIN', render: (row) => row.gstin || '—' },
    { key: 'email', header: 'Email', render: (row) => row.email || '—' },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    { key: 'total_invoices', header: 'Invoices' },
    { key: 'total_payable', header: 'Payable', render: (row) => formatCurrency(row.total_payable) },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold text-slate-800">Vendors</h1>
        <Button icon={Plus} onClick={() => navigate('/vendors/new')}>
          New Vendor
        </Button>
      </div>

      <div className="mb-4 max-w-sm">
        <Input placeholder="Search name, code, GSTIN, email" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <Card padded={false}>
        {loading ? (
          <LoadingState label="Loading vendors..." />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : vendors.length === 0 ? (
          <EmptyState title="No vendors found" actionLabel="Add Vendor" onAction={() => navigate('/vendors/new')} />
        ) : (
          <>
            <Table columns={columns} data={vendors} onRowClick={(row) => navigate(`/vendors/${row.id}`)} />
            <div className="px-4">
              <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
