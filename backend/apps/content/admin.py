"""
Django admin for content management
"""
from django.contrib import admin
from .models import ScheduledPost, PostMedia, PublishHistory


@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    """Admin interface for Scheduled Post model"""
    
    list_display = [
        'tiktok_account', 'status', 'scheduled_time',
        'published_at', 'retry_count', 'created_at'
    ]
    list_filter = ['status', 'privacy_level', 'is_deleted', 'scheduled_time']
    search_fields = ['caption', 'tiktok_account__username', 'tiktok_video_id']
    readonly_fields = [
        'id', 'published_at', 'tiktok_video_id', 'video_url',
        'retry_count', 'created_at', 'updated_at'
    ]
    ordering = ['-scheduled_time']
    
    fieldsets = (
        ('Post Info', {
            'fields': ('id', 'tiktok_account', 'status', 'caption', 'hashtags', 'mentions', 'privacy_level')
        }),
        ('Scheduling', {
            'fields': ('scheduled_time', 'timezone')
        }),
        ('Publishing', {
            'fields': ('published_at', 'tiktok_video_id', 'video_url')
        }),
        ('Error Tracking', {
            'fields': ('error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    """Admin interface for Post Media model"""
    
    list_display = [
        'scheduled_post', 'media_type', 'file_size',
        'duration', 'is_processed', 'created_at'
    ]
    list_filter = ['media_type', 'is_processed', 'created_at']
    search_fields = ['scheduled_post__caption', 'file_path']
    readonly_fields = ['id', 'file_size', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(PublishHistory)
class PublishHistoryAdmin(admin.ModelAdmin):
    """Admin interface for Publish History model"""
    
    list_display = [
        'scheduled_post', 'attempt_number', 'success',
        'started_at', 'completed_at', 'http_status'
    ]
    list_filter = ['success', 'started_at']
    search_fields = ['scheduled_post__caption', 'error_code', 'error_message']
    readonly_fields = [
        'id', 'scheduled_post', 'attempt_number', 'started_at',
        'completed_at', 'success', 'error_code', 'error_message',
        'api_response', 'http_status', 'created_at'
    ]
    ordering = ['-started_at']
