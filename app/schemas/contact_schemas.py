"""
Contact related Pydantic schemas.
"""
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, IDModelMixin, TimestampMixin


class ContactCreate(BaseSchema):
    """Contact creation schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Contact name")
    email: EmailStr = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone")


class ContactUpdate(BaseSchema):
    """Contact update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)


class ContactResponse(IDModelMixin, TimestampMixin):
    """Contact response schema."""

    organization_id: UUID
    owner_id: UUID
    name: str
    email: str
    phone: Optional[str] = None


class ContactWithOwner(ContactResponse):
    """Contact response with owner information."""

    owner_name: str


class ContactListResponse(BaseSchema):
    """Paginated contact list response."""

    items: list[ContactResponse]
    total: int
    skip: int
    limit: int
    has_more: bool
