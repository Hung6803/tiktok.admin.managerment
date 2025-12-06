"""
Publish history model for tracking publishing attempts and results
"""
from django.db import models
from core.models import BaseModel


class PublishHistory(BaseModel):
    """
    History of publishing attempts for scheduled posts
    Provides audit trail and debugging information
    """

    post = models.ForeignKey(
        'content.ScheduledPost',
        on_delete=models.CASCADE,
        related_name='publish_history',
        help_text="Post that was attempted to publish"
    )
    account = models.ForeignKey(
        'tiktok_accounts.TikTokAccount',
        on_delete=models.CASCADE,
        related_name='publish_history',
        help_text="Account used for publishing"
    )

    status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('failed', 'Failed')],
        help_text="Status of publish attempt"
    )
    tiktok_video_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="TikTok's video ID if successful"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When successfully published"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if failed"
    )

    # Analytics metrics
    views = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total views for this video"
    )
    likes = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total likes for this video"
    )
    comments = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total comments for this video"
    )
    shares = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total shares for this video"
    )

    class Meta:
        db_table = 'publish_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'account']),
            models.Index(fields=['status']),
        ]
        verbose_name = "Publish History"
        verbose_name_plural = "Publish Histories"

    def __str__(self):
        return f"{self.account.username} - {self.status}"
