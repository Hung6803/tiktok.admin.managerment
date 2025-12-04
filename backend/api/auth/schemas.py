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
