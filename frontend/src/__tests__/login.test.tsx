import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AxiosError } from 'axios'
import Login from '@/app/(auth)/login/page'
import { AuthProvider } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import '@testing-library/jest-dom'

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  apiClient: {
    post: jest.fn(),
    get: jest.fn(),
  },
  default: {
    post: jest.fn(),
    get: jest.fn(),
  }
}))

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn()
}))

import { apiClient } from '@/lib/api-client'
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>

describe('Login Page', () => {
  const mockPush = jest.fn()

  beforeEach(() => {
    // Mock successful login response
    mockApiClient.post.mockResolvedValue({
      data: {
        access_token: 'fake_token',
        refresh_token: 'fake_refresh',
        user: {
          id: '123',
          email: 'test@example.com',
          username: 'testuser'
        }
      }
    })

    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders login form', () => {
    render(
      <AuthProvider>
        <Login />
      </AuthProvider>
    )

    // Use getByLabelText since inputs have labels
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('handles login error', async () => {
    // Mock API error with proper AxiosError structure
    const axiosError = new AxiosError(
      'Request failed with status code 401',
      '401',
      undefined,
      undefined,
      {
        status: 401,
        statusText: 'Unauthorized',
        data: { message: 'Invalid credentials' },
        headers: {},
        config: {} as any
      }
    )
    mockApiClient.post.mockRejectedValueOnce(axiosError)

    render(
      <AuthProvider>
        <Login />
      </AuthProvider>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const loginButton = screen.getByRole('button', { name: /sign in/i })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
    fireEvent.click(loginButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('submits login successfully', async () => {
    render(
      <AuthProvider>
        <Login />
      </AuthProvider>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const loginButton = screen.getByRole('button', { name: /sign in/i })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(loginButton)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/accounts')
    })
  })
})