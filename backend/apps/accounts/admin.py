"""
Django admin configuration for accounts app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for User model
    """
    list_display = ['email', 'username', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_active', 'is_email_verified', 'is_deleted']
    search_fields = ['email', 'username']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('timezone', 'is_email_verified', 'last_login_ip',
                      'is_deleted', 'deleted_at')
        }),
    )
