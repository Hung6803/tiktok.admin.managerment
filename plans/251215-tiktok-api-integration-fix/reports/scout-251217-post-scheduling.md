# Codebase Scout Report: Post Scheduling UI, Backend Models & Publishing Services

Date: 2025-12-17
Scope: Post scheduling UI, backend models/schemas, TikTok publishing services, media upload
Status: Complete - 40 files identified

## 1. FRONTEND POST SCHEDULING UI COMPONENTS

Primary UI Files:
- frontend/src/components/posts/post-form.tsx - Post creation form (media upload, scheduling, validation)
- frontend/src/components/posts/post-card.tsx - Individual post display card
- frontend/src/app/(dashboard)/schedule/page.tsx - Calendar-based scheduling page

Frontend Hooks:
- frontend/src/hooks/use-posts.ts - React Query hooks (usePosts, useCreatePost, useUploadMedia)
  * Auto-refetch every 15 seconds
  * Handles post CRUD operations

## 2. BACKEND POST/MEDIA DATA MODELS

Core Models:
- backend/apps/content/models/scheduled_post_model.py
  * Main post model with status/type/privacy fields
  * Relations: user, account, media (reverse)
  * Status values: draft, scheduled, pending, publishing, published, failed
  * Post types: video, slideshow, photo

- backend/apps/content/models/post_media_model.py
  * Media files attached to posts
  * Media types: video, image, thumbnail, slideshow_source, slideshow_video
  * Fields: file_path, file_size, file_mime_type

- backend/apps/content/models/publish_history_model.py
  * Publishing attempt audit trail

Migrations:
- 0001_initial.py - Initial schema
- 0005_add_scheduling_fields.py - Add scheduled_time/published_at
- 0006_add_slideshow_fields_to_post_media.py - Slideshow support
- 0010_add_post_type_field.py - Post type enumeration

## 3. BACKEND API SCHEMAS & ROUTERS

Schemas:
- backend/api/posts/schemas.py
  * PostStatus enum (draft, scheduled, pending, publishing, published, failed)
  * PostPrivacy enum (public_to_everyone, mutual_follow_friends, self_only)
  * MediaIn schema (file_path, file_size, file_mime_type)
  * PostIn/PostOut schemas

- backend/api/media/schemas.py
  * Media upload request/response schemas

API Implementation:
- backend/api/posts/post_router.py - Post CRUD endpoints
- backend/api/posts/post_service.py - Business logic (create, update, query by date)
- backend/api/posts/tests/test_posts_api.py - Integration tests
- backend/api/posts/tests/test_post_service.py - Service unit tests
- backend/api/posts/tests/test_slideshow_api.py - Slideshow tests

Media API:
- backend/api/media/router.py - Upload/delete endpoints
- backend/api/media/upload_handler.py - Chunked upload support with local storage
- backend/api/media/processing_service.py - File validation/conversion
- backend/api/media/schemas.py - Upload schemas

## 4. TIKTOK PUBLISHING SERVICES

Direct Publishing:
- backend/apps/content/services/tiktok_publish_service.py
  * Main publishing service
  * Direct Post API + Creator Inbox API fallback
  * Chunked upload for large videos
  * Retry logic with exponential backoff

Media-Specific Publishers:
- backend/apps/content/services/tiktok_photo_service.py - Single image posts
- backend/apps/content/services/tiktok_video_service.py - Video publishing
- backend/apps/content/services/photo_slideshow_service.py - Image-to-video conversion

## 5. CELERY SCHEDULING TASKS

Publishing Tasks:
- backend/apps/scheduler/tasks/publish_post_task.py
  * Main executor task
  * Handles token refresh before publishing
  * Path sanitization (security)
  * Cleanup temp files
  * Retry logic

- backend/apps/scheduler/tasks/check_scheduled_posts_task.py - Poll for due posts
- backend/apps/scheduler/tasks/convert_slideshow_task.py - Slideshow generation
- backend/apps/scheduler/tasks/sync_accounts_task.py - Account sync

Scheduler Config:
- backend/apps/scheduler/apps.py
- backend/apps/scheduler/admin.py

## 6. TESTS

- backend/apps/content/tests/test_post_media_model.py
- backend/apps/content/tests/test_scheduled_post_model.py
- backend/apps/content/tests/test_publish_history_model.py
- backend/apps/content/tests/test_photo_slideshow_service.py
- backend/apps/scheduler/tests/test_scheduler_tasks.py

## ARCHITECTURE SUMMARY

Frontend: User creates post in PostForm -> uploads media -> schedules for time
Backend: Post stored in ScheduledPost + PostMedia models
Scheduler: Celery beat polls for due posts -> publish_post_task executes
Publishing: TikTok service selects handler (video/photo/slideshow) -> posts to API
