import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { AnalyticsMetrics, AnalyticsTimeSeries } from '@/types'

/**
 * Fetch analytics metrics for an account
 */
export function useAccountMetrics(accountId: string) {
  return useQuery({
    queryKey: ['analytics', 'metrics', accountId],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsMetrics>(
        `/analytics/accounts/${accountId}/metrics`
      )
      return response.data
    },
    enabled: !!accountId,
    refetchInterval: 60000, // Refetch every minute
  })
}

/**
 * Fetch time series data for a specific metric
 */
export function useAccountTimeSeries(
  accountId: string,
  metric: 'followers' | 'views' | 'likes' | 'engagement',
  period: 'day' | 'week' | 'month' = 'week'
) {
  return useQuery({
    queryKey: ['analytics', 'timeseries', accountId, metric, period],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsTimeSeries>(
        `/analytics/accounts/${accountId}/timeseries`,
        {
          params: { metric, period },
        }
      )
      return response.data
    },
    enabled: !!accountId,
  })
}

/**
 * Fetch aggregated metrics across all accounts
 */
export function useAggregatedMetrics() {
  return useQuery({
    queryKey: ['analytics', 'aggregated'],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsMetrics>('/analytics/aggregated')
      return response.data
    },
    refetchInterval: 60000,
  })
}
