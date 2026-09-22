import Badge from './Badge'

const STATUS_MAP = {
  UPLOADED: 'slate',
  PROCESSING: 'blue',
  EXTRACTED: 'blue',
  VALIDATED: 'blue',
  EXCEPTION: 'orange',
  PENDING_APPROVAL: 'amber',
  PENDING: 'amber',
  APPROVED: 'green',
  REJECTED: 'red',
  PAYMENT_PENDING: 'amber',
  PROCESSING_PAYMENT: 'blue',
  PAID: 'green',
  FAILED: 'red',
  CANCELLED: 'slate',
  DRAFT: 'slate',
  SUBMITTED: 'blue',
  UNDER_REVIEW: 'amber',
  ACTIVE: 'green',
  INACTIVE: 'slate',
  MATCHED: 'green',
  PARTIAL_MATCH: 'amber',
  MISMATCH: 'red',
  OPEN: 'amber',
  RESOLVED: 'green',
  OVERRIDDEN: 'purple',
  LOW: 'blue',
  MEDIUM: 'amber',
  HIGH: 'orange',
  CRITICAL: 'red',
}

function humanize(status) {
  return String(status || '')
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export default function StatusBadge({ status }) {
  const color = STATUS_MAP[status] || 'slate'
  return <Badge color={color}>{humanize(status)}</Badge>
}
