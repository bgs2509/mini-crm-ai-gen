"""
Task related Pydantic schemas.
"""
from typing import Optional
from uuid import UUID
from datetime import date

from pydantic import Field

from app.schemas.base import BaseSchema, IDModelMixin, TimestampMixin


class TaskCreate(BaseSchema):
    """Task creation schema."""

    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    due_date: Optional[date] = Field(None, description="Task due date")


class TaskUpdate(BaseSchema):
    """Task update schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_done: Optional[bool] = None


class TaskResponse(IDModelMixin, TimestampMixin):
    """Task response schema."""

    deal_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_done: bool


class TaskListResponse(BaseSchema):
    """Task list response."""

    items: list[TaskResponse]
    total: int
