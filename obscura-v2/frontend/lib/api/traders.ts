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

export interface TraderRegistration {
  display_name: string
  bio?: string
  performance_fee: number
  exchanges: string[]
  chains?: string[]
  avatar_url?: string
}

export interface TraderUpdate {
  display_name?: string
  bio?: string
  performance_fee?: number
  exchanges?: string[]
  chains?: string[]
  avatar_url?: string
}

export interface TraderSettings {
  notifications_enabled: boolean
  auto_verify_trades: boolean
  public_profile: boolean
  show_pnl: boolean
  show_trade_history: boolean
  min_copy_amount: number | null
  max_followers: number | null
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
    timeframe: '7d' | '30d' | '90d' | 'all' = '30d'
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
  ): Promise<{ trades: Trade[]; total: number; limit: number; offset: number }> {
    return apiClient.get(`/api/v1/traders/${traderId}/trades`, { limit, offset })
  },

  /**
   * Get trader's followers
   */
  async getTraderFollowers(
    traderId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<{ followers: any[]; total: number; limit: number; offset: number }> {
    return apiClient.get(`/api/v1/traders/${traderId}/followers`, { limit, offset })
  },

  async getTraderSubscriberList(traderId: string): Promise<TraderFollowerListResponse> {
    return apiClient.get(`/api/v1/traders/${traderId}/followers`)
  },

  // ============= Trader Management =============

  /**
   * Register as a new trader
   */
  async register(data: TraderRegistration): Promise<TraderProfile> {
    return apiClient.post<TraderProfile>('/api/v1/traders/register', data)
  },

  /**
   * Update trader profile
   */
  async updateProfile(traderId: string, data: TraderUpdate): Promise<TraderProfile> {
    return apiClient.patch<TraderProfile>(`/api/v1/traders/${traderId}`, data)
  },

  /**
   * Get current trader's own profile (if registered as trader)
   */
  async getMyProfile(): Promise<TraderProfile> {
    return apiClient.get<TraderProfile>('/api/v1/traders/me')
  },

  /**
   * Get trader settings
   */
  async getSettings(traderId: string): Promise<TraderSettings> {
    return apiClient.get<TraderSettings>(`/api/v1/traders/${traderId}/settings`)
  },

  /**
   * Update trader settings
   */
  async updateSettings(traderId: string, settings: Partial<TraderSettings>): Promise<TraderSettings> {
    return apiClient.patch<TraderSettings>(`/api/v1/traders/${traderId}/settings`, settings)
  },

  /**
   * Deactivate trader account (stop accepting followers)
   */
  async deactivate(traderId: string): Promise<{ message: string; deactivated_at: string }> {
    return apiClient.post(`/api/v1/traders/${traderId}/deactivate`)
  },

  /**
   * Reactivate trader account
   */
  async reactivate(traderId: string): Promise<TraderProfile> {
    return apiClient.post<TraderProfile>(`/api/v1/traders/${traderId}/reactivate`)
  },
}
