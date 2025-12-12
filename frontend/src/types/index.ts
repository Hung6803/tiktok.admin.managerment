/**
 * User account type
 */
export interface User {
  id: string
  email: string
  username: string
  timezone: string
  created_at: string
}

/**
 * TikTok account type
 * SECURITY: access_token and refresh_token removed - never send to frontend
 * Backend manages tokens securely in database
 */
export interface TikTokAccount {
  id: string
  user_id: string
  tiktok_user_id: string
  username: string
  display_name: string
  avatar_url: string
  follower_count: number
  following_count: number
  likes_count: number
  video_count: number
  is_verified: boolean
  is_active: boolean
  token_expires_at: string
  last_synced_at: string | null
  created_at: string
  updated_at: string
}

/**
 * Post status enum
 */
export enum PostStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  PUBLISHING = 'publishing',
  PUBLISHED = 'published',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

/**
 * Post visibility enum
 */
export enum PostVisibility {
  PUBLIC = 'public_to_everyone',
  FRIENDS = 'mutual_follow_friends',
  PRIVATE = 'self_only',
}

/**
 * Media type
 */
export interface Media {
  id: string
  file_url: string
  file_size: number
  mime_type: string
  duration: number | null
  width: number | null
  height: number | null
  thumbnail_url: string | null
  created_at: string
}

/**
 * Post type
 */
export interface Post {
  id: string
  user_id: string
  account_id: string
  account?: TikTokAccount
  media_id: string
  media?: Media
  caption: string
  visibility: PostVisibility
  scheduled_time: string
  status: PostStatus
  tiktok_video_id: string | null
  tiktok_share_url: string | null
  publish_attempts: number
  last_error: string | null
  published_at: string | null
  created_at: string
  updated_at: string
}

/**
 * Analytics metrics type
 */
export interface AnalyticsMetrics {
  follower_count: number
  following_count: number
  likes_count: number
  video_count: number
  views_total: number
  likes_total: number
  comments_total: number
  shares_total: number
  engagement_rate: number
}

/**
 * Time series data point
 */
export interface TimeSeriesDataPoint {
  date: string
  value: number
}

/**
 * Analytics time series response
 */
export interface AnalyticsTimeSeries {
  metric: string
  period: string
  data: TimeSeriesDataPoint[]
}

/**
 * Auth response type
 * SECURITY: Tokens no longer returned in response body
 * Backend sets them as httpOnly cookies instead
 */
export interface AuthResponse {
  user: User
  message?: string
}

/**
 * API error response
 */
export interface APIError {
  message: string
  errors?: Record<string, string[]>
  status?: number
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  data: T[]
  meta: PaginationMeta
}

/**
 * User profile update request
 */
export interface UserProfileUpdate {
  username?: string
  timezone?: string
}

/**
 * Password change request
 */
export interface PasswordChangeRequest {
  current_password: string
  new_password: string
}

/**
 * Settings update response
 */
export interface SettingsUpdateResponse {
  message: string
  user?: User
}
