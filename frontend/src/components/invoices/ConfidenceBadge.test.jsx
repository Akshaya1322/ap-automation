import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ConfidenceBadge from './ConfidenceBadge'

describe('ConfidenceBadge', () => {
  it('renders a dash when no level is provided', () => {
    render(<ConfidenceBadge level={null} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders the level and rounded score', () => {
    render(<ConfidenceBadge level="HIGH" score={93.6} />)
    expect(screen.getByText('HIGH')).toBeInTheDocument()
    expect(screen.getByText('(94%)')).toBeInTheDocument()
  })

  it('uses a red tone for LOW confidence', () => {
    render(<ConfidenceBadge level="LOW" score={12} />)
    expect(screen.getByText('LOW').closest('span')).toHaveClass('bg-red-100')
  })
})
