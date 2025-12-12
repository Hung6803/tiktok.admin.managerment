"""
Pydantic schemas for authentication API
"""
from ninja import Schema
from pydantic import EmailStr, field_validator, field_serializer
from typing import Optional
from datetime import datetime
from uuid import UUID


class RegisterIn(Schema):
    """User registration input schema"""
    email: EmailStr
    password: str
    username: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class LoginIn(Schema):
    """User login input schema"""
    email: EmailStr
    password: str


class RefreshIn(Schema):
    """Token refresh input schema"""
    refresh_token: str


class LogoutIn(Schema):
    """Logout input schema"""
    refresh_token: Optional[str] = None  # Optional for logging out all sessions


class TokenOut(Schema):
    """JWT token output schema"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class UserOut(Schema):
    """User profile output schema"""
    id: UUID
    email: str
    username: str
    timezone: str
    is_email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorOut(Schema):
    """Standard error response schema"""
    detail: str


class ProfileUpdateIn(Schema):
    """Profile update input schema"""
    username: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format"""
        if v is not None:
            if len(v) < 2:
                raise ValueError('Username must be at least 2 characters')
            if len(v) > 50:
                raise ValueError('Username must be at most 50 characters')
        return v

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone is a known timezone"""
        if v is not None:
            valid_timezones = {
                'UTC', 'America/New_York', 'America/Chicago', 'America/Denver',
                'America/Los_Angeles', 'America/Sao_Paulo', 'Europe/London',
                'Europe/Paris', 'Europe/Moscow', 'Asia/Dubai', 'Asia/Kolkata',
                'Asia/Bangkok', 'Asia/Ho_Chi_Minh', 'Asia/Singapore',
                'Asia/Shanghai', 'Asia/Tokyo', 'Asia/Seoul', 'Australia/Sydney',
                'Pacific/Auckland'
            }
            if v not in valid_timezones:
                raise ValueError('Invalid timezone')
        return v


class PasswordChangeIn(Schema):
    """Password change input schema"""
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v


class MessageOut(Schema):
    """Simple message response schema"""
    message: str
