/**
 * useZcashPayment Hook
 * 
 * Manages Zcash payment flow with automatic status polling
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { zcashPaymentsAPI, type PaymentResponse, type PaymentStatus } from '@/lib/api/zcash-payments'
import { type PaymentRequest, SUBSCRIPTION_TIERS } from '@/lib/zcash/payment'

interface UseZcashPaymentOptions {
  pollInterval?: number // ms, default 5000
  maxPollTime?: number // ms, default 30 min
  onPaymentConfirmed?: (payment: PaymentResponse) => void
  onPaymentExpired?: (payment: PaymentResponse) => void
}

interface UseZcashPaymentReturn {
  // State
  payment: PaymentResponse | null
  paymentRequest: PaymentRequest | null
  status: PaymentStatus | null
  loading: boolean
  error: string | null
  isPolling: boolean

  // Actions
  createPayment: (tier: keyof typeof SUBSCRIPTION_TIERS, traderId?: string) => Promise<void>
  checkStatus: () => Promise<boolean>
  startPolling: () => void
  stopPolling: () => void
  reset: () => void
  simulatePayment: () => Promise<void>
}

export function useZcashPayment(
  userId: string,
  options: UseZcashPaymentOptions = {}
): UseZcashPaymentReturn {
  const {
    pollInterval = 5000,
    maxPollTime = 30 * 60 * 1000, // 30 minutes
    onPaymentConfirmed,
    onPaymentExpired,
  } = options

  const [payment, setPayment] = useState<PaymentResponse | null>(null)
  const [paymentRequest, setPaymentRequest] = useState<PaymentRequest | null>(null)
  const [status, setStatus] = useState<PaymentStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const pollStartTimeRef = useRef<number | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  const createPayment = useCallback(
    async (tier: keyof typeof SUBSCRIPTION_TIERS, traderId?: string) => {
      setLoading(true)
      setError(null)

      try {
        const response = await zcashPaymentsAPI.createPayment({
          userId,
          tier,
          traderId,
        })

        setPayment(response)
        setPaymentRequest({
          address: response.paymentAddress,
          amount: response.amountZec,
          memo: response.memo,
          label: `Obscura ${tier} Subscription`,
          message: traderId ? `Copy trading subscription for trader ${traderId}` : undefined,
        })
        setStatus({ id: response.id, status: 'pending' })
      } catch (err: any) {
        const message = err?.message || 'Failed to create payment'
        setError(message)
        throw new Error(message)
      } finally {
        setLoading(false)
      }
    },
    [userId]
  )

  const checkStatus = useCallback(async (): Promise<boolean> => {
    if (!payment) return false

    try {
      const statusResponse = await zcashPaymentsAPI.checkPaymentStatus(payment.id)
      setStatus(statusResponse)

      if (statusResponse.status === 'confirmed') {
        stopPolling()
        onPaymentConfirmed?.(payment)
        return true
      }

      if (statusResponse.status === 'expired') {
        stopPolling()
        onPaymentExpired?.(payment)
        return false
      }

      return false
    } catch (err: any) {
      console.error('Error checking payment status:', err)
      return false
    }
  }, [payment, onPaymentConfirmed, onPaymentExpired])

  const startPolling = useCallback(() => {
    if (pollIntervalRef.current || !payment) return

    setIsPolling(true)
    pollStartTimeRef.current = Date.now()

    pollIntervalRef.current = setInterval(async () => {
      // Check if exceeded max poll time
      if (
        pollStartTimeRef.current &&
        Date.now() - pollStartTimeRef.current > maxPollTime
      ) {
        stopPolling()
        setError('Payment verification timed out')
        return
      }

      await checkStatus()
    }, pollInterval)
  }, [payment, pollInterval, maxPollTime, checkStatus])

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
    setIsPolling(false)
    pollStartTimeRef.current = null
  }, [])

  const reset = useCallback(() => {
    stopPolling()
    setPayment(null)
    setPaymentRequest(null)
    setStatus(null)
    setError(null)
  }, [stopPolling])

  const simulatePayment = useCallback(async () => {
    if (!payment) return

    try {
      await zcashPaymentsAPI.simulatePayment(payment.paymentAddress)
      // Wait a moment then check status
      await new Promise((resolve) => setTimeout(resolve, 500))
      await checkStatus()
    } catch (err: any) {
      setError(err?.message || 'Simulation failed')
    }
  }, [payment, checkStatus])

  return {
    payment,
    paymentRequest,
    status,
    loading,
    error,
    isPolling,
    createPayment,
    checkStatus,
    startPolling,
    stopPolling,
    reset,
    simulatePayment,
  }
}

export default useZcashPayment
