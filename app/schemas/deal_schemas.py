"""
Deal related Pydantic schemas.
"""
from typing import Optional
from uuid import UUID
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema, IDModelMixin, UpdateTimestampMixin
from app.models.deal import DealStatus, DealStage


class DealCreate(BaseSchema):
    """Deal creation schema."""

    contact_id: UUID = Field(..., description="Contact UUID")
    title: str = Field(..., min_length=1, max_length=255, description="Deal title")
    amount: Decimal = Field(..., ge=0, description="Deal amount")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="Currency code")


class DealUpdate(BaseSchema):
    """Deal update schema (for PATCH)."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    status: Optional[DealStatus] = None
    stage: Optional[DealStage] = None


class DealResponse(IDModelMixin, UpdateTimestampMixin):
    """Deal response schema."""

    organization_id: UUID
    contact_id: UUID
    owner_id: UUID
    title: str
    amount: Decimal
    currency: str
    status: DealStatus
    stage: DealStage


class DealWithContact(DealResponse):
    """Deal response with contact information."""

    contact_name: str
    contact_email: str


class DealWithRelations(DealWithContact):
    """Deal response with all relations."""

    owner_name: str
    tasks_count: int
    pending_tasks_count: int
    activities_count: int


class DealListResponse(BaseSchema):
    """Paginated deal list response."""

    items: list[DealResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class DealSummary(BaseSchema):
    """Deal summary by status/stage."""

    status: Optional[DealStatus] = None
    stage: Optional[DealStage] = None
    count: int
    total_amount: float
