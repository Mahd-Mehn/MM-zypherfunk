"use client"

import { createContext, useContext, ReactNode } from "react"
import { useAuth } from "@/hooks/use-auth"
import type { User } from "@/lib/api/types"

interface AuthContextType {
  user: User | null
  loading: boolean
  error: string | null
  isAuthenticated: boolean
  requestMagicLink: (email: string) => Promise<any>
  verifyMagicLink: (token: string) => Promise<any>
  connectWallet: (walletAddress: string) => Promise<User>
  disconnectWallet: () => Promise<User>
  logout: () => Promise<void>
  refetch: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const auth = useAuth()

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}

export function useAuthContext() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuthContext must be used within an AuthProvider")
  }
  return context
}
