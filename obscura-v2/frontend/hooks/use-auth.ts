/**
 * Authentication Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { authAPI } from '@/lib/api'
import type { User } from '@/lib/api/types'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasToken, setHasToken] = useState(false)

  const loadUser = useCallback(async () => {
    const isAuth = authAPI.isAuthenticated()
    setHasToken(isAuth)

    if (!isAuth) {
      setLoading(false)
      return
    }

    try {
      const userData = await authAPI.getCurrentUser()
      setUser(userData)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load user:', err)
      setError(err.message)

      // Only clear tokens and user if it's an authentication error (401)
      // For network errors, keep the token so user isn't logged out
      if (err.status === 401 || err.code === 'UNAUTHORIZED') {
        setUser(null)
        setHasToken(false)
        authAPI.logout()
      }
      // For other errors (network, timeout), keep hasToken true
      // so the user isn't immediately redirected to login
    } finally {
      setLoading(false)
    }
  }, [])

  // Load user on mount
  useEffect(() => {
    loadUser()
  }, [loadUser])

  const requestMagicLink = useCallback(async (email: string) => {
    try {
      setError(null)
      const response = await authAPI.requestMagicLink(email)
      return response
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const verifyMagicLink = useCallback(async (token: string) => {
    try {
      setError(null)
      console.log('Verifying magic link...')
      const response = await authAPI.verifyMagicLink(token)
      console.log('Magic link verified, setting user and token')
      setUser(response.user)
      setHasToken(true)
      console.log('User set:', response.user.email, 'hasToken:', true)
      return response
    } catch (err: any) {
      console.error('Magic link verification failed:', err)
      setError(err.message)
      throw err
    }
  }, [])

  const connectWallet = useCallback(async (walletAddress: string) => {
    try {
      setError(null)
      const updatedUser = await authAPI.connectWallet(walletAddress)
      setUser(updatedUser)
      return updatedUser
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const disconnectWallet = useCallback(async () => {
    try {
      setError(null)
      const updatedUser = await authAPI.disconnectWallet()
      setUser(updatedUser)
      return updatedUser
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await authAPI.logout()
      setUser(null)
      setHasToken(false)
      setError(null)
    } catch (err: any) {
      console.error('Logout error:', err)
    }
  }, [])

  const isAuthenticated = hasToken || !!user
  
  // Debug logging
  useEffect(() => {
    console.log('Auth state:', { 
      hasToken, 
      hasUser: !!user, 
      isAuthenticated, 
      loading,
      userEmail: user?.email 
    })
  }, [hasToken, user, isAuthenticated, loading])

  return {
    user,
    loading,
    error,
    // User is authenticated if they have a token OR if user data is loaded
    // This prevents redirect loops when API is temporarily unavailable
    isAuthenticated,
    requestMagicLink,
    verifyMagicLink,
    connectWallet,
    disconnectWallet,
    logout,
    refetch: loadUser,
  }
}
