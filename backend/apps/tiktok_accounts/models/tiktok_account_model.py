"""
TikTok account model for managing connected TikTok accounts
"""
from django.db import models
from core.models import BaseModel
from core.fields import EncryptedTextField


class TikTokAccount(BaseModel):
    """
    TikTok account connected to user via OAuth 2.0
    Stores account information and encrypted OAuth tokens
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Token Expired'),
        ('revoked', 'Access Revoked'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='tiktok_accounts',
        help_text="User who owns this TikTok account"
    )
    tiktok_user_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="TikTok's unique user ID"
    )
    username = models.CharField(
        max_length=100,
        help_text="TikTok username"
    )
    display_name = models.CharField(
        max_length=200,
        help_text="TikTok display name"
    )
    avatar_url = models.URLField(
        max_length=500,  # TikTok avatar URLs can be very long
        null=True,
        blank=True,
        help_text="Profile picture URL"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True,
        help_text="Account connection status"
    )

    # OAuth tokens (encrypted using Fernet symmetric encryption)
    access_token = EncryptedTextField(
        help_text="Encrypted OAuth access token"
    )
    refresh_token = EncryptedTextField(
        null=True,
        blank=True,
        help_text="Encrypted OAuth refresh token"
    )
    token_expires_at = models.DateTimeField(
        help_text="When the access token expires"
    )

    # Account metadata
    follower_count = models.IntegerField(
        default=0,
        help_text="Number of followers"
    )
    following_count = models.IntegerField(
        default=0,
        help_text="Number of accounts being followed"
    )
    video_count = models.IntegerField(
        default=0,
        help_text="Total number of videos posted"
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time account data was synced from TikTok"
    )
    last_refreshed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time token was refreshed"
    )
    last_error = models.TextField(
        null=True,
        blank=True,
        help_text="Last error message from token refresh or API calls"
    )

    class Meta:
        db_table = 'tiktok_accounts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'is_deleted']),
            models.Index(fields=['token_expires_at']),
            models.Index(fields=['user', 'status', '-created_at'], name='user_status_created_idx'),
        ]
        verbose_name = "TikTok Account"
        verbose_name_plural = "TikTok Accounts"
        app_label = 'tiktok_accounts'

    def __str__(self):
        return f"{self.username} (@{self.tiktok_user_id})"

    @property
    def is_active(self) -> bool:
        """Check if account is active (for frontend compatibility)"""
        return self.status == 'active'

    def is_token_expired(self):
        """Check if access token has expired"""
        from django.utils import timezone
        return timezone.now() >= self.token_expires_at

    def needs_refresh(self):
        """Check if token needs refresh (expiring within 1 hour)"""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() >= self.token_expires_at - timedelta(hours=1)
