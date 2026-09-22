import { Download } from 'lucide-react'
import { useEffect, useState } from 'react'
import AgingChart from '../charts/AgingChart'
import StatusBarChart from '../charts/StatusBarChart'
import VendorBarChart from '../charts/VendorBarChart'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import ErrorState from '../components/ui/ErrorState'
import Input from '../components/ui/Input'
import LoadingState from '../components/ui/LoadingState'
import Select from '../components/ui/Select'
import { useToast } from '../context/ToastContext'
import { extractErrorMessage } from '../services/api'
import { reportsApi } from '../services/reports'
import { vendorsApi } from '../services/vendors'

const REPORT_TABS = [
  { key: 'aging', label: 'AP Aging' },
  { key: 'invoices', label: 'Invoice Status' },
  { key: 'exceptions', label: 'Exceptions' },
  { key: 'vendors', label: 'Vendor' },
  { key: 'payments', label: 'Payment' },
  { key: 'gst', label: 'GST / Tax' },
  { key: 'audit', label: 'Audit' },
]

function formatCurrency(amount) {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
}

function SimpleTable({ columns, rows }) {
  if (!rows || rows.length === 0) return <p className="text-sm text-slate-400 py-8 text-center">No data.</p>
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
          {columns.map((c) => (
            <th key={c.key} className="py-2 px-2">
              {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className="border-b border-slate-50 last:border-0">
            {columns.map((c) => (
              <td key={c.key} className="py-2 px-2 text-slate-700">
                {c.render ? c.render(row) : row[c.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function Reports() {
  const toast = useToast()
  const [tab, setTab] = useState('aging')
  const [filters, setFilters] = useState({ date_from: '', date_to: '', vendor: '', status: '' })
  const [vendors, setVendors] = useState([])
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    vendorsApi.list({ page_size: 100 }).then(({ data }) => setVendors(data.results || data)).catch(() => {})
  }, [])

  const activeFilters = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await reportsApi.get(tab, activeFilters)
      setData(data)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, filters])

  const setFilter = (name, value) => setFilters((prev) => ({ ...prev, [name]: value }))

  const handleExport = async () => {
    setExporting(true)
    try {
      await reportsApi.downloadCsv(tab, activeFilters, `${tab}_report.csv`)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold text-slate-800">Reports</h1>
        <Button variant="secondary" icon={Download} onClick={handleExport} loading={exporting}>
          Export CSV
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {REPORT_TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => {
              setLoading(true)
              setData(null)
              setTab(t.key)
            }}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === t.key ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Card className="mb-5">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <Input label="From" type="date" value={filters.date_from} onChange={(e) => setFilter('date_from', e.target.value)} />
          <Input label="To" type="date" value={filters.date_to} onChange={(e) => setFilter('date_to', e.target.value)} />
          <Select
            label="Vendor"
            placeholder="All vendors"
            value={filters.vendor}
            onChange={(e) => setFilter('vendor', e.target.value)}
            options={vendors.map((v) => ({ label: v.name, value: v.id }))}
          />
          <Select
            label="Status"
            placeholder="All statuses"
            value={filters.status}
            onChange={(e) => setFilter('status', e.target.value)}
            options={['UPLOADED', 'PROCESSING', 'EXCEPTION', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'PAYMENT_PENDING', 'PAID'].map(
              (s) => ({ label: s.replace('_', ' '), value: s })
            )}
          />
        </div>
      </Card>

      {loading ? (
        <LoadingState label="Loading report..." />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <div className="space-y-5">
          {tab === 'aging' && data && (
            <>
              <Card title="AP Aging Chart">
                <AgingChart buckets={data.buckets} />
              </Card>
              <Card title="AP Aging Detail" padded={false}>
                <div className="p-4">
                  <SimpleTable
                    columns={[
                      { key: 'label', label: 'Bucket' },
                      { key: 'count', label: 'Invoices' },
                      { key: 'amount', label: 'Amount', render: (r) => formatCurrency(r.amount) },
                      { key: 'percentage', label: '%', render: (r) => `${r.percentage}%` },
                    ]}
                    rows={data.buckets}
                  />
                </div>
              </Card>
            </>
          )}

          {tab === 'invoices' && data && (
            <>
              <Card title="Invoice Status Chart">
                <StatusBarChart data={data} />
              </Card>
              <Card title="Invoice Status Detail" padded={false}>
                <div className="p-4">
                  <SimpleTable
                    columns={[
                      { key: 'status', label: 'Status' },
                      { key: 'count', label: 'Count' },
                      { key: 'amount', label: 'Amount', render: (r) => formatCurrency(r.amount) },
                    ]}
                    rows={data}
                  />
                </div>
              </Card>
            </>
          )}

          {tab === 'exceptions' && data && (
            <div className="grid lg:grid-cols-3 gap-5">
              <Card title={`By Type (${data.total} total)`}>
                <SimpleTable columns={[{ key: 'exception_type', label: 'Type' }, { key: 'count', label: 'Count' }]} rows={data.by_type} />
              </Card>
              <Card title="By Severity">
                <SimpleTable columns={[{ key: 'severity', label: 'Severity' }, { key: 'count', label: 'Count' }]} rows={data.by_severity} />
              </Card>
              <Card title="By Status">
                <SimpleTable columns={[{ key: 'status', label: 'Status' }, { key: 'count', label: 'Count' }]} rows={data.by_status} />
              </Card>
            </div>
          )}

          {tab === 'vendors' && data && (
            <>
              <Card title="Vendor-wise Amount">
                <VendorBarChart data={data.slice(0, 10)} />
              </Card>
              <Card title="Vendor Detail" padded={false}>
                <div className="p-4">
                  <SimpleTable
                    columns={[
                      { key: 'vendor_name', label: 'Vendor' },
                      { key: 'invoice_count', label: 'Invoices' },
                      { key: 'total_amount', label: 'Total Amount', render: (r) => formatCurrency(r.total_amount) },
                    ]}
                    rows={data}
                  />
                </div>
              </Card>
            </>
          )}

          {tab === 'payments' && data && (
            <>
              <Card title="Payment Status Chart">
                <StatusBarChart data={data} />
              </Card>
              <Card title="Payment Status Detail" padded={false}>
                <div className="p-4">
                  <SimpleTable
                    columns={[
                      { key: 'status', label: 'Status' },
                      { key: 'count', label: 'Count' },
                      { key: 'amount', label: 'Amount', render: (r) => formatCurrency(r.amount) },
                    ]}
                    rows={data}
                  />
                </div>
              </Card>
            </>
          )}

          {tab === 'gst' && data && (
            <>
              <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {[
                  ['Taxable Amount', data.summary.total_taxable],
                  ['CGST', data.summary.total_cgst],
                  ['SGST', data.summary.total_sgst],
                  ['IGST', data.summary.total_igst],
                  ['Total Tax', data.summary.total_tax],
                ].map(([label, value]) => (
                  <Card key={label} padded>
                    <p className="text-xs text-slate-500">{label}</p>
                    <p className="text-lg font-semibold text-slate-800 mt-1">{formatCurrency(value)}</p>
                  </Card>
                ))}
              </div>
              <Card title="Tax by Vendor" padded={false}>
                <div className="p-4">
                  <SimpleTable
                    columns={[
                      { key: 'vendor_name', label: 'Vendor' },
                      { key: 'gstin', label: 'GSTIN' },
                      { key: 'taxable', label: 'Taxable', render: (r) => formatCurrency(r.taxable) },
                      { key: 'tax', label: 'Tax', render: (r) => formatCurrency(r.tax) },
                    ]}
                    rows={data.by_vendor}
                  />
                </div>
              </Card>
            </>
          )}

          {tab === 'audit' && data && (
            <Card title="Audit Action Summary" padded={false}>
              <div className="p-4">
                <SimpleTable columns={[{ key: 'action', label: 'Action' }, { key: 'count', label: 'Count' }]} rows={data} />
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
