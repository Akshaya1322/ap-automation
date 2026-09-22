import { ArrowLeft } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Card from '../components/ui/Card'
import ErrorState from '../components/ui/ErrorState'
import LoadingState from '../components/ui/LoadingState'
import StatusBadge from '../components/ui/StatusBadge'
import { extractErrorMessage } from '../services/api'
import { purchaseOrdersApi } from '../services/purchaseOrders'

function formatCurrency(amount, currency = 'INR') {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
}

export default function PurchaseOrderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [po, setPo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await purchaseOrdersApi.get(id)
      setPo(data)
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

  if (loading) return <LoadingState label="Loading purchase order..." />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!po) return null

  return (
    <div>
      <button
        onClick={() => navigate('/purchase-orders')}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-3"
      >
        <ArrowLeft size={15} /> Back to purchase orders
      </button>

      <div className="flex items-center gap-2 mb-1">
        <h1 className="text-xl font-semibold text-slate-800">{po.po_number}</h1>
        <StatusBadge status={po.status} />
      </div>
      <p className="text-sm text-slate-500 mb-5">
        {po.vendor_name} &middot; {po.order_date} &middot; {po.department || 'No department'}
      </p>

      <Card title="Line Items">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
              <th className="py-2">#</th>
              <th className="py-2">Description</th>
              <th className="py-2 text-right">Qty</th>
              <th className="py-2 text-right">Unit Price</th>
              <th className="py-2 text-right">Tax</th>
              <th className="py-2 text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {po.line_items.map((li) => (
              <tr key={li.id} className="border-b border-slate-50 last:border-0">
                <td className="py-2 text-slate-500">{li.line_no}</td>
                <td className="py-2 text-slate-700">{li.description}</td>
                <td className="py-2 text-right text-slate-700">{li.quantity}</td>
                <td className="py-2 text-right text-slate-700">{formatCurrency(li.unit_price, po.currency)}</td>
                <td className="py-2 text-right text-slate-700">{formatCurrency(li.tax_amount, po.currency)}</td>
                <td className="py-2 text-right font-medium text-slate-800">{formatCurrency(li.amount, po.currency)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={5} className="pt-3 text-right text-slate-500">
                Subtotal
              </td>
              <td className="pt-3 text-right font-medium">{formatCurrency(po.subtotal, po.currency)}</td>
            </tr>
            <tr>
              <td colSpan={5} className="text-right text-slate-500">
                Tax
              </td>
              <td className="text-right font-medium">{formatCurrency(po.tax_amount, po.currency)}</td>
            </tr>
            <tr>
              <td colSpan={5} className="text-right text-slate-800 font-semibold">
                Total
              </td>
              <td className="text-right text-slate-800 font-semibold">{formatCurrency(po.total_amount, po.currency)}</td>
            </tr>
          </tfoot>
        </table>
      </Card>

      {po.goods_receipts?.length > 0 && (
        <Card title="Goods Receipts (GRN)" className="mt-5">
          <div className="space-y-4">
            {po.goods_receipts.map((grn) => (
              <div key={grn.id} className="border border-slate-200 rounded-md p-3">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-slate-700">{grn.grn_number}</p>
                  <StatusBadge status={grn.status} />
                </div>
                <p className="text-xs text-slate-400 mb-2">
                  Received {grn.received_date} by {grn.received_by_name || 'Unknown'}
                </p>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-slate-500 border-b border-slate-100">
                      <th className="py-1">Description</th>
                      <th className="py-1 text-right">Qty Received</th>
                    </tr>
                  </thead>
                  <tbody>
                    {grn.line_items.map((li) => (
                      <tr key={li.id}>
                        <td className="py-1 text-slate-600">{li.description}</td>
                        <td className="py-1 text-right text-slate-600">{li.quantity_received}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
