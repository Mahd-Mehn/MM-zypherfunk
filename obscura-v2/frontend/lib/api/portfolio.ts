/**
 * Portfolio API Service
 */

import { apiClient } from './client'
import type {
  PortfolioOverview,
  PortfolioAllocation,
  PortfolioPerformance,
  DashboardData,
  AlertsResponse,
} from './types'

export const portfolioAPI = {
  /**
   * Get portfolio overview
   */
  async getOverview(): Promise<PortfolioOverview> {
    return apiClient.get<PortfolioOverview>('/api/v1/portfolio/overview')
  },

  /**
   * Get portfolio allocation
   */
  async getAllocation(): Promise<PortfolioAllocation> {
    return apiClient.get<PortfolioAllocation>('/api/v1/portfolio/allocation')
  },

  /**
   * Get portfolio performance
   */
  async getPerformance(
    timeframe: '7d' | '30d' | '90d' | '1y' = '30d'
  ): Promise<PortfolioPerformance> {
    return apiClient.get<PortfolioPerformance>('/api/v1/portfolio/performance', {
      timeframe,
    })
  },

  /**
   * Get dashboard data (overview + recent activity)
   */
  async getDashboard(): Promise<DashboardData> {
    return apiClient.get<DashboardData>('/api/v1/portfolio/dashboard')
  },

  /**
   * Get user alerts
   */
  async getAlerts(
    limit: number = 20,
    unreadOnly: boolean = false
  ): Promise<AlertsResponse> {
    return apiClient.get<AlertsResponse>('/api/v1/portfolio/alerts', {
      limit,
      unread_only: unreadOnly,
    })
  },

  /**
   * Mark alert as read
   */
  async markAlertRead(alertId: string): Promise<{ message: string }> {
    return apiClient.post(`/api/v1/portfolio/alerts/${alertId}/mark-read`)
  },
}
