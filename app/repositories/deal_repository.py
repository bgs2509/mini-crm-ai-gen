"""
Deal repository for deal management operations.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.deal import Deal, DealStatus, DealStage
from app.repositories.base import BaseRepository


class DealRepository(BaseRepository[Deal]):
    """Repository for Deal model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize deal repository.

        Args:
            db: Database session
        """
        super().__init__(Deal, db)

    async def search_deals(
        self,
        organization_id: UUID,
        search_query: Optional[str] = None,
        status: Optional[DealStatus] = None,
        stage: Optional[DealStage] = None,
        owner_id: Optional[UUID] = None,
        contact_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Deal]:
        """
        Search deals with filters.

        Args:
            organization_id: Organization UUID
            search_query: Search query for title
            status: Filter by status
            stage: Filter by stage
            owner_id: Filter by owner
            contact_id: Filter by contact
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of deals
        """
        query = select(Deal).where(
            Deal.organization_id == organization_id
        )

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(Deal.title.ilike(search_pattern))

        if status:
            query = query.where(Deal.status == status)

        if stage:
            query = query.where(Deal.stage == stage)

        if owner_id:
            query = query.where(Deal.owner_id == owner_id)

        if contact_id:
            query = query.where(Deal.contact_id == contact_id)

        query = query.order_by(Deal.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_contact(self, deal_id: UUID) -> Optional[Deal]:
        """
        Get deal with contact relationship loaded.

        Args:
            deal_id: Deal UUID

        Returns:
            Deal with contact or None
        """
        result = await self.db.execute(
            select(Deal)
            .options(joinedload(Deal.contact))
            .where(Deal.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def count_by_contact(
        self,
        contact_id: UUID,
        exclude_status: Optional[List[DealStatus]] = None
    ) -> int:
        """
        Count deals for a contact.

        Args:
            contact_id: Contact UUID
            exclude_status: List of statuses to exclude

        Returns:
            Count of deals
        """
        query = select(func.count()).select_from(Deal).where(
            Deal.contact_id == contact_id
        )

        if exclude_status:
            query = query.where(Deal.status.notin_(exclude_status))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_summary_by_status(
        self,
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get deal summary grouped by status.

        Args:
            organization_id: Organization UUID

        Returns:
            List of dicts with status, count, and total_amount
        """
        result = await self.db.execute(
            select(
                Deal.status,
                func.count(Deal.id).label('count'),
                func.sum(Deal.amount).label('total_amount')
            )
            .where(Deal.organization_id == organization_id)
            .group_by(Deal.status)
        )

        return [
            {
                'status': row.status,
                'count': row.count,
                'total_amount': float(row.total_amount or 0)
            }
            for row in result.all()
        ]

    async def get_summary_by_stage(
        self,
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get deal summary grouped by stage.

        Args:
            organization_id: Organization UUID

        Returns:
            List of dicts with stage, count, and total_amount
        """
        result = await self.db.execute(
            select(
                Deal.stage,
                func.count(Deal.id).label('count'),
                func.sum(Deal.amount).label('total_amount')
            )
            .where(Deal.organization_id == organization_id)
            .group_by(Deal.stage)
        )

        return [
            {
                'stage': row.stage,
                'count': row.count,
                'total_amount': float(row.total_amount or 0)
            }
            for row in result.all()
        ]

    async def get_total_value(
        self,
        organization_id: UUID,
        status: Optional[DealStatus] = None
    ) -> Decimal:
        """
        Get total value of deals.

        Args:
            organization_id: Organization UUID
            status: Optional status filter

        Returns:
            Total value
        """
        query = select(func.sum(Deal.amount)).where(
            Deal.organization_id == organization_id
        )

        if status:
            query = query.where(Deal.status == status)

        result = await self.db.execute(query)
        total = result.scalar_one()
        return Decimal(total or 0)

    async def get_average_deal_value(
        self,
        organization_id: UUID,
        status: Optional[DealStatus] = None
    ) -> Decimal:
        """
        Get average deal value.

        Args:
            organization_id: Organization UUID
            status: Optional status filter

        Returns:
            Average value
        """
        query = select(func.avg(Deal.amount)).where(
            Deal.organization_id == organization_id
        )

        if status:
            query = query.where(Deal.status == status)

        result = await self.db.execute(query)
        avg = result.scalar_one()
        return Decimal(avg or 0)
