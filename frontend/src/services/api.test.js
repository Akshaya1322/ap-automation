import { describe, expect, it } from 'vitest'
import { extractErrorMessage } from './api'

describe('extractErrorMessage', () => {
  it('prefers a top-level message field', () => {
    const error = { response: { data: { message: 'Invoice not found.' } } }
    expect(extractErrorMessage(error)).toBe('Invoice not found.')
  })

  it('falls back to DRF detail field', () => {
    const error = { response: { data: { detail: 'Authentication credentials were not provided.' } } }
    expect(extractErrorMessage(error)).toBe('Authentication credentials were not provided.')
  })

  it('extracts the first field error from a validation errors object', () => {
    const error = { response: { data: { errors: { gstin: ['Invalid GSTIN format.'] } } } }
    expect(extractErrorMessage(error)).toBe('Invalid GSTIN format.')
  })

  it('falls back to a generic message when nothing is present', () => {
    const error = {}
    expect(extractErrorMessage(error)).toBe('Something went wrong. Please try again.')
  })

  it('uses the network error message when there is no response', () => {
    const error = { message: 'Network Error' }
    expect(extractErrorMessage(error)).toBe('Network Error')
  })
})
