"""
Analytics API endpoints.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_organization
from app.schemas.analytics_schemas import (
    DealsSummaryResponse,
    FunnelResponse
)
from app.services.analytics_service import AnalyticsService
from app.models.user import User
from app.models.organization_member import MemberRole


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/deals/summary",
    response_model=DealsSummaryResponse,
    summary="Get deals summary",
    description="Get summary statistics for all deals (cached for 5 minutes)."
)
async def get_deals_summary(
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Get deals summary statistics.

    Returns aggregated metrics:
    - Total deals count and value
    - Won/lost/in-progress breakdown
    - Average deal value
    - Win rate percentage

    Results are cached for 5 minutes.
    """
    org_id, _ = org_info
    service = AnalyticsService(db)

    summary = await service.get_deals_summary(org_id)

    return DealsSummaryResponse(**summary)


@router.get(
    "/deals/funnel",
    response_model=FunnelResponse,
    summary="Get sales funnel",
    description="Get sales funnel metrics by status and stage (cached for 5 minutes)."
)
async def get_funnel_metrics(
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sales funnel metrics.

    Returns:
    - Breakdown by deal status (with counts, amounts, percentages)
    - Breakdown by deal stage (with counts, amounts, percentages)
    - Overall conversion rate

    Results are cached for 5 minutes.
    """
    org_id, _ = org_info
    service = AnalyticsService(db)

    funnel = await service.get_funnel_metrics(org_id)

    return FunnelResponse(**funnel)
