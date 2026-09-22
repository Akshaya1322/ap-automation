import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  Gauge,
  IndianRupee,
  TimerReset,
  Wallet,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import AgingChart from '../charts/AgingChart'
import StatusBarChart from '../charts/StatusBarChart'
import TrendLineChart from '../charts/TrendLineChart'
import VendorBarChart from '../charts/VendorBarChart'
import Card from '../components/ui/Card'
import ErrorState from '../components/ui/ErrorState'
import Input from '../components/ui/Input'
import KpiCard from '../components/ui/KpiCard'
import LoadingState from '../components/ui/LoadingState'
import Select from '../components/ui/Select'
import { extractErrorMessage } from '../services/api'
import { dashboardApi } from '../services/dashboard'
import { vendorsApi } from '../services/vendors'

const DEPARTMENTS = ['Finance', 'Operations', 'IT', 'Marketing', 'HR', 'Procurement']
const STATUSES = [
  'UPLOADED', 'PROCESSING', 'EXTRACTED', 'VALIDATED', 'EXCEPTION',
  'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'PAYMENT_PENDING', 'PAID',
]

function formatCurrency(amount) {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
}

export default function Dashboard() {
  const [filters, setFilters] = useState({ date_from: '', date_to: '', vendor: '', status: '', department: '' })
  const [vendors, setVendors] = useState([])
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    vendorsApi.list({ page_size: 100 }).then(({ data }) => setVendors(data.results || data)).catch(() => {})
  }, [])

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
      const { data } = await dashboardApi.get(params)
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
  }, [filters])

  const setFilter = (name, value) => setFilters((prev) => ({ ...prev, [name]: value }))

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Dashboard</h1>

      <Card className="mb-5">
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
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
            options={STATUSES.map((s) => ({ label: s.replace('_', ' '), value: s }))}
          />
          <Select
            label="Department"
            placeholder="All departments"
            value={filters.department}
            onChange={(e) => setFilter('department', e.target.value)}
            options={DEPARTMENTS.map((d) => ({ label: d, value: d }))}
          />
        </div>
      </Card>

      {loading ? (
        <LoadingState label="Loading dashboard..." />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
            <KpiCard label="Total Invoices" value={data.kpis.total_invoices} icon={FileText} tone="blue" />
            <KpiCard label="Pending Approvals" value={data.kpis.pending_approvals} icon={Clock} tone="amber" />
            <KpiCard label="Exceptions" value={data.kpis.exceptions} icon={AlertTriangle} tone="orange" />
            <KpiCard label="Approved Invoices" value={data.kpis.approved_invoices} icon={CheckCircle2} tone="green" />
            <KpiCard label="Total Payable" value={formatCurrency(data.kpis.total_payable_amount)} icon={Wallet} tone="blue" />
            <KpiCard label="Overdue Amount" value={formatCurrency(data.kpis.overdue_amount)} icon={IndianRupee} tone="red" />
            <KpiCard label="OCR Accuracy" value={`${data.kpis.ocr_accuracy}%`} icon={Gauge} tone="green" hint="Avg. confidence across processed invoices" />
            <KpiCard label="Avg. Processing Time" value={`${data.kpis.avg_processing_time_hours}h`} icon={TimerReset} tone="blue" />
          </div>

          <div className="grid lg:grid-cols-2 gap-5 mb-5">
            <Card title="Invoice Processing Trend (30 days)">
              <TrendLineChart data={data.charts.processing_trend} />
            </Card>
            <Card title="Invoice Status Distribution">
              <StatusBarChart data={data.charts.status_distribution} />
            </Card>
          </div>

          <div className="grid lg:grid-cols-2 gap-5 mb-5">
            <Card title="AP Aging">
              <AgingChart buckets={data.charts.ap_aging.buckets} />
            </Card>
            <Card title="Vendor-wise Invoice Amount">
              <VendorBarChart data={data.charts.vendor_wise_amount} />
            </Card>
          </div>

          <div className="grid lg:grid-cols-2 gap-5">
            <Card title="Payment Status">
              <StatusBarChart data={data.charts.payment_status} />
            </Card>
            <Card title="Monthly Invoice Volume">
              <TrendLineChart data={data.charts.monthly_volume} xKey="month" />
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
