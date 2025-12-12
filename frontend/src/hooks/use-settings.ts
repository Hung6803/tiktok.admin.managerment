import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { UserProfileUpdate, PasswordChangeRequest, SettingsUpdateResponse } from '@/types'
import { useAuth } from '@/lib/auth-context'

/**
 * Update user profile settings (username, timezone)
 */
export function useUpdateProfile() {
  const { refreshUser } = useAuth()

  return useMutation({
    mutationFn: async (data: UserProfileUpdate) => {
      const response = await apiClient.put<SettingsUpdateResponse>('/auth/profile', data)
      return response.data
    },
    onSuccess: async () => {
      await refreshUser()
    },
  })
}

/**
 * Change user password
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: PasswordChangeRequest) => {
      const response = await apiClient.post<{ message: string }>('/auth/password', data)
      return response.data
    },
  })
}

/**
 * Common timezones for selection
 */
export const COMMON_TIMEZONES = [
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
  { value: 'America/New_York', label: 'Eastern Time (US & Canada)' },
  { value: 'America/Chicago', label: 'Central Time (US & Canada)' },
  { value: 'America/Denver', label: 'Mountain Time (US & Canada)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US & Canada)' },
  { value: 'America/Sao_Paulo', label: 'Brasilia Time' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Central European Time' },
  { value: 'Europe/Moscow', label: 'Moscow Time' },
  { value: 'Asia/Dubai', label: 'Dubai (Gulf Standard Time)' },
  { value: 'Asia/Kolkata', label: 'India Standard Time' },
  { value: 'Asia/Bangkok', label: 'Bangkok (Indochina Time)' },
  { value: 'Asia/Ho_Chi_Minh', label: 'Ho Chi Minh City (Indochina Time)' },
  { value: 'Asia/Singapore', label: 'Singapore Time' },
  { value: 'Asia/Shanghai', label: 'China Standard Time' },
  { value: 'Asia/Tokyo', label: 'Japan Standard Time' },
  { value: 'Asia/Seoul', label: 'Korea Standard Time' },
  { value: 'Australia/Sydney', label: 'Australian Eastern Time' },
  { value: 'Pacific/Auckland', label: 'New Zealand Time' },
]
