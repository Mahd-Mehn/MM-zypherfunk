/**
 * Traders API Service
 */

import { apiClient } from './client'
import type {
  TraderProfile,
  TraderPerformance,
  Trade,
  LeaderboardResponse,
  TraderFollowerListResponse,
} from './types'

export interface TraderFilters {
  search?: string
  verificationType?: string
  chain?: string
  sortBy?: 'followers' | 'winRate' | 'pnl' | 'trades'
  limit?: number
  offset?: number
  timeframe?: '7d' | '30d' | '90d' | 'all'
}

export const tradersAPI = {
  /**
   * Get leaderboard of traders
   */
  async getLeaderboard(filters?: TraderFilters): Promise<LeaderboardResponse> {
    return apiClient.get<LeaderboardResponse>('/api/v1/traders/leaderboard', filters)
  },

  /**
   * Get trader profile
   */
  async getTraderProfile(traderId: string): Promise<TraderProfile> {
    return apiClient.get<TraderProfile>(`/api/v1/traders/${traderId}`)
  },

  /**
   * Get trader performance data
   */
  async getTraderPerformance(
    traderId: string,
    timeframe: '7d' | '30d' | '90d' | '1y' = '30d'
  ): Promise<TraderPerformance> {
    return apiClient.get<TraderPerformance>(`/api/v1/traders/${traderId}/performance`, {
      timeframe,
    })
  },

  /**
   * Get trader's trades
   */
  async getTraderTrades(
    traderId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<{ trades: Trade[]; total: number }> {
    return apiClient.get(`/api/v1/traders/${traderId}/trades`, { limit, offset })
  },

  /**
   * Get trader's followers
   */
  async getTraderFollowers(traderId: string): Promise<{ followers: number; follower_list: any[] }> {
    return apiClient.get(`/api/v1/traders/${traderId}/followers`)
  },

  async getTraderSubscriberList(traderId: string): Promise<TraderFollowerListResponse> {
    return apiClient.get(`/api/v1/traders/${traderId}/followers`)
  },
}
