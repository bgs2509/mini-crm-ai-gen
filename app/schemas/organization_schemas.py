"""
Organization related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, IDModelMixin, TimestampMixin
from app.models.organization_member import MemberRole


class OrganizationResponse(IDModelMixin, TimestampMixin):
    """Organization response schema."""

    name: str
    default_currency: Optional[str] = None


class OrganizationWithRole(OrganizationResponse):
    """Organization with user's role."""

    role: MemberRole


class UserWithRole(BaseSchema):
    """User with role in organization."""

    id: UUID
    email: str
    name: str
    role: MemberRole
    joined_at: datetime


class MemberListResponse(BaseSchema):
    """Organization members list response."""

    members: List[UserWithRole]
    total: int


class UpdateOrganizationRequest(BaseSchema):
    """Update organization request schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    default_currency: Optional[str] = Field(None, min_length=3, max_length=3)


class AddMemberRequest(BaseSchema):
    """Add member to organization request."""

    user_email: str = Field(..., description="Email of user to add")
    role: MemberRole = Field(default=MemberRole.MEMBER, description="Member role")


class UpdateMemberRoleRequest(BaseSchema):
    """Update member role request."""

    role: MemberRole = Field(..., description="New role")
