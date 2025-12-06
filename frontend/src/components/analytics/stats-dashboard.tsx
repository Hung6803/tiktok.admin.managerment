'use client'

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { AnalyticsMetrics } from '@/types'
import { Users, Heart, Eye, TrendingUp } from 'lucide-react'

interface StatsDashboardProps {
  metrics: AnalyticsMetrics | undefined
  loading?: boolean
}

/**
 * Stats dashboard component
 * Displays key analytics metrics in card format
 */
export function StatsDashboard({ metrics, loading }: StatsDashboardProps) {
  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toLocaleString()
  }

  const stats = [
    {
      title: 'Total Followers',
      value: metrics?.follower_count || 0,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Total Likes',
      value: metrics?.likes_total || 0,
      icon: Heart,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      title: 'Total Views',
      value: metrics?.views_total || 0,
      icon: Eye,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Engagement Rate',
      value: metrics?.engagement_rate ? `${(metrics.engagement_rate * 100).toFixed(2)}%` : '0%',
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      raw: true,
    },
  ]

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse space-y-3">
                <div className="h-10 w-10 bg-gray-200 rounded-full" />
                <div className="h-8 w-24 bg-gray-200 rounded" />
                <div className="h-4 w-32 bg-gray-200 rounded" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-3xl font-bold mt-2">
                    {stat.raw ? stat.value : formatNumber(stat.value as number)}
                  </p>
                </div>
                <div className={`p-3 rounded-full ${stat.bgColor}`}>
                  <Icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
