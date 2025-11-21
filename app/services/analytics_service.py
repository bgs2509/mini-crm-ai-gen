"""
Analytics service for deal metrics and funnel analysis.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_result
from app.repositories.deal_repository import DealRepository
from app.repositories.protocols import IDealRepository
from app.models.deal import DealStatus


class AnalyticsService:
    """Service for analytics and reporting with dependency inversion."""

    def __init__(
        self,
        db: AsyncSession,
        deal_repo: Optional[IDealRepository] = None
    ):
        """
        Initialize analytics service.

        Args:
            db: Database session
            deal_repo: Deal repository (uses default if None)
        """
        self.db = db
        self.deal_repo = deal_repo or DealRepository(db)

    @cache_result("analytics:summary", ttl=300)
    async def get_deals_summary(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get deal summary statistics (cached for 5 minutes).

        Args:
            organization_id: Organization UUID

        Returns:
            Summary statistics
        """
        # Get total metrics
        total_deals = await self.deal_repo.count(organization_id=organization_id)
        total_value = await self.deal_repo.get_total_value(organization_id)
        average_value = await self.deal_repo.get_average_deal_value(organization_id)

        # Get won deals metrics
        won_deals = await self.deal_repo.count(
            organization_id=organization_id,
            status=DealStatus.WON
        )
        won_value = await self.deal_repo.get_total_value(
            organization_id,
            status=DealStatus.WON
        )

        # Get lost deals metrics
        lost_deals = await self.deal_repo.count(
            organization_id=organization_id,
            status=DealStatus.LOST
        )
        lost_value = await self.deal_repo.get_total_value(
            organization_id,
            status=DealStatus.LOST
        )

        # Get in-progress deals metrics
        in_progress_deals = await self.deal_repo.count(
            organization_id=organization_id,
            status=DealStatus.IN_PROGRESS
        )
        in_progress_value = await self.deal_repo.get_total_value(
            organization_id,
            status=DealStatus.IN_PROGRESS
        )

        # Calculate win rate
        closed_deals = won_deals + lost_deals
        win_rate = (won_deals / closed_deals * 100) if closed_deals > 0 else 0.0

        return {
            'total_deals': total_deals,
            'total_value': total_value,
            'average_deal_value': average_value,
            'won_deals': won_deals,
            'won_value': won_value,
            'lost_deals': lost_deals,
            'lost_value': lost_value,
            'in_progress_deals': in_progress_deals,
            'in_progress_value': in_progress_value,
            'win_rate': round(win_rate, 2)
        }

    @cache_result("analytics:funnel", ttl=300)
    async def get_funnel_metrics(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get sales funnel metrics (cached for 5 minutes).

        Args:
            organization_id: Organization UUID

        Returns:
            Funnel metrics
        """
        # Get metrics by status
        by_status = await self.deal_repo.get_summary_by_status(organization_id)

        # Get metrics by stage
        by_stage = await self.deal_repo.get_summary_by_stage(organization_id)

        # Calculate total for percentages
        total_deals = sum(item['count'] for item in by_status)

        # Add percentages
        for item in by_status:
            item['percentage'] = round(
                (item['count'] / total_deals * 100) if total_deals > 0 else 0,
                2
            )

        for item in by_stage:
            item['percentage'] = round(
                (item['count'] / total_deals * 100) if total_deals > 0 else 0,
                2
            )

        # Calculate conversion rate (won / total closed)
        won_count = next(
            (item['count'] for item in by_status if item['status'] == DealStatus.WON),
            0
        )
        lost_count = next(
            (item['count'] for item in by_status if item['status'] == DealStatus.LOST),
            0
        )
        closed_count = won_count + lost_count
        conversion_rate = (won_count / closed_count * 100) if closed_count > 0 else 0.0

        return {
            'by_status': by_status,
            'by_stage': by_stage,
            'conversion_rate': round(conversion_rate, 2)
        }
