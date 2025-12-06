"""
Media upload schemas for validation and serialization
"""
from ninja import Schema, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import field_validator


class MediaType(str, Enum):
    """Media type enumeration"""
    video = "video"
    image = "image"


class UploadStatus(str, Enum):
    """Upload status enumeration"""
    pending = "pending"
    uploading = "uploading"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ChunkUploadIn(Schema):
    """Chunk upload input schema"""
    upload_id: str
    chunk_index: int = Field(..., ge=0)
    total_chunks: int = Field(..., gt=0)
    file_name: str
    file_size: int = Field(..., gt=0)
    content_type: str


class ChunkUploadOut(Schema):
    """Chunk upload response schema"""
    upload_id: str
    chunk_index: int
    received_bytes: int
    status: str
    next_chunk: Optional[int] = None
    progress: int = 0  # percentage


class UploadInitIn(Schema):
    """Initialize upload session schema"""
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, le=500*1024*1024)  # max 500MB
    content_type: str
    chunk_size: int = Field(5*1024*1024, gt=0)  # 5MB default
    media_type: MediaType = MediaType.video

    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v):
        """Validate content type"""
        allowed_types = [
            'video/mp4', 'video/quicktime', 'video/webm',
            'image/jpeg', 'image/png', 'image/jpg'
        ]
        if v not in allowed_types:
            raise ValueError(f'Content type must be one of: {", ".join(allowed_types)}')
        return v


class UploadInitOut(Schema):
    """Initialize upload response schema"""
    upload_id: str
    chunk_size: int
    total_chunks: int
    upload_url: str
    expires_at: datetime


class MediaOut(Schema):
    """Media output schema"""
    id: str
    file_name: str
    file_size: int
    file_mime_type: str
    media_type: str
    duration: Optional[int] = None  # seconds
    thumbnail_url: Optional[str] = None
    file_path: str  # local storage path
    status: str = "completed"
    created_at: datetime

    class Config:
        from_attributes = True


class UploadProgressOut(Schema):
    """Upload progress response schema"""
    upload_id: str
    progress: int = Field(..., ge=0, le=100)  # percentage
    uploaded_bytes: int
    total_bytes: int
    status: UploadStatus
    eta_seconds: Optional[int] = None
    message: Optional[str] = None


class VideoMetadataOut(Schema):
    """Video metadata output schema"""
    duration: int
    width: int
    height: int
    fps: float
    codec: str
    bitrate: int
    has_audio: bool


class SimpleUploadOut(Schema):
    """Simple upload response schema"""
    media_id: str
    file_name: str
    file_size: int
    media_type: MediaType
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    file_path: str
    message: str


class MultiImageUploadIn(Schema):
    """Multiple image upload input schema"""
    post_id: Optional[str] = None

    @field_validator('post_id')
    @classmethod
    def validate_post_id(cls, v):
        """Validate post ID format if provided"""
        if v and len(v) != 36:  # UUID length
            raise ValueError('Invalid post ID format')
        return v


class SupportedFormatsOut(Schema):
    """Supported formats response schema"""
    video: List[str]
    image: List[str]
    max_file_size: int
    max_duration: int
    max_resolution: str
    chunk_size_recommended: int
