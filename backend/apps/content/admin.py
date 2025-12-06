"""
Django admin for content management
"""
from django.contrib import admin
from .models import ScheduledPost, PostMedia, PublishHistory


@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    """Admin interface for Scheduled Post model"""

    list_display = [
        'title', 'user', 'status', 'scheduled_time',
        'published_at', 'created_at'
    ]
    list_filter = ['status', 'privacy_level', 'is_deleted', 'scheduled_time']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = [
        'id', 'published_at', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    filter_horizontal = ['accounts']

    fieldsets = (
        ('Post Info', {
            'fields': ('id', 'user', 'title', 'description', 'status', 'hashtags', 'privacy_level')
        }),
        ('Accounts', {
            'fields': ('accounts',)
        }),
        ('Settings', {
            'fields': ('allow_comments', 'allow_duet', 'allow_stitch')
        }),
        ('Scheduling', {
            'fields': ('scheduled_time',)
        }),
        ('Publishing', {
            'fields': ('published_at',)
        }),
        ('Error Tracking', {
            'fields': ('error_message',),
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
        'post', 'media_type', 'file_size',
        'duration', 'is_processed', 'created_at'
    ]
    list_filter = ['media_type', 'is_processed', 'created_at']
    search_fields = ['post__title', 'file_path']
    readonly_fields = ['id', 'file_size', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(PublishHistory)
class PublishHistoryAdmin(admin.ModelAdmin):
    """Admin interface for Publish History model"""

    list_display = [
        'post', 'account', 'status',
        'published_at', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['post__title', 'account__username', 'error_message']
    readonly_fields = [
        'id', 'post', 'account', 'status', 'tiktok_video_id',
        'published_at', 'error_message', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
