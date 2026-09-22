import { AlertTriangle, ArrowLeft, Check, MessageSquare, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ApprovalActionModal from '../components/approvals/ApprovalActionModal'
import ApprovalTimeline from '../components/approvals/ApprovalTimeline'
import ConfidenceBadge from '../components/invoices/ConfidenceBadge'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import ErrorState from '../components/ui/ErrorState'
import LoadingState from '../components/ui/LoadingState'
import StatusBadge from '../components/ui/StatusBadge'
import { useToast } from '../context/ToastContext'
import { extractErrorMessage } from '../services/api'
import { approvalsApi } from '../services/approvals'

function formatCurrency(amount, currency = 'INR') {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
}

export default function ApprovalDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [step, setStep] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalAction, setModalAction] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await approvalsApi.get(id)
      setStep(data)
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

  const handleSubmit = async (comment) => {
    setSubmitting(true)
    try {
      const fn = { approve: approvalsApi.approve, reject: approvalsApi.reject, request_changes: approvalsApi.requestChanges }[
        modalAction
      ]
      await fn(id, comment)
      toast.success(`Invoice ${modalAction.replace('_', ' ')}d.`)
      setModalAction(null)
      load()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingState label="Loading approval..." />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!step) return null

  const invoice = step.invoice
  const canAct = step.is_current_step && step.status === 'PENDING'
  const openExceptions = invoice.exceptions?.filter((e) => e.status === 'OPEN') || []

  return (
    <div>
      <button
        onClick={() => navigate('/approvals')}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-3"
      >
        <ArrowLeft size={15} /> Back to approvals
      </button>

      <div className="flex flex-wrap items-start justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-slate-800">{invoice.invoice_number}</h1>
            <StatusBadge status={invoice.status} />
            <ConfidenceBadge level={invoice.ocr_confidence_level} score={invoice.ocr_confidence} />
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {invoice.vendor_name || invoice.vendor_name_raw} &middot; PO {invoice.po_number || invoice.po_number_raw || 'Not linked'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-400">Amount</p>
          <p className="text-2xl font-semibold text-slate-800">{formatCurrency(invoice.total_amount, invoice.currency)}</p>
        </div>
      </div>

      {canAct && (
        <div className="flex gap-2 mb-5">
          <Button variant="success" icon={Check} onClick={() => setModalAction('approve')}>
            Approve
          </Button>
          <Button variant="danger" icon={X} onClick={() => setModalAction('reject')}>
            Reject
          </Button>
          <Button variant="secondary" icon={MessageSquare} onClick={() => setModalAction('request_changes')}>
            Request Changes
          </Button>
        </div>
      )}
      {!canAct && step.status === 'PENDING' && (
        <p className="text-sm text-amber-600 bg-amber-50 border border-amber-100 rounded-md px-3 py-2 mb-5">
          This step isn't active yet, or isn't assigned to you.
        </p>
      )}

      {openExceptions.length > 0 && (
        <div className="mb-5 rounded-md border border-orange-200 bg-orange-50 px-4 py-3">
          <p className="text-sm font-medium text-orange-800 flex items-center gap-1.5">
            <AlertTriangle size={15} /> {openExceptions.length} open exception{openExceptions.length > 1 ? 's' : ''}
          </p>
          <ul className="mt-1.5 space-y-1">
            {openExceptions.map((exc) => (
              <li key={exc.id} className="text-xs text-orange-700">
                <Badge color="orange">{exc.severity}</Badge> {exc.exception_type_display}: {exc.description}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Invoice Summary">
          <dl className="space-y-2 text-sm">
            {[
              ['Vendor', invoice.vendor_name || invoice.vendor_name_raw || '—'],
              ['GSTIN', invoice.gstin || '—'],
              ['Invoice Date', invoice.invoice_date || '—'],
              ['Due Date', invoice.due_date || '—'],
              ['PO Number', invoice.po_number || invoice.po_number_raw || 'Not linked'],
              ['PO Match Status', invoice.po_match_status || 'Not run'],
              ['Department', invoice.department || '—'],
              ['OCR Confidence', invoice.ocr_confidence != null ? `${invoice.ocr_confidence}% (${invoice.ocr_confidence_level})` : '—'],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between">
                <dt className="text-slate-500">{label}</dt>
                <dd className="text-slate-700 font-medium">{value}</dd>
              </div>
            ))}
          </dl>
          <Button
            variant="ghost"
            size="sm"
            className="mt-3 px-0"
            onClick={() => navigate(`/invoices/${invoice.id}`)}
          >
            View full invoice &rarr;
          </Button>
        </Card>

        <Card title="Approval Timeline">
          <ApprovalTimeline steps={step.all_steps} />
        </Card>
      </div>

      <ApprovalActionModal
        open={!!modalAction}
        action={modalAction}
        onClose={() => setModalAction(null)}
        onSubmit={handleSubmit}
        submitting={submitting}
      />
    </div>
  )
}
