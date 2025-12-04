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
import { zcashPaymentsAPI } from './zcash-payments'
import { verificationAPI } from './verification'
import { dashboardAPI } from './dashboard'
import { copyTradingAPI } from './copy-trading'
import { citadelAPI, citadelGatewayAPI } from './citadel'
import { analyticsAPI } from './analytics'

export {
  authAPI,
  exchangesAPI,
  subscriptionsAPI,
  tradersAPI,
  portfolioAPI,
  executionsAPI,
  systemAPI,
  zcashPaymentsAPI,
  verificationAPI,
  dashboardAPI,
  copyTradingAPI,
  citadelAPI,
  citadelGatewayAPI,
  analyticsAPI,
}

// Convenience export for all APIs
export const api = {
  auth: authAPI,
  exchanges: exchangesAPI,
  subscriptions: subscriptionsAPI,
  traders: tradersAPI,
  portfolio: portfolioAPI,
  executions: executionsAPI,
  system: systemAPI,
  zcashPayments: zcashPaymentsAPI,
  verification: verificationAPI,
  dashboard: dashboardAPI,
  copyTrading: copyTradingAPI,
  citadel: citadelAPI,
  citadelGateway: citadelGatewayAPI,
  analytics: analyticsAPI,
}

export default api
