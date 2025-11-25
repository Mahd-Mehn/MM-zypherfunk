/**
 * API Client - Base HTTP client with authentication and error handling
 */

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

export interface APIResponse<T = any> {
  data?: T
  error?: {
    code: string
    message: string
    details?: any
  }
}

class APIClient {
  private baseURL: string
  private timeout: number

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    this.timeout = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000')
  }

  /**
   * Build full URL for an API endpoint, ensuring the API prefix is included.
   * - Gateway exposes routes under `/api/v1`.
   */
  private buildUrl(endpoint: string): string {
    const apiPrefix = '/api/v1'
    const base = this.baseURL.replace(/\/$/, '')

    // Ensure endpoint starts with a slash
    const ep = endpoint.startsWith('/') ? endpoint : `/${endpoint}`

    // If caller already included the api prefix, don't double-prefix
    if (ep.startsWith(`${apiPrefix}/`) || ep === apiPrefix) {
      return `${base}${ep}`
    }

    return `${base}${apiPrefix}${ep}`
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('access_token')
  }

  private setAuthToken(token: string) {
    if (typeof window === 'undefined') return
    localStorage.setItem('access_token', token)
  }

  private removeAuthToken() {
    if (typeof window === 'undefined') return
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('refresh_token')
  }

  private setRefreshToken(token: string) {
    if (typeof window === 'undefined') return
    localStorage.setItem('refresh_token', token)
  }

  private async refreshAccessToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) return false

    try {
      const response = await fetch(this.buildUrl('/auth/refresh'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (response.ok) {
        const data = await response.json()
        this.setAuthToken(data.access_token)
        return true
      }
      
      this.removeAuthToken()
      return false
    } catch (error) {
      this.removeAuthToken()
      return false
    }
  }

  async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = this.buildUrl(endpoint)
    const token = this.getAuthToken()

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      // Handle 401 - Try to refresh token
      if (response.status === 401 && token) {
        const refreshed = await this.refreshAccessToken()
        if (refreshed) {
          // Retry the request with new token
          return this.request<T>(endpoint, options)
        }
        // Don't redirect here - let the component handle it
        // This prevents redirect loops
        throw new APIError('Authentication required', 401, 'UNAUTHORIZED')
      }

      const data = await response.json()

      if (!response.ok) {
        throw new APIError(
          data.detail || data.message || 'Request failed',
          response.status,
          data.code,
          data.details
        )
      }

      return data as T
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof APIError) {
        throw error
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new APIError('Request timeout', 408, 'TIMEOUT')
        }
        throw new APIError(error.message, 500, 'NETWORK_ERROR')
      }

      throw new APIError('Unknown error occurred', 500, 'UNKNOWN_ERROR')
    }
  }

  async get<T = any>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const queryString = params
      ? '?' + new URLSearchParams(params).toString()
      : ''
    return this.request<T>(`${endpoint}${queryString}`, { method: 'GET' })
  }

  async post<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async put<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async patch<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  async delete<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  // Auth helpers
  setTokens(accessToken: string, refreshToken: string) {
    this.setAuthToken(accessToken)
    this.setRefreshToken(refreshToken)
  }

  clearTokens() {
    this.removeAuthToken()
  }

  isAuthenticated(): boolean {
    return !!this.getAuthToken()
  }
}

export const apiClient = new APIClient()
