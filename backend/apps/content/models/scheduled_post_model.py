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
        ('queued', 'In Queue'),
        ('processing', 'Processing'),
        ('published', 'Published'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private'),
    ]

    tiktok_account = models.ForeignKey(
        'tiktok_accounts.TikTokAccount',
        on_delete=models.CASCADE,
        related_name='scheduled_posts',
        help_text="TikTok account to publish to"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text="Current status of the post"
    )

    # Content details
    caption = models.TextField(
        max_length=2200,
        help_text="Post caption (max 2200 chars per TikTok limits)"
    )
    hashtags = models.JSONField(
        default=list,
        help_text="List of hashtags"
    )
    mentions = models.JSONField(
        default=list,
        help_text="List of mentioned users"
    )
    privacy_level = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='public',
        help_text="Post privacy setting"
    )

    # Scheduling
    scheduled_time = models.DateTimeField(
        db_index=True,
        help_text="When to publish the post"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="Timezone for scheduled_time"
    )

    # Publishing metadata
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the post was actually published"
    )
    tiktok_video_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        help_text="TikTok's video ID after publishing"
    )
    video_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL to the published TikTok video"
    )

    # Error tracking
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if publishing failed"
    )
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of times publishing has been retried"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retry attempts"
    )

    class Meta:
        db_table = 'scheduled_posts'
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['status', 'scheduled_time']),
            models.Index(fields=['tiktok_account', 'status']),
        ]
        verbose_name = "Scheduled Post"
        verbose_name_plural = "Scheduled Posts"

    def __str__(self):
        return f"{self.tiktok_account.username} - {self.scheduled_time} ({self.status})"

    def can_retry(self):
        """Check if post can be retried"""
        return self.retry_count < self.max_retries and self.status == 'failed'

    def is_ready_to_publish(self):
        """Check if post is ready to be published"""
        from django.utils import timezone
        return (
            self.status == 'scheduled' and
            self.scheduled_time <= timezone.now() and
            not self.is_deleted
        )
