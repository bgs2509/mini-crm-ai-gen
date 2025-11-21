"""
Activity repository for activity timeline operations.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.activity import Activity, ActivityType
from app.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    """Repository for Activity model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize activity repository.

        Args:
            db: Database session
        """
        super().__init__(Activity, db)

    async def create_activity(
        self,
        deal_id: UUID,
        activity_type: ActivityType,
        payload: Dict[str, Any],
        author_id: Optional[UUID] = None
    ) -> Activity:
        """
        Create new activity.

        Args:
            deal_id: Deal UUID
            activity_type: Activity type
            payload: Activity payload data
            author_id: User who created activity (None for system activities)

        Returns:
            Created activity
        """
        return await self.create(
            deal_id=deal_id,
            type=activity_type,
            payload=payload,
            author_id=author_id
        )

    async def get_deal_timeline(
        self,
        deal_id: UUID,
        activity_type: Optional[ActivityType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Activity]:
        """
        Get activity timeline for a deal.

        Args:
            deal_id: Deal UUID
            activity_type: Optional filter by activity type
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of activities ordered by creation time (newest first)
        """
        query = (
            select(Activity)
            .options(joinedload(Activity.author))
            .where(Activity.deal_id == deal_id)
        )

        if activity_type:
            query = query.where(Activity.type == activity_type)

        query = query.order_by(Activity.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_comments(
        self,
        deal_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Activity]:
        """
        Get comments for a deal.

        Args:
            deal_id: Deal UUID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of comment activities
        """
        return await self.get_deal_timeline(
            deal_id=deal_id,
            activity_type=ActivityType.COMMENT,
            skip=skip,
            limit=limit
        )

    async def count_activities(
        self,
        deal_id: UUID,
        activity_type: Optional[ActivityType] = None
    ) -> int:
        """
        Count activities for a deal.

        Args:
            deal_id: Deal UUID
            activity_type: Optional filter by activity type

        Returns:
            Count of activities
        """
        filters: Dict[str, Any] = {'deal_id': deal_id}
        if activity_type:
            filters['type'] = activity_type

        return await self.count(**filters)
