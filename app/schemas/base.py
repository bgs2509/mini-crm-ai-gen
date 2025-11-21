"""
Base Pydantic schemas.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        str_strip_whitespace=True
    )


class IDModelMixin(BaseSchema):
    """Mixin for models with ID field."""

    id: UUID


class TimestampMixin(BaseSchema):
    """Mixin for models with created_at field."""

    created_at: datetime


class UpdateTimestampMixin(TimestampMixin):
    """Mixin for models with created_at and updated_at fields."""

    updated_at: datetime


class PaginatedResponse(BaseSchema):
    """Generic paginated response schema."""

    items: list
    total: int
    skip: int
    limit: int
    has_more: bool

    @classmethod
    def create(
        cls,
        items: list,
        total: int,
        skip: int,
        limit: int
    ) -> "PaginatedResponse":
        """
        Create paginated response.

        Args:
            items: List of items
            total: Total count
            skip: Number of items skipped
            limit: Maximum items per page

        Returns:
            Paginated response
        """
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )


class ErrorResponse(BaseSchema):
    """Error response schema."""

    error_code: str
    message: str
    details: Optional[dict] = None


class MessageResponse(BaseSchema):
    """Simple message response schema."""

    message: str
