'use client'

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { AnalyticsTimeSeries } from '@/types'
import { format } from 'date-fns'

interface ChartCardProps {
  title: string
  data: AnalyticsTimeSeries | undefined
  loading?: boolean
  icon?: React.ReactNode
}

/**
 * Chart card component for analytics visualization
 * Displays time series data as a simple line chart
 */
export function ChartCard({ title, data, loading, icon }: ChartCardProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {icon}
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="animate-pulse text-gray-400">Loading chart...</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {icon}
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-gray-400">
            No data available
          </div>
        </CardContent>
      </Card>
    )
  }

  const maxValue = Math.max(...data.data.map(d => d.value))
  const minValue = Math.min(...data.data.map(d => d.value))
  const range = maxValue - minValue || 1

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          {/* Simple SVG line chart */}
          <svg className="w-full h-full" viewBox="0 0 600 200">
            {/* Grid lines */}
            <line x1="0" y1="0" x2="600" y2="0" stroke="#e5e7eb" strokeWidth="1" />
            <line x1="0" y1="50" x2="600" y2="50" stroke="#e5e7eb" strokeWidth="1" />
            <line x1="0" y1="100" x2="600" y2="100" stroke="#e5e7eb" strokeWidth="1" />
            <line x1="0" y1="150" x2="600" y2="150" stroke="#e5e7eb" strokeWidth="1" />
            <line x1="0" y1="200" x2="600" y2="200" stroke="#e5e7eb" strokeWidth="1" />

            {/* Line chart */}
            <polyline
              fill="none"
              stroke="#3b82f6"
              strokeWidth="2"
              points={data.data
                .map((point, i) => {
                  const x = (i / (data.data.length - 1)) * 600
                  const y = 200 - ((point.value - minValue) / range) * 180 - 10
                  return `${x},${y}`
                })
                .join(' ')}
            />

            {/* Data points */}
            {data.data.map((point, i) => {
              const x = (i / (data.data.length - 1)) * 600
              const y = 200 - ((point.value - minValue) / range) * 180 - 10
              return (
                <g key={i}>
                  <circle cx={x} cy={y} r="3" fill="#3b82f6" />
                  <title>{`${format(new Date(point.date), 'MMM d')}: ${point.value}`}</title>
                </g>
              )
            })}
          </svg>

          {/* Legend */}
          <div className="flex justify-between text-xs text-gray-600 mt-2">
            <span>{format(new Date(data.data[0].date), 'MMM d')}</span>
            <span>{format(new Date(data.data[data.data.length - 1].date), 'MMM d')}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
