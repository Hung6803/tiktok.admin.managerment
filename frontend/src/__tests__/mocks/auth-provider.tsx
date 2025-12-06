import React from 'react'
import { AuthContext } from '@/lib/auth-context'

export const mockAuthContextValue = {
  user: { id: '123', email: 'test@example.com' },
  login: jest.fn(),
  logout: jest.fn(),
  isAuthenticated: true
}

export const MockAuthProvider: React.FC<{children: React.ReactNode}> = ({ children }) => (
  <AuthContext.Provider value={mockAuthContextValue}>
    {children}
  </AuthContext.Provider>
)