/**
 * Traders Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { tradersAPI } from '@/lib/api'
import type { TraderFilters } from '@/lib/api/traders'
import type { TraderProfile, TraderPerformance, Trade, TraderFollower } from '@/lib/api/types'

type UseTradersOptions = {
  enabled?: boolean
}

export function useTraderFollowers(traderId: string | null) {
  const [followers, setFollowers] = useState<TraderFollower[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!traderId) {
      setLoading(false)
      return
    }
    loadFollowers()
  }, [traderId])

  const loadFollowers = async () => {
    if (!traderId) return

    try {
      setLoading(true)
      const data = await tradersAPI.getTraderSubscriberList(traderId)
      setFollowers(data.followers)
      setTotal(data.total)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load trader followers:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return {
    followers,
    total,
    loading,
    error,
    refetch: loadFollowers,
  }
}

export function useTraders(filters?: TraderFilters, options?: UseTradersOptions) {
  const enabled = options?.enabled ?? true
  const [traders, setTraders] = useState<TraderProfile[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!enabled) {
      setLoading(false)
      return
    }
    loadTraders()
  }, [JSON.stringify(filters), enabled])

  const loadTraders = async () => {
    if (!enabled) return
    try {
      setLoading(true)
      const data = await tradersAPI.getLeaderboard(filters)
      setTraders(data.traders)
      setTotal(data.total)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load traders:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return {
    traders,
    total,
    loading,
    error,
    refetch: loadTraders,
  }
}

export function useTraderProfile(traderId: string | null) {
  const [trader, setTrader] = useState<TraderProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!traderId) {
      setLoading(false)
      return
    }
    loadTrader()
  }, [traderId])

  const loadTrader = async () => {
    if (!traderId) return

    try {
      setLoading(true)
      const data = await tradersAPI.getTraderProfile(traderId)
      setTrader(data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load trader:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return {
    trader,
    loading,
    error,
    refetch: loadTrader,
  }
}

export function useTraderPerformance(
  traderId: string | null,
  timeframe: '7d' | '30d' | '90d' | '1y' = '30d'
) {
  const [performance, setPerformance] = useState<TraderPerformance | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!traderId) {
      setLoading(false)
      return
    }
    loadPerformance()
  }, [traderId, timeframe])

  const loadPerformance = async () => {
    if (!traderId) return

    try {
      setLoading(true)
      const data = await tradersAPI.getTraderPerformance(traderId, timeframe)
      setPerformance(data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load performance:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return {
    performance,
    loading,
    error,
    refetch: loadPerformance,
  }
}

export function useTraderTrades(traderId: string | null, limit: number = 20) {
  const [trades, setTrades] = useState<Trade[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!traderId) {
      setLoading(false)
      return
    }
    loadTrades()
  }, [traderId, limit])

  const loadTrades = async () => {
    if (!traderId) return

    try {
      setLoading(true)
      const data = await tradersAPI.getTraderTrades(traderId, limit)
      setTrades(data.trades)
      setTotal(data.total)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load trades:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return {
    trades,
    total,
    loading,
    error,
    refetch: loadTrades,
  }
}
