'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { apiClient, tokenStorage } from './api-client'
import { useRouter } from 'next/navigation'
import { User } from '@/types'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

/**
 * Authentication provider component
 * Manages user state, login, register, and logout operations
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check if user is logged in on mount
    if (typeof window !== 'undefined') {
      const isAuthPage = window.location.pathname === '/login' || window.location.pathname === '/register'
      const hasToken = tokenStorage.getAccessToken()
      if (!isAuthPage && hasToken) {
        fetchUser()
      } else {
        setLoading(false)
      }
    }
  }, [])

  /**
   * Fetch current user information
   */
  const fetchUser = async () => {
    try {
      const response = await apiClient.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Login user with email and password
   */
  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.post('/auth/login', { email, password })
      const { access_token, refresh_token } = response.data
      tokenStorage.setTokens(access_token, refresh_token)
      await fetchUser()
      router.push('/accounts')
    } catch (error) {
      throw error
    }
  }

  /**
   * Register new user
   */
  const register = async (email: string, username: string, password: string) => {
    try {
      const response = await apiClient.post('/auth/register', {
        email,
        username,
        password,
      })
      const { access_token, refresh_token } = response.data
      tokenStorage.setTokens(access_token, refresh_token)
      await fetchUser()
      router.push('/accounts')
    } catch (error) {
      throw error
    }
  }

  /**
   * Logout user and clear tokens
   */
  const logout = async () => {
    try {
      await apiClient.post('/auth/logout')
    } catch (error) {
      // Logout anyway even if API fails
    } finally {
      tokenStorage.clearTokens()
      setUser(null)
      router.push('/login')
    }
  }

  /**
   * Refresh user data
   */
  const refreshUser = async () => {
    await fetchUser()
  }

  const isAuthenticated = !!user

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook to access auth context
 */
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
