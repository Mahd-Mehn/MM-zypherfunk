/**
 * Subscription API Service
 */

import { apiClient } from './client'
import type {
  Subscription,
  SubscriptionCreate,
  SubscriptionUpdate,
  SubscriptionListResponse,
} from './types'

export const subscriptionsAPI = {
  /**
   * Get user's subscriptions
   */
  async getSubscriptions(): Promise<SubscriptionListResponse> {
    return apiClient.get<SubscriptionListResponse>('/api/v1/subscriptions')
  },

  /**
   * Create new subscription (start copy trading)
   */
  async createSubscription(data: SubscriptionCreate): Promise<Subscription> {
    return apiClient.post<Subscription>('/api/v1/subscriptions', data)
  },

  /**
   * Get specific subscription
   */
  async getSubscription(subscriptionId: string): Promise<Subscription> {
    return apiClient.get<Subscription>(`/api/v1/subscriptions/${subscriptionId}`)
  },

  /**
   * Update subscription settings
   */
  async updateSubscription(
    subscriptionId: string,
    data: SubscriptionUpdate
  ): Promise<Subscription> {
    return apiClient.patch<Subscription>(`/api/v1/subscriptions/${subscriptionId}`, data)
  },

  /**
   * Pause subscription
   */
  async pauseSubscription(subscriptionId: string): Promise<Subscription> {
    return apiClient.post<Subscription>(`/api/v1/subscriptions/${subscriptionId}/pause`)
  },

  /**
   * Resume subscription
   */
  async resumeSubscription(subscriptionId: string): Promise<Subscription> {
    return apiClient.post<Subscription>(`/api/v1/subscriptions/${subscriptionId}/resume`)
  },

  /**
   * Cancel subscription
   */
  async cancelSubscription(subscriptionId: string): Promise<{ message: string }> {
    return apiClient.delete(`/api/v1/subscriptions/${subscriptionId}`)
  },
}
