"""
Authentication and authorization related Pydantic schemas.
"""
from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema, IDModelMixin, TimestampMixin
from app.models.organization_member import MemberRole


class RegisterRequest(BaseSchema):
    """User registration request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    organization_name: str = Field(..., min_length=1, max_length=255, description="Organization name")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseSchema):
    """User login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")


class TokenResponse(BaseSchema):
    """Token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class RefreshRequest(BaseSchema):
    """Token refresh request schema."""

    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(IDModelMixin, TimestampMixin):
    """User response schema."""

    email: EmailStr
    name: str


class OrganizationWithRole(BaseSchema):
    """Organization with user's role."""

    id: UUID
    name: str
    role: MemberRole
    created_at: datetime


class LoginResponse(BaseSchema):
    """Login response with tokens and user info."""

    user: UserResponse
    organizations: List[OrganizationWithRole]
    tokens: TokenResponse


class RegisterResponse(BaseSchema):
    """Registration response with tokens and user info."""

    user: UserResponse
    organization: OrganizationWithRole
    tokens: TokenResponse
