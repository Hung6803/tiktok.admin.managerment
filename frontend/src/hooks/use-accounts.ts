import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { TikTokAccount } from '@/types'

/**
 * Fetch all TikTok accounts
 */
export function useAccounts() {
  return useQuery({
    queryKey: ['tiktok-accounts'],
    queryFn: async () => {
      const response = await apiClient.get<{ accounts: TikTokAccount[] }>('/tiktok/accounts')
      return response.data.accounts
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

/**
 * Get TikTok OAuth URL with CSRF protection
 * Generates random state parameter and saves to sessionStorage
 */
export function useGetAuthUrl() {
  return useMutation({
    mutationFn: async () => {
      // Generate random state for OAuth CSRF protection
      const state = generateRandomState()
      sessionStorage.setItem('oauth_state', state)

      const response = await apiClient.get<{ auth_url: string }>('/tiktok/auth/url', {
        params: { state }
      })
      return response.data.auth_url
    },
  })
}

/**
 * Generate cryptographically secure random state for OAuth
 */
function generateRandomState(): string {
  const array = new Uint8Array(32)
  if (typeof window !== 'undefined' && window.crypto) {
    window.crypto.getRandomValues(array)
  } else {
    // Fallback for SSR (should not be used for OAuth)
    for (let i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256)
    }
  }
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * Delete TikTok account
 */
export function useDeleteAccount() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (accountId: string) => {
      await apiClient.delete(`/tiktok/accounts/${accountId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tiktok-accounts'] })
    },
  })
}

/**
 * Sync TikTok account data
 */
export function useSyncAccount() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (accountId: string) => {
      const response = await apiClient.post(`/tiktok/accounts/${accountId}/sync`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tiktok-accounts'] })
    },
  })
}
