"""
Analytics related Pydantic schemas.
"""
from typing import List
from decimal import Decimal

from app.schemas.base import BaseSchema
from app.models.deal import DealStatus, DealStage


class StatusMetrics(BaseSchema):
    """Metrics for a specific status."""

    status: DealStatus
    count: int
    total_amount: Decimal
    percentage: float


class StageMetrics(BaseSchema):
    """Metrics for a specific stage."""

    stage: DealStage
    count: int
    total_amount: Decimal
    percentage: float


class DealsSummaryResponse(BaseSchema):
    """Deals summary statistics."""

    total_deals: int
    total_value: Decimal
    average_deal_value: Decimal
    won_deals: int
    won_value: Decimal
    lost_deals: int
    lost_value: Decimal
    in_progress_deals: int
    in_progress_value: Decimal
    win_rate: float


class FunnelResponse(BaseSchema):
    """Sales funnel metrics."""

    by_status: List[StatusMetrics]
    by_stage: List[StageMetrics]
    conversion_rate: float


class MetricsResponse(BaseSchema):
    """Combined metrics response."""

    summary: DealsSummaryResponse
    funnel: FunnelResponse
