/**
 * Portfolio Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { portfolioAPI } from '@/lib/api'
import type {
  PortfolioOverview,
  PortfolioAllocation,
  PortfolioPerformance,
  DashboardData,
  Alert,
} from '@/lib/api/types'

export function usePortfolio() {
  const [overview, setOverview] = useState<PortfolioOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadOverview()
  }, [])

  const loadOverview = async () => {
    try {
      setLoading(true)
      const data = await portfolioAPI.getOverview()
      setOverview(data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load portfolio:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return {
    overview,
    loading,
    error,
    refetch: loadOverview,
  }
}

export function usePortfolioAllocation() {
  const [allocation, setAllocation] = useState<PortfolioAllocation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAllocation()
  }, [])

  const loadAllocation = async () => {
    try {
      setLoading(true)
      const data = await portfolioAPI.getAllocation()
      setAllocation(data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load allocation:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return {
    allocation,
    loading,
    error,
    refetch: loadAllocation,
  }
}

export function usePortfolioPerformance(timeframe: '7d' | '30d' | '90d' | '1y' = '30d') {
  const [performance, setPerformance] = useState<PortfolioPerformance | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPerformance()
  }, [timeframe])

  const loadPerformance = async () => {
    try {
      setLoading(true)
      const data = await portfolioAPI.getPerformance(timeframe)
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

export function useDashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      const data = await portfolioAPI.getDashboard()
      setDashboard(data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load dashboard:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return {
    dashboard,
    loading,
    error,
    refetch: loadDashboard,
  }
}

export function useAlerts(limit: number = 20, unreadOnly: boolean = false) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAlerts()
  }, [limit, unreadOnly])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      const data = await portfolioAPI.getAlerts(limit, unreadOnly)
      setAlerts(data.alerts)
      setUnreadCount(data.unread_count)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load alerts:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = useCallback(async (alertId: string) => {
    try {
      await portfolioAPI.markAlertRead(alertId)
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, read: true } : alert
        )
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (err: any) {
      console.error('Failed to mark alert as read:', err)
    }
  }, [])

  return {
    alerts,
    unreadCount,
    loading,
    error,
    markAsRead,
    refetch: loadAlerts,
  }
}
