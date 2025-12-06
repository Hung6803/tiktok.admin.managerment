import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { Sidebar } from '@/components/dashboard/sidebar'
import { AuthProvider } from '@/lib/auth-context'
import '@testing-library/jest-dom'

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  }
}))

// Mock the router context
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/accounts'),
  useRouter: jest.fn(() => ({
    push: jest.fn(),
  })),
}))

import { apiClient } from '@/lib/api-client'
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>

describe('Dashboard Sidebar', () => {
  const mockUser = {
    id: '123',
    email: 'test@example.com',
    username: 'testuser'
  }

  beforeEach(() => {
    // Mock access token in localStorage
    global.localStorage.setItem('access_token', 'fake_token')

    // Mock the /auth/me endpoint
    mockApiClient.get.mockResolvedValue({
      data: mockUser
    })
  })

  afterEach(() => {
    global.localStorage.clear()
    jest.clearAllMocks()
  })

  it('renders navigation links', async () => {
    render(
      <AuthProvider>
        <Sidebar />
      </AuthProvider>
    )

    // Wait for auth to load
    await waitFor(() => {
      expect(screen.getByText('Accounts')).toBeInTheDocument()
    })

    // Check for actual menu items from the sidebar
    const links = ['Accounts', 'Schedule', 'Analytics', 'Settings']

    links.forEach(link => {
      expect(screen.getByText(link)).toBeInTheDocument()
    })
  })

  it('highlights active navigation item', async () => {
    render(
      <AuthProvider>
        <Sidebar />
      </AuthProvider>
    )

    // Wait for the component to render
    await waitFor(() => {
      expect(screen.getByText('Accounts')).toBeInTheDocument()
    })

    const accountsLink = screen.getByText('Accounts')

    // Check if the parent link element has the active class (bg-blue-600)
    const linkElement = accountsLink.closest('a')
    expect(linkElement).toHaveClass('bg-blue-600')
  })
})