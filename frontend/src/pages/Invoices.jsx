import { Upload } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import ErrorState from '../components/ui/ErrorState'
import Input from '../components/ui/Input'
import LoadingState from '../components/ui/LoadingState'
import Pagination from '../components/ui/Pagination'
import Select from '../components/ui/Select'
import StatusBadge from '../components/ui/StatusBadge'
import Table from '../components/ui/Table'
import ConfidenceBadge from '../components/invoices/ConfidenceBadge'
import ExceptionCenter from '../components/invoices/ExceptionCenter'
import { extractErrorMessage } from '../services/api'
import { invoicesApi } from '../services/invoices'
import { INVOICE_TABS } from '../utils/navigation'

const PAGE_SIZE = 20

function formatCurrency(amount, currency = 'INR') {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
}

export default function Invoices() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const [invoices, setInvoices] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const activeTab = searchParams.get('status') || ''
  const search = searchParams.get('search') || ''
  const [searchInput, setSearchInput] = useState(search)

  const isExceptionTab = activeTab === 'EXCEPTION'

  const load = async () => {
    if (isExceptionTab) return
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: PAGE_SIZE }
      if (activeTab) params.status = activeTab
      if (search) params.search = search
      const { data } = await invoicesApi.list(params)
      setInvoices(data.results || data)
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
  }, [page, activeTab, search])

  useEffect(() => setPage(1), [activeTab, search])

  const setTab = (value) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set('status', value)
    else next.delete('status')
    setSearchParams(next)
  }

  const submitSearch = (e) => {
    e.preventDefault()
    const next = new URLSearchParams(searchParams)
    if (searchInput) next.set('search', searchInput)
    else next.delete('search')
    setSearchParams(next)
  }

  const columns = [
    {
      key: 'invoice_number',
      header: 'Invoice #',
      render: (row) => <span className="font-medium text-slate-800">{row.invoice_number || '—'}</span>,
    },
    { key: 'vendor_name', header: 'Vendor', render: (row) => row.vendor_name || <span className="text-slate-400">Unresolved</span> },
    { key: 'invoice_date', header: 'Invoice Date', render: (row) => row.invoice_date || '—' },
    { key: 'due_date', header: 'Due Date', render: (row) => row.due_date || '—' },
    {
      key: 'total_amount',
      header: 'Amount',
      render: (row) => formatCurrency(row.total_amount, row.currency),
    },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'ocr_confidence_level',
      header: 'OCR',
      render: (row) => <ConfidenceBadge level={row.ocr_confidence_level} />,
    },
    {
      key: 'open_exception_count',
      header: 'Exceptions',
      render: (row) =>
        row.open_exception_count > 0 ? (
          <span className="text-orange-600 font-medium">{row.open_exception_count}</span>
        ) : (
          <span className="text-slate-300">0</span>
        ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold text-slate-800">Invoices</h1>
        <Button icon={Upload} onClick={() => navigate('/invoices/upload')}>
          Upload Invoice
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        {INVOICE_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setTab(tab.value)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.value ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
        <form onSubmit={submitSearch} className="ml-auto w-full sm:w-64">
          <Input
            placeholder="Search invoice #, vendor, PO, GSTIN"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </form>
      </div>

      {isExceptionTab ? (
        <Card>
          <ExceptionCenter />
        </Card>
      ) : (
        <Card padded={false}>
          {loading ? (
            <LoadingState label="Loading invoices..." />
          ) : error ? (
            <ErrorState message={error} onRetry={load} />
          ) : invoices.length === 0 ? (
            <EmptyState
              title="No invoices found"
              description="Try adjusting your filters, or upload a new invoice to get started."
              actionLabel="Upload Invoice"
              onAction={() => navigate('/invoices/upload')}
            />
          ) : (
            <>
              <Table columns={columns} data={invoices} onRowClick={(row) => navigate(`/invoices/${row.id}`)} />
              <div className="px-4">
                <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
              </div>
            </>
          )}
        </Card>
      )}
    </div>
  )
}
