"""
Audit log model for tracking system activity
"""
from django.db import models
from .base_model import BaseModel


class AuditLog(BaseModel):
    """
    System activity audit trail
    Tracks all user actions for debugging, compliance, and security
    """

    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('publish', 'Publish'),
        ('schedule', 'Schedule'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text="User who performed the action"
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Type of action performed"
    )
    resource_type = models.CharField(
        max_length=100,
        help_text="Type of resource affected (e.g., 'TikTokAccount', 'ScheduledPost')"
    )
    resource_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the affected resource"
    )

    ip_address = models.GenericIPAddressField(
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="Browser user agent string"
    )

    changes = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON of changes made (before/after)"
    )
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional metadata about the action"
    )

    class Meta:
        app_label = 'core'  # Moved to core app
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', 'created_at']),
        ]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        user_str = self.user.email if self.user else "Anonymous"
        return f"{user_str} - {self.action} - {self.resource_type}"
