'use client'

import { useState } from 'react'
import { Calendar } from '@/components/ui/calendar'
import { PostForm } from '@/components/posts/post-form'
import { PostCard } from '@/components/posts/post-card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { usePosts } from '@/hooks/use-posts'
import { format } from 'date-fns'
import { Plus, Calendar as CalendarIcon } from 'lucide-react'

/**
 * Post scheduling page
 * Displays calendar view and scheduled posts
 */
export default function SchedulePage() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())
  const [showForm, setShowForm] = useState(false)

  const { data: posts, isLoading } = usePosts(selectedDate)

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Schedule Posts</h1>
          <p className="text-gray-600 mt-1">Plan and schedule your TikTok content</p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Schedule New Post
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Calendar Section */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-4">
              <CalendarIcon className="h-5 w-5 text-gray-600" />
              <h2 className="font-semibold">Calendar</h2>
            </div>
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
              className="rounded-md"
            />
          </div>
        </div>

        {/* Posts List Section */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">
              Posts for {format(selectedDate, 'MMMM d, yyyy')}
            </h2>

            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-4 border rounded-lg space-y-3">
                    <div className="flex items-center gap-2">
                      <Skeleton className="h-5 w-20" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-32 w-full" />
                  </div>
                ))}
              </div>
            ) : posts && posts.length === 0 ? (
              <div className="text-center py-12">
                <div className="h-16 w-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CalendarIcon className="h-8 w-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">No posts scheduled</h3>
                <p className="text-gray-600 mb-4">
                  No posts are scheduled for this date
                </p>
                <Button onClick={() => setShowForm(true)} variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Schedule a Post
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {posts?.map((post) => (
                  <PostCard key={post.id} post={post} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <PostForm
        open={showForm}
        onClose={() => setShowForm(false)}
        selectedDate={selectedDate}
      />
    </div>
  )
}
