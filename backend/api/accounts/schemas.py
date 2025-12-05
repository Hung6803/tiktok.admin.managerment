"""
Pydantic schemas for TikTok Accounts API
"""
from ninja import Schema
from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID


class AccountStatus(str, Enum):
    """TikTok account status"""
    active = "active"
    inactive = "inactive"
    expired = "expired"


class TikTokAccountOut(Schema):
    """TikTok account output schema"""
    id: UUID
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    status: AccountStatus
    follower_count: int
    following_count: int
    video_count: int
    last_synced_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AccountDetailOut(TikTokAccountOut):
    """Detailed TikTok account output schema"""
    tiktok_user_id: str
    token_expires_at: datetime
    last_error: Optional[str] = None
    updated_at: datetime


class AccountListOut(Schema):
    """Paginated list of TikTok accounts"""
    items: List[TikTokAccountOut]
    total: int
    cursor: Optional[str] = None
    has_more: bool = False


class SyncResultOut(Schema):
    """Result of account sync operation"""
    success: bool
    synced_at: datetime
    follower_count: int
    following_count: int
    video_count: int
    message: Optional[str] = None


class ErrorOut(Schema):
    """Standard error response schema"""
    detail: str
    code: Optional[str] = None
