/**
 * Executions API Service
 */

import { apiClient } from './client'
import type {
  Execution,
  ExecutionListResponse,
  ExecutionStats,
  ExecutionStatus,
} from './types'

export interface ExecutionFilters {
  limit?: number
  offset?: number
  status?: ExecutionStatus
  exchange?: string
  trader_id?: string
  start_date?: string
  end_date?: string
}

export interface CopyTradeExecuteRequest {
  trader_id: string
  subscription_id: string
  trade_id: string
  exchange: string
  symbol: string
  side: 'buy' | 'sell'
  order_type: string
  quantity: number
  price?: number
}

export const executionsAPI = {
  /**
   * Get user's executions
   */
  async getExecutions(filters?: ExecutionFilters): Promise<ExecutionListResponse> {
    return apiClient.get<ExecutionListResponse>('/api/v1/executions', filters)
  },

  /**
   * Get execution details
   */
  async getExecution(executionId: string): Promise<Execution> {
    return apiClient.get<Execution>(`/api/v1/executions/${executionId}`)
  },

  /**
   * Execute copy trade
   */
  async executeCopyTrade(data: CopyTradeExecuteRequest): Promise<Execution> {
    return apiClient.post<Execution>('/api/v1/executions/execute', data)
  },

  /**
   * Cancel execution
   */
  async cancelExecution(executionId: string): Promise<{ message: string }> {
    return apiClient.post(`/api/v1/executions/${executionId}/cancel`)
  },

  /**
   * Get execution statistics
   */
  async getStats(timeframe: '7d' | '30d' | '90d' | '1y' | 'all' = '30d'): Promise<ExecutionStats> {
    return apiClient.get<ExecutionStats>('/api/v1/executions/stats/summary', { timeframe })
  },
}
