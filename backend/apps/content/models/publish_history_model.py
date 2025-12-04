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

    scheduled_post = models.ForeignKey(
        'content.ScheduledPost',
        on_delete=models.CASCADE,
        related_name='publish_attempts',
        help_text="Post that was attempted to publish"
    )

    attempt_number = models.IntegerField(
        help_text="Attempt number (1, 2, 3, etc.)"
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the publish attempt started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the publish attempt completed"
    )

    success = models.BooleanField(
        default=False,
        help_text="Whether the publish was successful"
    )
    error_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Error code if failed"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if failed"
    )

    # API response
    api_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Full API response from TikTok"
    )
    http_status = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP status code from API"
    )

    class Meta:
        db_table = 'publish_history'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['scheduled_post', 'attempt_number']),
            models.Index(fields=['started_at']),
            models.Index(fields=['success']),
        ]
        verbose_name = "Publish History"
        verbose_name_plural = "Publish Histories"

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"Attempt {self.attempt_number} - {status}"

    def get_duration(self):
        """Get duration of publish attempt"""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None
