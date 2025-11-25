/**
 * Exchange Connection API Service
 */

import { apiClient } from './client'
import type {
  ExchangeConnection,
  ExchangeConnectionCreate,
  ExchangeConnectionUpdate,
  ExchangeConnectionTest,
  ExchangeListResponse,
  SupportedExchange,
} from './types'

export const exchangesAPI = {
  /**
   * Get list of supported exchanges
   */
  async getSupportedExchanges(): Promise<SupportedExchange[]> {
    return apiClient.get<SupportedExchange[]>('/api/v1/exchanges/supported')
  },

  /**
   * Get user's exchange connections
   */
  async getUserConnections(): Promise<ExchangeListResponse> {
    return apiClient.get<ExchangeListResponse>('/api/v1/exchanges')
  },

  /**
   * Create new exchange connection
   */
  async createConnection(data: ExchangeConnectionCreate): Promise<ExchangeConnection> {
    return apiClient.post<ExchangeConnection>('/api/v1/exchanges', data)
  },

  /**
   * Get specific exchange connection
   */
  async getConnection(connectionId: string): Promise<ExchangeConnection> {
    return apiClient.get<ExchangeConnection>(`/api/v1/exchanges/${connectionId}`)
  },

  /**
   * Test exchange connection
   */
  async testConnection(connectionId: string): Promise<ExchangeConnectionTest> {
    return apiClient.post<ExchangeConnectionTest>(`/api/v1/exchanges/${connectionId}/test`)
  },

  /**
   * Update exchange connection
   */
  async updateConnection(
    connectionId: string,
    data: ExchangeConnectionUpdate
  ): Promise<ExchangeConnection> {
    return apiClient.put<ExchangeConnection>(`/api/v1/exchanges/${connectionId}`, data)
  },

  /**
   * Delete exchange connection
   */
  async deleteConnection(connectionId: string): Promise<{ message: string }> {
    return apiClient.delete(`/api/v1/exchanges/${connectionId}`)
  },
}
