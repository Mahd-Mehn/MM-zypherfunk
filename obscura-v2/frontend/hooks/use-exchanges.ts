/**
 * Exchange Connections Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { exchangesAPI } from '@/lib/api'
import type {
  ExchangeConnection,
  ExchangeConnectionCreate,
  SupportedExchange,
} from '@/lib/api/types'

export function useExchanges() {
  const [connections, setConnections] = useState<ExchangeConnection[]>([])
  const [supportedExchanges, setSupportedExchanges] = useState<SupportedExchange[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [connectionsData, supportedData] = await Promise.all([
        exchangesAPI.getUserConnections(),
        exchangesAPI.getSupportedExchanges(),
      ])
      setConnections(connectionsData.connections)
      setSupportedExchanges(supportedData)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load exchanges:', err)
      setError(err.message)
      // Set empty arrays on error so the app doesn't break
      setConnections([])
      setSupportedExchanges([])
    } finally {
      setLoading(false)
    }
  }

  const createConnection = useCallback(async (data: ExchangeConnectionCreate) => {
    try {
      setError(null)
      const newConnection = await exchangesAPI.createConnection(data)
      setConnections((prev) => [newConnection, ...prev])
      return newConnection
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const testConnection = useCallback(async (connectionId: string) => {
    try {
      setError(null)
      const result = await exchangesAPI.testConnection(connectionId)
      // Refresh connections to get updated status
      await loadData()
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const deleteConnection = useCallback(async (connectionId: string) => {
    try {
      setError(null)
      await exchangesAPI.deleteConnection(connectionId)
      setConnections((prev) => prev.filter((c) => c.id !== connectionId))
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  return {
    connections,
    supportedExchanges,
    loading,
    error,
    createConnection,
    testConnection,
    deleteConnection,
    refetch: loadData,
  }
}
