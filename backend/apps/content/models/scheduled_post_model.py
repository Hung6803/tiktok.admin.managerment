"""
Scheduled post model for managing posts scheduled for publishing to TikTok
"""
from django.db import models
from core.models import BaseModel


class ScheduledPost(BaseModel):
    """
    Post scheduled for publishing to TikTok
    Tracks content, scheduling, and publishing status
    """

    class Meta:
        app_label = 'content'

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('pending', 'Pending'),
        ('publishing', 'Publishing'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    ]

    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='posts',
        help_text="User who created the post"
    )
    accounts = models.ManyToManyField(
        'tiktok_accounts.TikTokAccount',
        related_name='scheduled_posts',
        help_text="TikTok accounts to publish to"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text="Current status of the post"
    )

    # Content details
    title = models.CharField(
        max_length=150,
        help_text="Post title (max 150 chars)"
    )
    description = models.TextField(
        max_length=2200,
        help_text="Post description (max 2200 chars per TikTok limits)"
    )
    hashtags = models.JSONField(
        default=list,
        help_text="List of hashtags"
    )
    allow_comments = models.BooleanField(
        default=True,
        help_text="Allow comments on post"
    )
    allow_duet = models.BooleanField(
        default=True,
        help_text="Allow duet with this video"
    )
    allow_stitch = models.BooleanField(
        default=True,
        help_text="Allow stitch with this video"
    )
    privacy_level = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='public',
        help_text="Post privacy setting"
    )

    # Scheduling
    scheduled_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When to publish the post"
    )

    # Publishing metadata
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the post was actually published"
    )

    # Error tracking
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if publishing failed"
    )

    class Meta:
        db_table = 'scheduled_posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'scheduled_time']),
        ]
        verbose_name = "Scheduled Post"
        verbose_name_plural = "Scheduled Posts"

    def __str__(self):
        return f"{self.title} - {self.status}"
