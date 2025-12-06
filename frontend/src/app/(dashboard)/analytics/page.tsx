'use client'

import React, { useState } from 'react'
import { useAccounts } from '@/hooks/use-accounts'
import { useAccountMetrics, useAccountTimeSeries } from '@/hooks/use-analytics'
import { StatsDashboard } from '@/components/analytics/stats-dashboard'
import { ChartCard } from '@/components/analytics/chart-card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Users, Heart, Eye, TrendingUp } from 'lucide-react'

/**
 * Analytics dashboard page
 * Displays metrics and charts for selected account
 */
export default function AnalyticsPage() {
  const { data: accounts } = useAccounts()
  const [selectedAccountId, setSelectedAccountId] = useState<string>('')
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('week')

  // Auto-select first account when loaded (moved to useEffect to fix state update during render)
  React.useEffect(() => {
    if (!selectedAccountId && accounts && accounts.length > 0) {
      setSelectedAccountId(accounts[0].id)
    }
  }, [accounts, selectedAccountId])

  const { data: metrics, isLoading: metricsLoading } = useAccountMetrics(selectedAccountId)
  const { data: followersData, isLoading: followersLoading } = useAccountTimeSeries(
    selectedAccountId,
    'followers',
    period
  )
  const { data: viewsData, isLoading: viewsLoading } = useAccountTimeSeries(
    selectedAccountId,
    'views',
    period
  )
  const { data: likesData, isLoading: likesLoading } = useAccountTimeSeries(
    selectedAccountId,
    'likes',
    period
  )
  const { data: engagementData, isLoading: engagementLoading } = useAccountTimeSeries(
    selectedAccountId,
    'engagement',
    period
  )

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">Track your TikTok performance</p>
        </div>

        <div className="flex gap-3">
          {/* Account selector */}
          <select
            value={selectedAccountId}
            onChange={(e) => setSelectedAccountId(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md bg-white"
          >
            {accounts?.map((account) => (
              <option key={account.id} value={account.id}>
                @{account.username}
              </option>
            ))}
          </select>

          {/* Period selector */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as 'day' | 'week' | 'month')}
            className="px-4 py-2 border border-gray-300 rounded-md bg-white"
          >
            <option value="day">Daily</option>
            <option value="week">Weekly</option>
            <option value="month">Monthly</option>
          </select>
        </div>
      </div>

      {/* Stats Overview */}
      <StatsDashboard metrics={metrics} loading={metricsLoading} />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Followers Growth"
          data={followersData}
          loading={followersLoading}
          icon={<Users className="h-5 w-5 text-blue-600" />}
        />
        <ChartCard
          title="Views Trend"
          data={viewsData}
          loading={viewsLoading}
          icon={<Eye className="h-5 w-5 text-purple-600" />}
        />
        <ChartCard
          title="Likes Trend"
          data={likesData}
          loading={likesLoading}
          icon={<Heart className="h-5 w-5 text-red-600" />}
        />
        <ChartCard
          title="Engagement Rate"
          data={engagementData}
          loading={engagementLoading}
          icon={<TrendingUp className="h-5 w-5 text-green-600" />}
        />
      </div>

      {/* Additional Info */}
      {accounts && accounts.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold mb-2">No accounts connected</h3>
          <p className="text-gray-600">
            Connect a TikTok account to view analytics
          </p>
        </div>
      )}
    </div>
  )
}
