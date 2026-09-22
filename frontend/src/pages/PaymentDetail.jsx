import { ArrowLeft, Ban, CreditCard, Download } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import ErrorState from '../components/ui/ErrorState'
import LoadingState from '../components/ui/LoadingState'
import StatusBadge from '../components/ui/StatusBadge'
import { useToast } from '../context/ToastContext'
import { extractErrorMessage } from '../services/api'
import { paymentsApi } from '../services/payments'

function formatCurrency(amount, currency = 'INR') {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
}

export default function PaymentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [pr, setPr] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [processing, setProcessing] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await paymentsApi.get(id)
      setPr(data)
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

  const handleProcess = async () => {
    setProcessing(true)
    try {
      const { data } = await paymentsApi.process(id)
      setPr(data)
      toast[data.status === 'PAID' ? 'success' : 'error'](
        data.status === 'PAID' ? 'Payment processed successfully (simulated).' : 'Simulated payment failed. You can retry.'
      )
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setProcessing(false)
    }
  }

  const handleCancel = async () => {
    setProcessing(true)
    try {
      const { data } = await paymentsApi.cancel(id)
      setPr(data)
      toast.success('Payment request cancelled.')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setProcessing(false)
    }
  }

  if (loading) return <LoadingState label="Loading payment..." />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!pr) return null

  return (
    <div className="max-w-2xl">
      <button
        onClick={() => navigate('/payments')}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-3"
      >
        <ArrowLeft size={15} /> Back to payments
      </button>

      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-slate-800">{pr.request_number}</h1>
            <StatusBadge status={pr.status} />
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {pr.vendor_name} &middot; Invoice {pr.invoice_number}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-400">Amount</p>
          <p className="text-2xl font-semibold text-slate-800">{formatCurrency(pr.amount, pr.currency)}</p>
        </div>
      </div>

      {(pr.status === 'PAYMENT_PENDING' || pr.status === 'FAILED') && (
        <div className="flex gap-2 mb-5">
          <Button icon={CreditCard} onClick={handleProcess} loading={processing}>
            {pr.status === 'FAILED' ? 'Retry Payment' : 'Process Payment'}
          </Button>
          {pr.status === 'PAYMENT_PENDING' && (
            <Button variant="secondary" icon={Ban} onClick={handleCancel} loading={processing}>
              Cancel Request
            </Button>
          )}
        </div>
      )}

      <Card title="Payment Request Details">
        <dl className="space-y-2 text-sm">
          {[
            ['Method', pr.method.replace('_', ' ')],
            ['Requested Date', pr.requested_date],
            ['Due Date', pr.due_date || '—'],
            ['Requested By', pr.requested_by_name || '—'],
          ].map(([label, value]) => (
            <div key={label} className="flex justify-between">
              <dt className="text-slate-500">{label}</dt>
              <dd className="text-slate-700 font-medium">{value}</dd>
            </div>
          ))}
        </dl>
        <Button variant="ghost" size="sm" className="mt-3 px-0" onClick={() => navigate(`/invoices/${pr.invoice}`)}>
          View invoice &rarr;
        </Button>
      </Card>

      {pr.payment && (
        <Card title="Payment Result" className="mt-5">
          <div className="flex items-center gap-2 mb-3">
            <StatusBadge status={pr.payment.status} />
            <Badge color="slate">Simulated</Badge>
          </div>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Transaction Reference</dt>
              <dd className="text-slate-700 font-medium font-mono">{pr.payment.transaction_ref}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Payment Date</dt>
              <dd className="text-slate-700 font-medium">{pr.payment.payment_date ? new Date(pr.payment.payment_date).toLocaleString() : '—'}</dd>
            </div>
          </dl>
          {pr.payment.bank_response?.message && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-md px-3 py-2 mt-3">
              {pr.payment.bank_response.message}
            </p>
          )}
          {pr.payment.advice_file_url && (
            <a
              href={pr.payment.advice_file_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-blue-600 font-medium hover:underline mt-3"
            >
              <Download size={15} /> Download Payment Advice
            </a>
          )}
        </Card>
      )}
    </div>
  )
}
