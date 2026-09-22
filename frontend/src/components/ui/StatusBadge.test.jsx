import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import StatusBadge from './StatusBadge'

describe('StatusBadge', () => {
  it('humanizes the status text', () => {
    render(<StatusBadge status="PENDING_APPROVAL" />)
    expect(screen.getByText('Pending Approval')).toBeInTheDocument()
  })

  it('renders a green tone for APPROVED', () => {
    render(<StatusBadge status="APPROVED" />)
    expect(screen.getByText('Approved')).toHaveClass('bg-emerald-100')
  })

  it('renders a red tone for REJECTED', () => {
    render(<StatusBadge status="REJECTED" />)
    expect(screen.getByText('Rejected')).toHaveClass('bg-red-100')
  })

  it('falls back gracefully for an unknown status', () => {
    render(<StatusBadge status="SOME_NEW_STATUS" />)
    expect(screen.getByText('Some New Status')).toBeInTheDocument()
  })
})
