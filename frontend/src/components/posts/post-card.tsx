'use client'

import { Post, PostStatus } from '@/types'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Trash2, Edit, ExternalLink, Clock, Video } from 'lucide-react'
import { useDeletePost } from '@/hooks/use-posts'
import { format } from 'date-fns'
import { useState } from 'react'
import DOMPurify from 'dompurify'

interface PostCardProps {
  post: Post
  onEdit?: (post: Post) => void
}

const statusConfig = {
  [PostStatus.DRAFT]: { variant: 'secondary' as const, label: 'Draft' },
  [PostStatus.SCHEDULED]: { variant: 'default' as const, label: 'Scheduled' },
  [PostStatus.PUBLISHING]: { variant: 'warning' as const, label: 'Publishing' },
  [PostStatus.PUBLISHED]: { variant: 'success' as const, label: 'Published' },
  [PostStatus.FAILED]: { variant: 'destructive' as const, label: 'Failed' },
  [PostStatus.CANCELLED]: { variant: 'outline' as const, label: 'Cancelled' },
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

  const statusInfo = statusConfig[post.status]

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
              <span className="text-xs text-gray-500">
                @{post.account?.username}
              </span>
            </div>
            <CardTitle
              className="text-base line-clamp-2"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(post.caption) }}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {post.media && (
          <div className="relative aspect-video bg-gray-100 rounded-md overflow-hidden mb-4">
            {post.media.thumbnail_url ? (
              <img
                src={post.media.thumbnail_url}
                alt="Post thumbnail"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <Video className="h-12 w-12 text-gray-400" />
              </div>
            )}
          </div>
        )}

        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Clock className="h-4 w-4" />
          <span>
            {format(new Date(post.scheduled_time), 'MMM d, yyyy \'at\' h:mm a')}
          </span>
        </div>

        {post.status === PostStatus.FAILED && post.last_error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
            <strong>Error:</strong>{' '}
            <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(post.last_error) }} />
          </div>
        )}

        {post.tiktok_share_url && (
          <a
            href={post.tiktok_share_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 flex items-center gap-2 text-sm text-blue-600 hover:underline"
          >
            <ExternalLink className="h-4 w-4" />
            View on TikTok
          </a>
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
