import { useState } from 'react'
import Button from '../ui/Button'
import Modal from '../ui/Modal'

const CONFIG = {
  resolve: { title: 'Resolve Exception', variant: 'success', cta: 'Resolve' },
  reject: { title: 'Reject Exception', variant: 'danger', cta: 'Reject' },
  override: { title: 'Override Exception', variant: 'secondary', cta: 'Override & Proceed' },
}

export default function ExceptionActionModal({ open, action, exception, onClose, onSubmit, submitting }) {
  const [comment, setComment] = useState('')
  if (!action) return null
  const cfg = CONFIG[action]

  const handleSubmit = () => {
    if (!comment.trim()) return
    onSubmit(comment.trim())
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={cfg.title}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button variant={cfg.variant} onClick={handleSubmit} loading={submitting} disabled={!comment.trim()}>
            {cfg.cta}
          </Button>
        </>
      }
    >
      <p className="text-sm text-slate-600 mb-3">
        {exception?.exception_type_display} on invoice <span className="font-medium">{exception?.invoice_number}</span>
      </p>
      <p className="text-xs text-slate-400 mb-3">{exception?.description}</p>
      <label className="block text-sm font-medium text-slate-700 mb-1">
        Comment <span className="text-red-500">*</span>
      </label>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
        placeholder="Explain why this exception is being resolved/rejected/overridden..."
        autoFocus
      />
    </Modal>
  )
}
