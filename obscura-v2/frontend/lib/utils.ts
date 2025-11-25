import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

type ShortenIdentifierOptions = {
  prefixLength?: number
  suffixLength?: number
  fallback?: string
  separator?: string
}

/**
 * Safely shorten an address / identifier, guarding against undefined values.
 */
export function shortenIdentifier(
  value?: string | null,
  { prefixLength = 6, suffixLength = 4, fallback = '—', separator = '…' }: ShortenIdentifierOptions = {}
) {
  if (!value) return fallback
  const str = String(value)
  if (prefixLength <= 0 && suffixLength <= 0) return str
  if (str.length <= prefixLength + suffixLength) return str

  const prefix = prefixLength > 0 ? str.slice(0, prefixLength) : ''
  const suffix = suffixLength > 0 ? str.slice(-suffixLength) : ''

  if (prefixLength > 0 && suffixLength > 0) {
    return `${prefix}${separator}${suffix}`
  }

  if (prefixLength > 0) {
    return `${prefix}${separator}`.trim()
  }

  return `${separator}${suffix}`.trim()
}

export function formatPrefix(value?: string | null, length = 6, fallback = '—') {
  if (!value) return fallback
  const str = String(value)
  if (length <= 0) return str
  return str.slice(0, length)
}
