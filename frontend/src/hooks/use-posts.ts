import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Post, PostStatus, PostVisibility } from '@/types'
import { format } from 'date-fns'

interface CreatePostData {
  account_id: string
  media_id: string
  caption: string
  visibility: PostVisibility
  scheduled_time: string
}

interface UpdatePostData {
  title?: string
  description?: string
  privacy_level?: PostVisibility
  scheduled_time?: string
  hashtags?: string[]
}

/**
 * Backend PostListOut response type
 */
interface PostListResponse {
  items: Post[]
  total: number
  page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

/**
 * Fetch posts for a specific date
 */
export function usePosts(date?: Date) {
  const dateParam = date ? format(date, 'yyyy-MM-dd') : undefined

  return useQuery({
    queryKey: ['posts', dateParam],
    queryFn: async () => {
      const response = await apiClient.get<PostListResponse>('/posts/', {
        params: dateParam ? { from_date: dateParam, to_date: dateParam } : undefined,
      })
      return response.data.items || []
    },
    refetchInterval: 15000, // Refetch every 15 seconds
  })
}

/**
 * Fetch single post by ID
 */
export function usePost(postId: string) {
  return useQuery({
    queryKey: ['post', postId],
    queryFn: async () => {
      const response = await apiClient.get<Post>(`/posts/${postId}`)
      return response.data
    },
    enabled: !!postId,
  })
}

/**
 * Create new post
 * Transforms frontend data format to backend-compatible format
 */
export function useCreatePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: CreatePostData) => {
      // Transform to backend format
      const backendData = {
        title: data.caption.slice(0, 150), // Use caption as title (max 150 chars)
        description: data.caption,
        account_ids: [data.account_id], // Convert single to array
        scheduled_time: data.scheduled_time,
        privacy_level: data.visibility, // Map visibility to privacy_level
        media_ids: [data.media_id], // Link existing media from upload
      }
      const response = await apiClient.post<Post>('/posts/', backendData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })
}

/**
 * Update existing post
 */
export function useUpdatePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ postId, data }: { postId: string; data: UpdatePostData }) => {
      const response = await apiClient.put<Post>(`/posts/${postId}`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post', variables.postId] })
    },
  })
}

/**
 * Delete post
 */
export function useDeletePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (postId: string) => {
      await apiClient.delete(`/posts/${postId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })
}

/**
 * Upload media file response type
 */
interface UploadMediaResponse {
  media_id: string
  file_name: string
  file_size: number
  media_type: 'video' | 'image'
  duration?: number
  thumbnail_url?: string
  file_path: string
  message: string
}

/**
 * Upload media file
 */
export function useUploadMedia() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      // Determine media type based on file
      const mediaType = file.type.startsWith('video/') ? 'video' : 'image'
      formData.append('media_type', mediaType)

      const response = await apiClient.post<UploadMediaResponse>('/media/upload/simple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      // Return standardized response for compatibility
      return {
        id: response.data.media_id,
        url: response.data.thumbnail_url || response.data.file_path,
        ...response.data
      }
    },
  })
}

/**
 * Photo post creation data
 */
interface CreatePhotoPostData {
  title: string
  description: string
  account_ids: string[]
  images: Array<{ file_path: string; order: number }>
  cover_index?: number
  scheduled_time?: string
  privacy_level: PostVisibility
  disable_comment?: boolean
  hashtags?: string[]
  is_draft?: boolean
}

/**
 * Create photo post (1-35 images)
 */
export function useCreatePhotoPost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: CreatePhotoPostData) => {
      const response = await apiClient.post<Post>('/posts/photo', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })
}

/**
 * Upload multiple images and return their file paths
 */
export function useUploadMultipleImages() {
  const uploadMedia = useUploadMedia()

  return useMutation({
    mutationFn: async (files: File[]) => {
      const results = await Promise.all(
        files.map(async (file, index) => {
          const result = await uploadMedia.mutateAsync(file)
          return {
            file_path: result.file_path,
            order: index,
            thumbnail_url: result.thumbnail_url || result.url,
          }
        })
      )
      return results
    },
  })
}
