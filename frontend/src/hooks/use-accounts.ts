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
 * Get TikTok OAuth URL
 */
export function useGetAuthUrl() {
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.get<{ auth_url: string }>('/tiktok/auth/url')
      return response.data.auth_url
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
