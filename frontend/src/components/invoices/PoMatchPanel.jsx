import { Check, RefreshCw, X } from 'lucide-react'
import Badge from '../ui/Badge'
import Button from '../ui/Button'

const STATUS_CONFIG = {
  MATCHED: { color: 'green', label: 'Matched' },
  PARTIAL_MATCH: { color: 'amber', label: 'Partial Match' },
  MISMATCH: { color: 'red', label: 'Mismatch' },
  NOT_LINKED: { color: 'slate', label: 'Not Linked' },
}

function MatchIcon({ ok }) {
  return ok ? <Check size={14} className="text-emerald-600" /> : <X size={14} className="text-red-500" />
}

export default function PoMatchPanel({ result, onRun, running, poNumber, initialStatus }) {
  const status = result?.status || initialStatus || (poNumber ? null : 'NOT_LINKED')
  const cfg = STATUS_CONFIG[status] || null

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <p className="text-sm text-slate-500">
            {poNumber ? (
              <>
                Linked to PO <span className="font-medium text-slate-700">{poNumber}</span>
              </>
            ) : (
              'No purchase order linked yet.'
            )}
          </p>
          {cfg && <Badge color={cfg.color}>{cfg.label}</Badge>}
        </div>
        <Button size="sm" variant="secondary" icon={RefreshCw} onClick={onRun} loading={running}>
          Run PO Match
        </Button>
      </div>

      {result && result.status !== 'NOT_LINKED' && (
        <div className="space-y-5">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Header Comparison</p>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400 border-b border-slate-100">
                  <th className="py-1.5">Field</th>
                  <th className="py-1.5">PO</th>
                  <th className="py-1.5">Invoice</th>
                  <th className="py-1.5 text-center">Match</th>
                </tr>
              </thead>
              <tbody>
                {result.header_comparison.map((c) => (
                  <tr key={c.field} className="border-b border-slate-50 last:border-0">
                    <td className="py-1.5 text-slate-600">{c.field}</td>
                    <td className="py-1.5 text-slate-700">{c.po_value ?? '—'}</td>
                    <td className={`py-1.5 ${c.match ? 'text-slate-700' : 'text-red-600 font-medium'}`}>{c.invoice_value ?? '—'}</td>
                    <td className="py-1.5 text-center">
                      <MatchIcon ok={c.match} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Line Item Comparison {result.grn ? '(3-way: PO / GRN / Invoice)' : '(2-way: PO / Invoice)'}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-400 border-b border-slate-100">
                    <th className="py-1.5">#</th>
                    <th className="py-1.5">Description</th>
                    <th className="py-1.5 text-right">PO Qty</th>
                    {result.grn && <th className="py-1.5 text-right">GRN Qty</th>}
                    <th className="py-1.5 text-right">Invoice Qty</th>
                    <th className="py-1.5 text-right">PO Price</th>
                    <th className="py-1.5 text-right">Invoice Price</th>
                    <th className="py-1.5 text-center">Match</th>
                  </tr>
                </thead>
                <tbody>
                  {result.line_comparison.map((line) => {
                    const ok = line.quantity_match && line.price_match && !line.over_billed_vs_grn
                    return (
                      <tr key={line.line_no} className="border-b border-slate-50 last:border-0">
                        <td className="py-1.5 text-slate-500">{line.line_no}</td>
                        <td className="py-1.5 text-slate-700">{line.description || '—'}</td>
                        <td className="py-1.5 text-right text-slate-700">{line.po_quantity ?? '—'}</td>
                        {result.grn && (
                          <td className="py-1.5 text-right text-slate-700">{line.grn_quantity_received ?? '—'}</td>
                        )}
                        <td className={`py-1.5 text-right ${line.quantity_match ? 'text-slate-700' : 'text-red-600 font-medium'}`}>
                          {line.invoice_quantity ?? '—'}
                        </td>
                        <td className="py-1.5 text-right text-slate-700">{line.po_unit_price ?? '—'}</td>
                        <td className={`py-1.5 text-right ${line.price_match ? 'text-slate-700' : 'text-red-600 font-medium'}`}>
                          {line.invoice_unit_price ?? '—'}
                        </td>
                        <td className="py-1.5 text-center">
                          <MatchIcon ok={ok} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            {result.line_comparison.some((l) => l.over_billed_vs_grn) && (
              <p className="text-xs text-red-600 mt-2">
                One or more lines bill more quantity than was received per the GRN.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
