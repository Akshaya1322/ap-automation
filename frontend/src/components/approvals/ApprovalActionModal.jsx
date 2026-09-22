import { useState } from 'react'
import Button from '../ui/Button'
import Modal from '../ui/Modal'

const CONFIG = {
  approve: { title: 'Approve Invoice', variant: 'success', cta: 'Approve', required: false },
  reject: { title: 'Reject Invoice', variant: 'danger', cta: 'Reject', required: true },
  request_changes: { title: 'Request Changes', variant: 'secondary', cta: 'Request Changes', required: true },
}

export default function ApprovalActionModal({ open, action, onClose, onSubmit, submitting }) {
  const [comment, setComment] = useState('')
  if (!action) return null
  const cfg = CONFIG[action]
  const disabled = cfg.required && !comment.trim()

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
          <Button variant={cfg.variant} onClick={() => onSubmit(comment.trim())} loading={submitting} disabled={disabled}>
            {cfg.cta}
          </Button>
        </>
      }
    >
      <label className="block text-sm font-medium text-slate-700 mb-1">
        Comment {cfg.required && <span className="text-red-500">*</span>}
        {!cfg.required && <span className="text-slate-400 font-normal">(optional)</span>}
      </label>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
        placeholder={cfg.required ? 'A reason is required...' : 'Add an optional comment...'}
        autoFocus
      />
    </Modal>
  )
}
