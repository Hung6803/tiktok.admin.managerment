"""
Django admin for analytics
"""
from django.contrib import admin
from .models import AccountAnalytics


@admin.register(AccountAnalytics)
class AccountAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for Account Analytics model"""
    
    list_display = [
        'tiktok_account', 'date', 'follower_count',
        'total_views', 'total_likes', 'engagement_rate'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['tiktok_account__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-date']
    
    fieldsets = (
        ('Account', {
            'fields': ('id', 'tiktok_account', 'date')
        }),
        ('Counts', {
            'fields': ('follower_count', 'following_count', 'video_count')
        }),
        ('Engagement', {
            'fields': ('total_likes', 'total_views', 'total_shares', 'total_comments')
        }),
        ('Growth', {
            'fields': ('follower_growth', 'engagement_rate')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
