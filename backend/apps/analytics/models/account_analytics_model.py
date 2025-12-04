"""
Account analytics model for tracking TikTok account metrics over time
"""
from django.db import models
from core.models import BaseModel


class AccountAnalytics(BaseModel):
    """
    Daily analytics snapshot for TikTok accounts
    Tracks engagement metrics and growth over time
    """

    tiktok_account = models.ForeignKey(
        'tiktok_accounts.TikTokAccount',
        on_delete=models.CASCADE,
        related_name='analytics',
        help_text="TikTok account these analytics belong to"
    )
    date = models.DateField(
        db_index=True,
        help_text="Date of this analytics snapshot"
    )

    # Engagement metrics
    follower_count = models.IntegerField(
        default=0,
        help_text="Total followers on this date"
    )
    following_count = models.IntegerField(
        default=0,
        help_text="Total following on this date"
    )
    video_count = models.IntegerField(
        default=0,
        help_text="Total videos on this date"
    )
    total_likes = models.BigIntegerField(
        default=0,
        help_text="Total likes across all videos"
    )
    total_views = models.BigIntegerField(
        default=0,
        help_text="Total views across all videos"
    )
    total_shares = models.BigIntegerField(
        default=0,
        help_text="Total shares across all videos"
    )
    total_comments = models.BigIntegerField(
        default=0,
        help_text="Total comments across all videos"
    )

    # Growth metrics
    follower_growth = models.IntegerField(
        default=0,
        help_text="Change in followers since previous day"
    )
    engagement_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Engagement rate percentage"
    )

    class Meta:
        db_table = 'account_analytics'
        ordering = ['-date']
        unique_together = [['tiktok_account', 'date']]
        indexes = [
            models.Index(fields=['tiktok_account', 'date']),
            models.Index(fields=['date']),
        ]
        verbose_name = "Account Analytics"
        verbose_name_plural = "Account Analytics"

    def __str__(self):
        return f"{self.tiktok_account.username} - {self.date}"

    def calculate_engagement_rate(self):
        """Calculate engagement rate: (likes + comments + shares) / views * 100"""
        if self.total_views > 0:
            total_engagement = self.total_likes + self.total_comments + self.total_shares
            return round((total_engagement / self.total_views) * 100, 2)
        return 0.0
