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
      const response = await apiClient.get<{ items: TikTokAccount[], total: number, has_more: boolean }>('/accounts/')
      return response.data.items ?? []
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

/**
 * Get TikTok OAuth authorization URL
 * Opens a new window to the backend authorize endpoint with JWT token
 * Backend handles state generation and redirects to TikTok
 */
export function useGetAuthUrl() {
  return useMutation({
    mutationFn: async () => {
      // Get the access token from localStorage
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('Not authenticated')
      }

      // Open authorize URL in same window - token passed via query param
      // Backend will validate token and redirect to TikTok
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      return `${baseUrl}/tiktok/oauth/authorize?token=${encodeURIComponent(token)}`
    },
  })
}

/**
 * Delete TikTok account
 */
export function useDeleteAccount() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (accountId: string) => {
      await apiClient.delete(`/accounts/${accountId}`)
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
      const response = await apiClient.post(`/accounts/${accountId}/sync`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tiktok-accounts'] })
    },
  })
}
