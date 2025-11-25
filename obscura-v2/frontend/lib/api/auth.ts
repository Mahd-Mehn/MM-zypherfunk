/**
 * Authentication API Service
 */

import { apiClient } from './client'
import type {
  AuthResponse,
  MagicLinkRequest,
  MagicLinkResponse,
  MagicLinkVerify,
  User,
  UserType,
  WalletConnectRequest,
} from './types'

export const authAPI = {
  /**
   * Request a magic link for passwordless authentication
   */
  async requestMagicLink(email: string): Promise<MagicLinkResponse> {
    const data: MagicLinkRequest = { email }
    return apiClient.post<MagicLinkResponse>('/api/v1/auth/magic-link/request', data)
  },

  /**
   * Verify magic link token and authenticate
   */
  async verifyMagicLink(token: string): Promise<AuthResponse> {
    const data: MagicLinkVerify = { token }
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/magic-link/verify', data)
    
    // Store tokens
    apiClient.setTokens(response.access_token, response.refresh_token)
    
    return response
  },

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/api/v1/auth/me')
  },

  /**
   * Connect wallet address to user account
   */
  async connectWallet(walletAddress: string): Promise<User> {
    const data: WalletConnectRequest = { wallet_address: walletAddress }
    return apiClient.post<User>('/api/v1/auth/wallet/connect', data)
  },

  /**
   * Disconnect wallet from user account
   */
  async disconnectWallet(): Promise<User> {
    return apiClient.delete<User>('/api/v1/auth/wallet/disconnect')
  },

  /**
   * Update the current user's role (trader, follower, etc.)
   */
  async updateUserType(userId: string, userType: UserType): Promise<User> {
    return apiClient.put<User>(`/api/v1/auth/users/${userId}/type`, {
      user_type: userType,
    })
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout')
    } finally {
      apiClient.clearTokens()
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return apiClient.isAuthenticated()
  },
}
