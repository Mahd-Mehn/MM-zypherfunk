/**
 * Subscriptions Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { subscriptionsAPI } from '@/lib/api'
import type { Subscription, SubscriptionCreate, SubscriptionUpdate, TraderFollower } from '@/lib/api/types'

export function useSubscriptions() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [followers, setFollowers] = useState<TraderFollower[]>([])
  const [isTrader, setIsTrader] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSubscriptions()
  }, [])

  const loadSubscriptions = async () => {
    try {
      setLoading(true)
      const data = await subscriptionsAPI.getSubscriptions()
      
      // Check if response contains followers (trader view) or subscriptions (follower view)
      if ('followers' in data && Array.isArray(data.followers)) {
        setFollowers(data.followers as TraderFollower[])
        setIsTrader(true)
        setSubscriptions([])
      } else if ('subscriptions' in data && Array.isArray(data.subscriptions)) {
        setSubscriptions(data.subscriptions as Subscription[])
        setIsTrader(false)
        setFollowers([])
      }
      
      setError(null)
    } catch (err: any) {
      console.error('Failed to load subscriptions:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const createSubscription = useCallback(async (data: SubscriptionCreate) => {
    try {
      setError(null)
      const newSubscription = await subscriptionsAPI.createSubscription(data)
      setSubscriptions((prev) => [newSubscription, ...prev])
      return newSubscription
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const updateSubscription = useCallback(
    async (subscriptionId: string, data: SubscriptionUpdate) => {
      try {
        setError(null)
        const updated = await subscriptionsAPI.updateSubscription(subscriptionId, data)
        setSubscriptions((prev) =>
          prev.map((sub) => (sub.id === subscriptionId ? updated : sub))
        )
        return updated
      } catch (err: any) {
        setError(err.message)
        throw err
      }
    },
    []
  )

  const pauseSubscription = useCallback(async (subscriptionId: string) => {
    try {
      setError(null)
      const updated = await subscriptionsAPI.pauseSubscription(subscriptionId)
      setSubscriptions((prev) =>
        prev.map((sub) => (sub.id === subscriptionId ? updated : sub))
      )
      return updated
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const resumeSubscription = useCallback(async (subscriptionId: string) => {
    try {
      setError(null)
      const updated = await subscriptionsAPI.resumeSubscription(subscriptionId)
      setSubscriptions((prev) =>
        prev.map((sub) => (sub.id === subscriptionId ? updated : sub))
      )
      return updated
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const cancelSubscription = useCallback(async (subscriptionId: string) => {
    try {
      setError(null)
      await subscriptionsAPI.cancelSubscription(subscriptionId)
      setSubscriptions((prev) => prev.filter((sub) => sub.id !== subscriptionId))
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  return {
    subscriptions,
    followers,
    isTrader,
    loading,
    error,
    createSubscription,
    updateSubscription,
    pauseSubscription,
    resumeSubscription,
    cancelSubscription,
    refetch: loadSubscriptions,
  }
}
