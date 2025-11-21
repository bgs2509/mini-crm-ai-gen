"""
Activity related Pydantic schemas.
"""
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, IDModelMixin, TimestampMixin
from app.models.activity import ActivityType


class CommentCreate(BaseSchema):
    """Comment creation schema."""

    text: str = Field(..., min_length=1, description="Comment text")


class ActivityResponse(IDModelMixin, TimestampMixin):
    """Activity response schema."""

    deal_id: UUID
    author_id: Optional[UUID] = None
    author_name: Optional[str] = None
    type: ActivityType
    payload: Dict[str, Any]


class TimelineResponse(BaseSchema):
    """Timeline response with activities."""

    items: list[ActivityResponse]
    total: int
    skip: int
    limit: int
    has_more: bool
