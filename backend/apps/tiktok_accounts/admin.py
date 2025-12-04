"""
Django admin for TikTok accounts
"""
from django.contrib import admin
from .models import TikTokAccount


@admin.register(TikTokAccount)
class TikTokAccountAdmin(admin.ModelAdmin):
    """Admin interface for TikTok Account model"""
    
    list_display = [
        'username', 'tiktok_user_id', 'user', 'status',
        'follower_count', 'video_count', 'last_synced_at', 'created_at'
    ]
    list_filter = ['status', 'is_deleted', 'created_at']
    search_fields = ['username', 'tiktok_user_id', 'display_name', 'user__email']
    readonly_fields = [
        'id', 'tiktok_user_id',
        'created_at', 'updated_at', 'deleted_at'
    ]
    exclude = ['access_token', 'refresh_token']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Account Info', {
            'fields': ('id', 'user', 'tiktok_user_id', 'username', 'display_name', 'avatar_url', 'status')
        }),
        ('Token Status', {
            'fields': ('token_expires_at',),
            'description': 'OAuth tokens are encrypted and hidden for security'
        }),
        ('Metrics', {
            'fields': ('follower_count', 'following_count', 'video_count', 'last_synced_at')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
