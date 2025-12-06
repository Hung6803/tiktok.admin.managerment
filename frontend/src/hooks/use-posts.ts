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
  caption?: string
  visibility?: PostVisibility
  scheduled_time?: string
  status?: PostStatus
}

/**
 * Fetch posts for a specific date
 */
export function usePosts(date?: Date) {
  const dateParam = date ? format(date, 'yyyy-MM-dd') : undefined

  return useQuery({
    queryKey: ['posts', dateParam],
    queryFn: async () => {
      const response = await apiClient.get<{ posts: Post[] }>('/posts/', {
        params: dateParam ? { date: dateParam } : undefined,
      })
      return response.data.posts
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
 */
export function useCreatePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: CreatePostData) => {
      const response = await apiClient.post<Post>('/posts/', data)
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
 * Upload media file
 */
export function useUploadMedia() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post<{ id: string; url: string }>('/media/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
  })
}
