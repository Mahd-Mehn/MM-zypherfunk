/**
 * System API Service
 */

import { apiClient } from './client'
import type { HealthCheck, RateLimitStatus } from './types'

export const systemAPI = {
  /**
   * Get system health status
   */
  async getHealth(): Promise<HealthCheck> {
    return apiClient.get<HealthCheck>('/health')
  },

  /**
   * Get detailed health check
   */
  async getDetailedHealth(): Promise<HealthCheck> {
    return apiClient.get<HealthCheck>('/api/v1/system/health/detailed')
  },

  /**
   * Get rate limit status
   */
  async getRateLimitStatus(): Promise<RateLimitStatus> {
    return apiClient.get<RateLimitStatus>('/api/v1/rate-limits/status')
  },
}
