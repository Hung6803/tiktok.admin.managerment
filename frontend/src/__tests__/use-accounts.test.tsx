import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAccounts } from '@/hooks/use-accounts'
import '@testing-library/jest-dom'
import { ReactNode } from 'react'

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  }
}))

import { apiClient } from '@/lib/api-client'

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>

describe('useAccounts Hook', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('fetches accounts successfully', async () => {
    const mockAccounts = [
      { id: '1', username: 'testuser', display_name: 'Test Account', is_active: true }
    ]

    mockApiClient.get.mockResolvedValueOnce({
      data: { accounts: mockAccounts }
    })

    const { result } = renderHook(() => useAccounts(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0].username).toBe('testuser')
  })

  it('handles fetch error', async () => {
    mockApiClient.get.mockRejectedValueOnce(new Error('Failed to fetch'))

    const { result } = renderHook(() => useAccounts(), { wrapper })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeTruthy()
  })
})