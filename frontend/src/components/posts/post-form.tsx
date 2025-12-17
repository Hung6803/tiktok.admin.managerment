'use client'

import { useState, useCallback, useRef } from 'react'
import { AxiosError } from 'axios'
import { useForm } from 'react-hook-form'
import { useAccounts } from '@/hooks/use-accounts'
import { useCreatePost, useUploadMedia, useCreatePhotoPost, useUploadMultipleImages } from '@/hooks/use-posts'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { PostVisibility } from '@/types'
import { Upload, X, Video, Image as ImageIcon, Star } from 'lucide-react'
import { formatFileSize } from '@/lib/utils'

interface PostFormProps {
  open: boolean
  onClose: () => void
  selectedDate?: Date
}

type PostType = 'video' | 'images'

interface FormData {
  account_id: string
  caption: string
  visibility: PostVisibility
  scheduled_time: string
}

interface UploadedImage {
  file: File
  preview: string
  file_path?: string
  order: number
}

/**
 * Post creation form component
 * Supports both video and photo (1-35 images) posts
 */
export function PostForm({ open, onClose, selectedDate }: PostFormProps) {
  const { data: accounts } = useAccounts()
  const createPost = useCreatePost()
  const uploadMedia = useUploadMedia()
  const createPhotoPost = useCreatePhotoPost()
  const uploadMultipleImages = useUploadMultipleImages()

  const [postType, setPostType] = useState<PostType>('video')
  const [error, setError] = useState('')
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)

  // Video state
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const videoInputRef = useRef<HTMLInputElement>(null)

  // Images state
  const [images, setImages] = useState<UploadedImage[]>([])
  const [coverIndex, setCoverIndex] = useState(0)
  const imageInputRef = useRef<HTMLInputElement>(null)

  const { register, handleSubmit, formState: { errors }, reset } = useForm<FormData>({
    defaultValues: {
      visibility: PostVisibility.PUBLIC,
      scheduled_time: selectedDate
        ? new Date(selectedDate.getTime() + 2 * 60 * 60 * 1000).toISOString().slice(0, 16)
        : new Date().toISOString().slice(0, 16),
    },
  })

  // Handle video file selection
  const handleVideoSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file size (100MB max)
      if (file.size > 100 * 1024 * 1024) {
        setError('Video file size must be under 100MB')
        return
      }
      // Validate file type
      const allowedTypes = ['video/mp4', 'video/quicktime', 'video/webm', 'video/x-msvideo']
      if (!allowedTypes.includes(file.type)) {
        setError('Only MP4, MOV, WEBM, and AVI videos are allowed')
        return
      }
      setVideoFile(file)
      setError('')
    }
  }, [])

  // Handle image files selection
  const handleImagesSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const newImages: UploadedImage[] = []
    const currentCount = images.length
    const maxImages = 35

    // Validate total count
    if (currentCount + files.length > maxImages) {
      setError(`Maximum ${maxImages} images allowed. You can add ${maxImages - currentCount} more.`)
      return
    }

    Array.from(files).forEach((file, index) => {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
      if (!allowedTypes.includes(file.type)) {
        setError('Only JPG, PNG, and WebP images are allowed')
        return
      }
      // Validate file size (20MB max per image)
      if (file.size > 20 * 1024 * 1024) {
        setError('Each image must be under 20MB')
        return
      }

      newImages.push({
        file,
        preview: URL.createObjectURL(file),
        order: currentCount + index,
      })
    })

    setImages(prev => [...prev, ...newImages])
    setError('')

    // Reset input to allow selecting same files again
    if (imageInputRef.current) {
      imageInputRef.current.value = ''
    }
  }, [images.length])

  // Remove an image
  const removeImage = useCallback((index: number) => {
    setImages(prev => {
      const updated = prev.filter((_, i) => i !== index)
      // Reorder remaining images
      return updated.map((img, i) => ({ ...img, order: i }))
    })
    // Adjust cover index if needed
    if (coverIndex >= index && coverIndex > 0) {
      setCoverIndex(prev => prev - 1)
    }
  }, [coverIndex])

  // Set cover image
  const selectCover = useCallback((index: number) => {
    setCoverIndex(index)
  }, [])

  // Clear video
  const clearVideo = useCallback(() => {
    setVideoFile(null)
    if (videoInputRef.current) {
      videoInputRef.current.value = ''
    }
  }, [])

  // Reset form
  const resetForm = useCallback(() => {
    reset()
    setVideoFile(null)
    setImages([])
    setCoverIndex(0)
    setError('')
    setUploadProgress(null)
    setPostType('video')
  }, [reset])

  const onSubmit = async (data: FormData) => {
    setError('')

    if (postType === 'video') {
      // Video post submission
      if (!videoFile) {
        setError('Please select a video file')
        return
      }

      try {
        setUploadProgress(0)
        const mediaData = await uploadMedia.mutateAsync(videoFile)
        setUploadProgress(100)

        await createPost.mutateAsync({
          account_id: data.account_id,
          media_id: mediaData.id,
          caption: data.caption,
          visibility: data.visibility,
          scheduled_time: new Date(data.scheduled_time).toISOString(),
        })

        resetForm()
        onClose()
      } catch (err) {
        handleError(err)
      }
    } else {
      // Photo post submission
      if (images.length === 0) {
        setError('Please select at least one image')
        return
      }

      try {
        setUploadProgress(0)

        // Upload all images
        const files = images.map(img => img.file)
        const uploadedImages = await uploadMultipleImages.mutateAsync(files)
        setUploadProgress(50)

        // Create photo post
        await createPhotoPost.mutateAsync({
          title: data.caption.slice(0, 150),
          description: data.caption,
          account_ids: [data.account_id],
          images: uploadedImages.map((img, index) => ({
            file_path: img.file_path,
            order: index,
          })),
          cover_index: coverIndex,
          scheduled_time: new Date(data.scheduled_time).toISOString(),
          privacy_level: data.visibility,
          disable_comment: false,
          hashtags: [],
          is_draft: false,
        })
        setUploadProgress(100)

        resetForm()
        onClose()
      } catch (err) {
        handleError(err)
      }
    }
  }

  const handleError = (err: unknown) => {
    if (err instanceof AxiosError) {
      const errorMessage = err.response?.data?.message || err.response?.data?.detail || 'Failed to create post'
      setError(errorMessage)
    } else if (err instanceof Error) {
      setError(err.message)
    } else {
      setError('Failed to create post')
    }
    setUploadProgress(null)
  }

  const isSubmitting = createPost.isPending || uploadMedia.isPending ||
                       createPhotoPost.isPending || uploadMultipleImages.isPending

  return (
    <Dialog open={open} onOpenChange={() => { resetForm(); onClose() }}>
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

          {/* Post Type Tabs */}
          <Tabs className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger
                type="button"
                data-state={postType === 'video' ? 'active' : 'inactive'}
                onClick={() => setPostType('video')}
                className="flex items-center gap-2"
              >
                <Video className="h-4 w-4" />
                Video
              </TabsTrigger>
              <TabsTrigger
                type="button"
                data-state={postType === 'images' ? 'active' : 'inactive'}
                onClick={() => setPostType('images')}
                className="flex items-center gap-2"
              >
                <ImageIcon className="h-4 w-4" />
                Images (1-35)
              </TabsTrigger>
            </TabsList>

            {/* Video Tab Content */}
            <TabsContent data-state={postType === 'video' ? 'active' : 'inactive'} hidden={postType !== 'video'}>
              <div className="space-y-2">
                <Label>Video File *</Label>
                <div className="flex items-center gap-2">
                  <input
                    ref={videoInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleVideoSelect}
                    className="hidden"
                    id="video-upload"
                  />
                  <label
                    htmlFor="video-upload"
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50"
                  >
                    <Upload className="h-4 w-4" />
                    Select Video
                  </label>
                  {videoFile && (
                    <Button type="button" variant="ghost" size="sm" onClick={clearVideo}>
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
                {videoFile && (
                  <p className="text-sm text-gray-600">
                    {videoFile.name} ({formatFileSize(videoFile.size)})
                  </p>
                )}
              </div>
            </TabsContent>

            {/* Images Tab Content */}
            <TabsContent data-state={postType === 'images' ? 'active' : 'inactive'} hidden={postType !== 'images'}>
              <div className="space-y-3">
                <Label>Images * (1-35 photos)</Label>
                <div className="flex items-center gap-2">
                  <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    multiple
                    onChange={handleImagesSelect}
                    className="hidden"
                    id="images-upload"
                  />
                  <label
                    htmlFor="images-upload"
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50"
                  >
                    <Upload className="h-4 w-4" />
                    Add Images
                  </label>
                  <span className="text-sm text-gray-500">
                    {images.length}/35 images
                  </span>
                </div>

                {/* Image Preview Grid */}
                {images.length > 0 && (
                  <div className="grid grid-cols-4 gap-2">
                    {images.map((img, index) => (
                      <div
                        key={index}
                        className={`relative group aspect-square rounded-md overflow-hidden border-2 cursor-pointer
                          ${index === coverIndex ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'}`}
                        onClick={() => selectCover(index)}
                      >
                        <img
                          src={img.preview}
                          alt={`Preview ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                        {/* Cover badge */}
                        {index === coverIndex && (
                          <div className="absolute top-1 left-1 bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded flex items-center gap-1">
                            <Star className="h-3 w-3 fill-current" />
                            Cover
                          </div>
                        )}
                        {/* Remove button */}
                        <button
                          type="button"
                          onClick={(e) => { e.stopPropagation(); removeImage(index) }}
                          className="absolute top-1 right-1 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="h-3 w-3" />
                        </button>
                        {/* Order number */}
                        <div className="absolute bottom-1 right-1 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded">
                          {index + 1}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {images.length > 0 && (
                  <p className="text-xs text-gray-500">
                    Click on an image to set it as cover photo
                  </p>
                )}
              </div>
            </TabsContent>
          </Tabs>

          {/* Upload Progress */}
          {uploadProgress !== null && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="caption">Caption *</Label>
            <textarea
              id="caption"
              rows={4}
              className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
              placeholder={postType === 'video' ? 'Write a caption for your video...' : 'Write a caption for your photos...'}
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
            <Button type="button" variant="outline" onClick={() => { resetForm(); onClose() }} className="flex-1">
              Cancel
            </Button>
            <Button
              type="submit"
              className="flex-1"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                uploadProgress !== null && uploadProgress < 100 ? 'Uploading...' : 'Creating...'
              ) : (
                `Schedule ${postType === 'video' ? 'Video' : 'Photo'} Post`
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
