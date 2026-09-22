// Validated palette (see dataviz skill reference) - fixed categorical order,
// never cycled/reassigned by filters.
export const CATEGORICAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']

export const STATUS_COLORS = {
  good: '#0ca30c',
  warning: '#fab219',
  serious: '#ec835a',
  critical: '#d03b3b',
  neutral: '#94a3b8',
}

export const INVOICE_STATUS_COLOR = {
  APPROVED: STATUS_COLORS.good,
  PAID: STATUS_COLORS.good,
  PENDING_APPROVAL: STATUS_COLORS.warning,
  PAYMENT_PENDING: STATUS_COLORS.warning,
  EXCEPTION: STATUS_COLORS.serious,
  REJECTED: STATUS_COLORS.critical,
  PROCESSING: CATEGORICAL[0],
  EXTRACTED: CATEGORICAL[0],
  VALIDATED: CATEGORICAL[0],
  UPLOADED: STATUS_COLORS.neutral,
}

// Sequential blue ramp, light -> dark (for AP aging buckets: least overdue -> most overdue).
export const SEQUENTIAL_BLUE = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b']

export function colorForStatus(status) {
  return INVOICE_STATUS_COLOR[status] || STATUS_COLORS.neutral
}
