'use client'

import { useState } from 'react'
import { AxiosError } from 'axios'
import { useForm } from 'react-hook-form'
import { useAccounts } from '@/hooks/use-accounts'
import { useCreatePost, useUploadMedia } from '@/hooks/use-posts'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PostVisibility } from '@/types'
import { Upload, X } from 'lucide-react'
import { formatFileSize } from '@/lib/utils'

interface PostFormProps {
  open: boolean
  onClose: () => void
  selectedDate?: Date
}

interface FormData {
  account_id: string
  caption: string
  visibility: PostVisibility
  scheduled_time: string
  media_file: FileList | null
}

/**
 * Post creation form component
 * Handles media upload and post scheduling
 */
export function PostForm({ open, onClose, selectedDate }: PostFormProps) {
  const { data: accounts } = useAccounts()
  const createPost = useCreatePost()
  const uploadMedia = useUploadMedia()
  const [error, setError] = useState('')
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)

  const { register, handleSubmit, formState: { errors }, reset, watch } = useForm<FormData>({
    defaultValues: {
      visibility: PostVisibility.PUBLIC,
      scheduled_time: selectedDate
        ? new Date(selectedDate.getTime() + 2 * 60 * 60 * 1000).toISOString().slice(0, 16)
        : new Date().toISOString().slice(0, 16),
    },
  })

  const mediaFile = watch('media_file')
  const selectedFile = mediaFile?.[0]

  const onSubmit = async (data: FormData) => {
    setError('')

    if (!data.media_file || data.media_file.length === 0) {
      setError('Please select a video file')
      return
    }

    try {
      // Upload media first
      setUploadProgress(0)
      const mediaData = await uploadMedia.mutateAsync(data.media_file[0])
      setUploadProgress(100)

      // Create post
      await createPost.mutateAsync({
        account_id: data.account_id,
        media_id: mediaData.id,
        caption: data.caption,
        visibility: data.visibility,
        scheduled_time: new Date(data.scheduled_time).toISOString(),
      })

      reset()
      setUploadProgress(null)
      onClose()
    } catch (err) {
      if (err instanceof AxiosError) {
        const errorMessage = err.response?.data?.message || 'Failed to create post'
        setError(errorMessage)
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to create post')
      }
      setUploadProgress(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Schedule New Post</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="account_id">TikTok Account *</Label>
            <select
              id="account_id"
              className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
              {...register('account_id', { required: 'Please select an account' })}
            >
              <option value="">Select account...</option>
              {accounts?.map((account) => (
                <option key={account.id} value={account.id}>
                  @{account.username} - {account.display_name}
                </option>
              ))}
            </select>
            {errors.account_id && (
              <p className="text-sm text-red-600">{errors.account_id.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="media_file">Video File *</Label>
            <div className="flex items-center gap-2">
              <Input
                id="media_file"
                type="file"
                accept="video/*"
                {...register('media_file', {
                  required: 'Please select a video file',
                  validate: {
                    fileSize: (files) => {
                      if (!files || files.length === 0) return true
                      const file = files[0]
                      const maxSize = 100 * 1024 * 1024 // 100MB
                      return file.size <= maxSize || 'File size must be under 100MB'
                    },
                    fileType: (files) => {
                      if (!files || files.length === 0) return true
                      const file = files[0]
                      const allowedTypes = ['video/mp4', 'video/quicktime', 'video/webm', 'video/x-msvideo']
                      return allowedTypes.includes(file.type) || 'Only MP4, MOV, WEBM, and AVI videos are allowed'
                    }
                  }
                })}
              />
            </div>
            {selectedFile && (
              <p className="text-sm text-gray-600">
                {selectedFile.name} ({formatFileSize(selectedFile.size)})
              </p>
            )}
            {uploadProgress !== null && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
            {errors.media_file && (
              <p className="text-sm text-red-600">{errors.media_file.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="caption">Caption *</Label>
            <textarea
              id="caption"
              rows={4}
              className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
              placeholder="Write a caption for your video..."
              {...register('caption', { required: 'Caption is required' })}
            />
            {errors.caption && (
              <p className="text-sm text-red-600">{errors.caption.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="visibility">Visibility</Label>
            <select
              id="visibility"
              className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
              {...register('visibility')}
            >
              <option value={PostVisibility.PUBLIC}>Public</option>
              <option value={PostVisibility.FRIENDS}>Friends Only</option>
              <option value={PostVisibility.PRIVATE}>Private</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="scheduled_time">Scheduled Time *</Label>
            <Input
              id="scheduled_time"
              type="datetime-local"
              {...register('scheduled_time', { required: 'Scheduled time is required' })}
            />
            {errors.scheduled_time && (
              <p className="text-sm text-red-600">{errors.scheduled_time.message}</p>
            )}
          </div>

          <div className="flex gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button
              type="submit"
              className="flex-1"
              disabled={createPost.isPending || uploadMedia.isPending}
            >
              {uploadMedia.isPending ? 'Uploading...' : createPost.isPending ? 'Creating...' : 'Schedule Post'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
