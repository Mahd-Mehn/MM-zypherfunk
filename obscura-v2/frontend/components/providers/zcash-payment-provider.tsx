"use client"

import { createContext, useContext, useState, useCallback, ReactNode } from "react"
import { paymentsAPI, type PaymentResponse, type PaymentStatusResponse } from "@/lib/api/payments"
import { generatePaymentURI, SUBSCRIPTION_TIERS } from "@/lib/zcash/payment"

interface ZcashPaymentContextType {
  // State
  currentPayment: PaymentResponse | null
  paymentStatus: PaymentStatusResponse | null
  isLoading: boolean
  error: string | null
  
  // Actions
  createPayment: (tier: 'basic' | 'pro' | 'premium', traderId?: string) => Promise<PaymentResponse>
  checkPayment: () => Promise<PaymentStatusResponse>
  clearPayment: () => void
  simulatePayment: () => Promise<void>
  
  // Utils
  getPaymentQRData: () => string | null
  getTierInfo: (tier: 'basic' | 'pro' | 'premium') => typeof SUBSCRIPTION_TIERS['basic']
}

const ZcashPaymentContext = createContext<ZcashPaymentContextType | undefined>(undefined)

interface ZcashPaymentProviderProps {
  children: ReactNode
  userId: string
}

export function ZcashPaymentProvider({ children, userId }: ZcashPaymentProviderProps) {
  const [currentPayment, setCurrentPayment] = useState<PaymentResponse | null>(null)
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Polling interval reference
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null)

  const createPayment = useCallback(async (
    tier: 'basic' | 'pro' | 'premium',
    traderId?: string
  ): Promise<PaymentResponse> => {
    setIsLoading(true)
    setError(null)
    
    try {
      const payment = await paymentsAPI.createSubscriptionPayment({
        userId,
        tier,
        traderId,
      })
      
      setCurrentPayment(payment)
      setPaymentStatus({ 
        paymentId: payment.paymentId, 
        status: 'pending', 
        confirmations: 0 
      })
      
      // Start polling for payment confirmation
      startPolling(payment.paymentAddress)
      
      return payment
    } catch (err: any) {
      setError(err.message || 'Failed to create payment')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const startPolling = useCallback((paymentAddress: string) => {
    // Clear existing poll
    if (pollInterval) {
      clearInterval(pollInterval)
    }
    
    // Poll every 10 seconds
    const interval = setInterval(async () => {
      try {
        const status = await paymentsAPI.checkPaymentStatus(paymentAddress)
        setPaymentStatus(status)
        
        if (status.status === 'confirmed' || status.status === 'expired') {
          clearInterval(interval)
          setPollInterval(null)
        }
      } catch (err) {
        console.error('Payment polling error:', err)
      }
    }, 10000)
    
    setPollInterval(interval)
  }, [pollInterval])

  const checkPayment = useCallback(async (): Promise<PaymentStatusResponse> => {
    if (!currentPayment) {
      throw new Error('No active payment')
    }
    
    setIsLoading(true)
    try {
      const status = await paymentsAPI.checkPaymentStatus(currentPayment.paymentAddress)
      setPaymentStatus(status)
      return status
    } catch (err: any) {
      setError(err.message || 'Failed to check payment')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [currentPayment])

  const clearPayment = useCallback(() => {
    if (pollInterval) {
      clearInterval(pollInterval)
      setPollInterval(null)
    }
    setCurrentPayment(null)
    setPaymentStatus(null)
    setError(null)
  }, [pollInterval])

  const simulatePayment = useCallback(async () => {
    if (!currentPayment) {
      throw new Error('No active payment')
    }
    
    setIsLoading(true)
    try {
      await paymentsAPI.simulatePayment(currentPayment.paymentAddress)
      // Check status after simulation
      await checkPayment()
    } catch (err: any) {
      setError(err.message || 'Failed to simulate payment')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [currentPayment, checkPayment])

  const getPaymentQRData = useCallback((): string | null => {
    if (!currentPayment) return null
    return currentPayment.paymentUri
  }, [currentPayment])

  const getTierInfo = useCallback((tier: 'basic' | 'pro' | 'premium') => {
    return SUBSCRIPTION_TIERS[tier]
  }, [])

  return (
    <ZcashPaymentContext.Provider
      value={{
        currentPayment,
        paymentStatus,
        isLoading,
        error,
        createPayment,
        checkPayment,
        clearPayment,
        simulatePayment,
        getPaymentQRData,
        getTierInfo,
      }}
    >
      {children}
    </ZcashPaymentContext.Provider>
  )
}

export function useZcashPayment() {
  const context = useContext(ZcashPaymentContext)
  if (context === undefined) {
    throw new Error("useZcashPayment must be used within a ZcashPaymentProvider")
  }
  return context
}
