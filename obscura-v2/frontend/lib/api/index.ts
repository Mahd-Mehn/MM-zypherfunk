/**
 * API Module - Central export for all API services
 */

export { apiClient, APIError } from './client'
export * from './types'

import { authAPI } from './auth'
import { exchangesAPI } from './exchanges'
import { subscriptionsAPI } from './subscriptions'
import { tradersAPI } from './traders'
import { portfolioAPI } from './portfolio'
import { executionsAPI } from './executions'
import { systemAPI } from './system'

export { authAPI, exchangesAPI, subscriptionsAPI, tradersAPI, portfolioAPI, executionsAPI, systemAPI }

// Convenience export for all APIs
export const api = {
  auth: authAPI,
  exchanges: exchangesAPI,
  subscriptions: subscriptionsAPI,
  traders: tradersAPI,
  portfolio: portfolioAPI,
  executions: executionsAPI,
  system: systemAPI,
}

export default api
