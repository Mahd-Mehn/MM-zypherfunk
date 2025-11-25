/**
 * User-friendly error messages for API errors
 */

import { APIError } from './client'

export function getErrorMessage(error: unknown): string {
  if (error instanceof APIError) {
    // Map common error codes to user-friendly messages
    switch (error.code) {
      case 'UNAUTHORIZED':
        return 'Please log in to continue'
      case 'FORBIDDEN':
        return 'You do not have permission to perform this action'
      case 'NOT_FOUND':
        return 'The requested resource was not found'
      case 'VALIDATION_ERROR':
        return error.details?.message || 'Invalid input provided'
      case 'RATE_LIMIT_EXCEEDED':
        return 'Too many requests. Please try again later'
      case 'TIMEOUT':
        return 'Request timed out. Please try again'
      case 'NETWORK_ERROR':
        return 'Network error. Please check your connection'
      default:
        return error.message || 'An unexpected error occurred'
    }
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'An unexpected error occurred'
}

export function isAuthError(error: unknown): boolean {
  return error instanceof APIError && error.status === 401
}

export function isValidationError(error: unknown): boolean {
  return error instanceof APIError && error.status === 422
}

export function isRateLimitError(error: unknown): boolean {
  return error instanceof APIError && error.status === 429
}

export function getValidationErrors(error: unknown): Record<string, string[]> | null {
  if (!isValidationError(error)) return null
  
  if (error instanceof APIError && error.details?.errors) {
    return error.details.errors
  }
  
  return null
}
