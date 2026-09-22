import { ArrowLeft, Pencil, Power } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import ErrorState from '../components/ui/ErrorState'
import LoadingState from '../components/ui/LoadingState'
import StatusBadge from '../components/ui/StatusBadge'
import Table from '../components/ui/Table'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { extractErrorMessage } from '../services/api'
import { invoicesApi } from '../services/invoices'
import { vendorsApi } from '../services/vendors'

const NEXT_STEP = {
  DRAFT: { action: 'submit', label: 'Submit for Review' },
  SUBMITTED: { action: 'startReview', label: 'Start Review' },
  UNDER_REVIEW: { action: 'approve', label: 'Approve Vendor' },
  APPROVED: { action: 'activate', label: 'Activate Vendor' },
}

function formatCurrency(amount, currency = 'INR') {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
}

export default function VendorDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { user } = useAuth()

  const [vendor, setVendor] = useState(null)
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const canManage = ['ADMIN', 'AP_MANAGER'].includes(user?.role)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [{ data: v }, { data: inv }] = await Promise.all([
        vendorsApi.get(id),
        invoicesApi.list({ vendor: id, page_size: 10 }),
      ])
      setVendor(v)
      setInvoices(inv.results || inv)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const runTransition = async (fn, label) => {
    setActionLoading(true)
    try {
      await fn(id)
      toast.success(label)
      load()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <LoadingState label="Loading vendor..." />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!vendor) return null

  const nextStep = NEXT_STEP[vendor.status]
  const invoiceColumns = [
    { key: 'invoice_number', header: 'Invoice #' },
    { key: 'invoice_date', header: 'Date' },
    { key: 'total_amount', header: 'Amount', render: (row) => formatCurrency(row.total_amount, row.currency) },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
  ]

  return (
    <div>
      <button
        onClick={() => navigate('/vendors')}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-3"
      >
        <ArrowLeft size={15} /> Back to vendors
      </button>

      <div className="flex flex-wrap items-start justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-slate-800">{vendor.name}</h1>
            <StatusBadge status={vendor.status} />
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {vendor.code} &middot; {vendor.category || 'Uncategorized'} &middot; {vendor.city}, {vendor.state}
          </p>
        </div>
        {canManage && (
          <div className="flex gap-2">
            <Button variant="secondary" icon={Pencil} onClick={() => navigate(`/vendors/${id}/edit`)}>
              Edit
            </Button>
            {nextStep && (
              <Button
                onClick={() => runTransition(vendorsApi[nextStep.action], `Vendor moved to next onboarding stage.`)}
                loading={actionLoading}
              >
                {nextStep.label}
              </Button>
            )}
            {vendor.status === 'ACTIVE' && (
              <Button variant="danger" icon={Power} onClick={() => runTransition(vendorsApi.deactivate, 'Vendor deactivated.')} loading={actionLoading}>
                Deactivate
              </Button>
            )}
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-5 mb-5">
        <Card title="Total Invoices" padded>
          <p className="text-2xl font-semibold text-slate-800">{vendor.total_invoices}</p>
        </Card>
        <Card title="Total Payable" padded>
          <p className="text-2xl font-semibold text-amber-600">{formatCurrency(vendor.total_payable)}</p>
        </Card>
        <Card title="Total Paid" padded>
          <p className="text-2xl font-semibold text-emerald-600">{formatCurrency(vendor.total_paid)}</p>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Company & Tax Details">
          <dl className="space-y-2 text-sm">
            {[
              ['GSTIN', vendor.gstin || '—'],
              ['PAN', vendor.pan || '—'],
              ['Payment Terms', `Net ${vendor.payment_terms_days} days`],
              ['Address', [vendor.address_line1, vendor.address_line2, vendor.city, vendor.state, vendor.pincode].filter(Boolean).join(', ') || '—'],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between gap-4">
                <dt className="text-slate-500 shrink-0">{label}</dt>
                <dd className="text-slate-700 font-medium text-right">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>

        <Card title="Contact Details">
          <dl className="space-y-2 text-sm">
            {[
              ['Contact Person', vendor.contact_person || '—'],
              ['Email', vendor.email || '—'],
              ['Phone', vendor.phone || '—'],
              ['Department', vendor.department || '—'],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between">
                <dt className="text-slate-500">{label}</dt>
                <dd className="text-slate-700 font-medium">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </div>

      <Card title="Bank Details" className="mt-5">
        {vendor.bank_details ? (
          <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Account Holder</span>
              <span className="text-slate-700 font-medium">{vendor.bank_details.account_holder_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Account Number</span>
              <span className="text-slate-700 font-medium font-mono">{vendor.bank_details.masked_account_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Bank</span>
              <span className="text-slate-700 font-medium">{vendor.bank_details.bank_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">IFSC</span>
              <span className="text-slate-700 font-medium">{vendor.bank_details.ifsc_code}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Verified</span>
              <Badge color={vendor.bank_details.is_verified ? 'green' : 'amber'}>
                {vendor.bank_details.is_verified ? 'Verified' : 'Unverified'}
              </Badge>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">No bank details on file.</p>
        )}
      </Card>

      <Card title="Invoice History" className="mt-5" padded={false}>
        {invoices.length === 0 ? (
          <p className="text-sm text-slate-400 p-5">No invoices from this vendor yet.</p>
        ) : (
          <Table columns={invoiceColumns} data={invoices} onRowClick={(row) => navigate(`/invoices/${row.id}`)} />
        )}
      </Card>
    </div>
  )
}
