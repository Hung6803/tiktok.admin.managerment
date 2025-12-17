'use client'

import { Post, PostStatus, PostType } from '@/types'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Trash2, Edit, Clock, Video, Users, ImageIcon, Images } from 'lucide-react'
import { useDeletePost } from '@/hooks/use-posts'
import { format } from 'date-fns'
import { useState } from 'react'
import DOMPurify from 'dompurify'

// Media files are served at /media/, not /api/v1/media/
// Extract base server URL without /api/v1 path
const getMediaBaseUrl = () => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
  // Remove /api/v1 suffix if present to get root server URL
  return apiUrl.replace(/\/api\/v1\/?$/, '')
}
const MEDIA_BASE_URL = getMediaBaseUrl()

interface PostCardProps {
  post: Post
  onEdit?: (post: Post) => void
}

const statusConfig: Record<string, { variant: 'secondary' | 'default' | 'warning' | 'success' | 'destructive' | 'outline'; label: string }> = {
  [PostStatus.DRAFT]: { variant: 'secondary', label: 'Draft' },
  [PostStatus.SCHEDULED]: { variant: 'default', label: 'Scheduled' },
  [PostStatus.PENDING]: { variant: 'secondary', label: 'Pending' },
  [PostStatus.PUBLISHING]: { variant: 'warning', label: 'Publishing' },
  [PostStatus.PUBLISHED]: { variant: 'success', label: 'Published' },
  [PostStatus.FAILED]: { variant: 'destructive', label: 'Failed' },
  [PostStatus.CANCELLED]: { variant: 'outline', label: 'Cancelled' },
}

/**
 * Post card component
 * Displays scheduled post information
 */
export function PostCard({ post, onEdit }: PostCardProps) {
  const deletePost = useDeletePost()
  const [showConfirm, setShowConfirm] = useState(false)

  const handleDelete = async () => {
    if (!showConfirm) {
      setShowConfirm(true)
      setTimeout(() => setShowConfirm(false), 3000)
      return
    }

    try {
      await deletePost.mutateAsync(post.id)
    } catch (error) {
      console.error('Failed to delete post:', error)
    }
  }

  const statusInfo = statusConfig[post.status] || statusConfig[PostStatus.DRAFT]

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <Users className="h-3 w-3" />
                {post.account_count} account{post.account_count !== 1 ? 's' : ''}
              </span>
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <ImageIcon className="h-3 w-3" />
                {post.media_count} media
              </span>
            </div>
            <CardTitle
              className="text-base line-clamp-2"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(post.title) }}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="relative aspect-video bg-gray-100 rounded-md overflow-hidden mb-4">
          {post.thumbnail_url ? (
            <>
              <img
                src={`${MEDIA_BASE_URL}${post.thumbnail_url}`}
                alt={post.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Hide image on error, show fallback icon
                  e.currentTarget.style.display = 'none'
                  e.currentTarget.nextElementSibling?.classList.remove('hidden')
                }}
              />
              <div className="hidden flex items-center justify-center h-full absolute inset-0">
                {post.post_type === PostType.PHOTO ? (
                  <Images className="h-12 w-12 text-gray-400" />
                ) : (
                  <Video className="h-12 w-12 text-gray-400" />
                )}
              </div>
              {/* Post type indicator badge */}
              <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                {post.post_type === PostType.PHOTO ? (
                  <>
                    <Images className="h-3 w-3" />
                    {post.media_count} photo{post.media_count !== 1 ? 's' : ''}
                  </>
                ) : post.post_type === PostType.SLIDESHOW ? (
                  <>
                    <Images className="h-3 w-3" />
                    Slideshow
                  </>
                ) : (
                  <>
                    <Video className="h-3 w-3" />
                    Video
                  </>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              {post.post_type === PostType.PHOTO ? (
                <Images className="h-12 w-12 text-gray-400" />
              ) : (
                <Video className="h-12 w-12 text-gray-400" />
              )}
            </div>
          )}
        </div>

        {post.description && (
          <p
            className="text-sm text-gray-600 line-clamp-3 mb-4"
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(post.description) }}
          />
        )}

        {post.scheduled_time && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="h-4 w-4" />
            <span>
              {format(new Date(post.scheduled_time), 'MMM d, yyyy \'at\' h:mm a')}
            </span>
          </div>
        )}

        {post.status === PostStatus.FAILED && post.error_message && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
            <strong>Error:</strong>{' '}
            <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(post.error_message) }} />
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2">
        {post.status === PostStatus.SCHEDULED && onEdit && (
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => onEdit(post)}
          >
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
        )}
        {(post.status === PostStatus.DRAFT || post.status === PostStatus.SCHEDULED || post.status === PostStatus.FAILED) && (
          <Button
            variant={showConfirm ? 'destructive' : 'outline'}
            size="sm"
            onClick={handleDelete}
            disabled={deletePost.isPending}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            {showConfirm ? 'Confirm?' : 'Delete'}
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}
