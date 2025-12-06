"""
Post schemas for validation and serialization
"""
from ninja import Schema, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import field_validator
from django.utils import timezone


class PostStatus(str, Enum):
    """Post status enumeration"""
    draft = "draft"
    scheduled = "scheduled"
    pending = "pending"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class PostPrivacy(str, Enum):
    """Post privacy level enumeration"""
    public = "public"
    friends = "friends"
    private = "private"


class MediaIn(Schema):
    """
    Media input schema for post attachments

    Required fields match PostMedia model:
    - file_size: File size in bytes
    - file_mime_type: MIME type (e.g., 'video/mp4')
    """
    file_path: str
    file_size: int
    file_mime_type: str
    media_type: str = "video"
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None


class PostCreateIn(Schema):
    """Create post input schema"""
    title: str = Field(..., max_length=150)
    description: str = Field(..., max_length=2200)
    account_ids: List[str]
    scheduled_time: Optional[datetime] = None
    privacy_level: PostPrivacy = PostPrivacy.public
    allow_comments: bool = True
    allow_duet: bool = True
    allow_stitch: bool = True
    hashtags: List[str] = []
    media: Optional[List[MediaIn]] = []
    is_draft: bool = False

    @field_validator('hashtags')
    @classmethod
    def validate_hashtags(cls, v):
        """Validate hashtags"""
        # Remove # if present, limit to 30 hashtags
        cleaned = [tag.lstrip('#') for tag in v]
        if len(cleaned) > 30:
            raise ValueError('Maximum 30 hashtags allowed')
        return cleaned

    @field_validator('scheduled_time')
    @classmethod
    def validate_scheduled_time(cls, v):
        """Validate scheduled time is in future"""
        if v and v <= timezone.now():
            raise ValueError('Scheduled time must be in the future')
        return v


class PostUpdateIn(Schema):
    """Update post input schema"""
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = Field(None, max_length=2200)
    scheduled_time: Optional[datetime] = None
    privacy_level: Optional[PostPrivacy] = None
    hashtags: Optional[List[str]] = None


class PostOut(Schema):
    """Post output schema"""
    id: str
    title: str
    description: str
    status: PostStatus
    scheduled_time: Optional[datetime]
    published_at: Optional[datetime]
    privacy_level: PostPrivacy
    account_count: int
    media_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostDetailOut(PostOut):
    """Detailed post output schema"""
    accounts: List[dict]
    media: List[dict]
    hashtags: List[str]
    allow_comments: bool
    allow_duet: bool
    allow_stitch: bool
    publish_history: List[dict]


class PostListOut(Schema):
    """Post list output with pagination"""
    items: List[PostOut]
    total: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool


class PublishResultOut(Schema):
    """Publish result output schema"""
    success: bool
    published_count: int
    failed_count: int
    results: List[dict]
    message: str


class BulkScheduleIn(Schema):
    """Bulk schedule input schema"""
    post_ids: List[str]
    scheduled_time: datetime
