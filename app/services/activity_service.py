"""
Activity service for timeline and comment management.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.activity_repository import ActivityRepository
from app.repositories.deal_repository import DealRepository
from app.repositories.protocols import IActivityRepository
from app.models.activity import ActivityType
from app.core.exceptions import NotFoundError


class ActivityService:
    """Service for activity operations with dependency inversion."""

    def __init__(
        self,
        db: AsyncSession,
        activity_repo: Optional[IActivityRepository] = None
    ):
        """
        Initialize activity service.

        Args:
            db: Database session
            activity_repo: Activity repository (uses default if None)
        """
        self.db = db
        self.activity_repo = activity_repo or ActivityRepository(db)

    async def add_comment(
        self,
        deal_id: UUID,
        author_id: UUID,
        text: str
    ):
        """
        Add comment to deal.

        Args:
            deal_id: Deal UUID
            author_id: User UUID
            text: Comment text

        Returns:
            Created activity

        Raises:
            NotFoundError: If deal does not exist
        """
        # Verify deal exists
        deal_repo = DealRepository(self.db)
        deal = await deal_repo.get_by_id(deal_id)
        if not deal:
            raise NotFoundError("Deal", deal_id)

        activity = await self.activity_repo.create_activity(
            deal_id=deal_id,
            activity_type=ActivityType.COMMENT,
            payload={'text': text},
            author_id=author_id
        )

        await self.db.commit()
        return activity

    async def log_task_created(
        self,
        deal_id: UUID,
        task_title: str,
        author_id: Optional[UUID] = None
    ):
        """
        Log task creation activity.

        Args:
            deal_id: Deal UUID
            task_title: Task title
            author_id: User UUID
        """
        await self.activity_repo.create_activity(
            deal_id=deal_id,
            activity_type=ActivityType.TASK_CREATED,
            payload={'task_title': task_title},
            author_id=author_id
        )
        await self.db.commit()

    async def log_task_completed(
        self,
        deal_id: UUID,
        task_title: str,
        author_id: Optional[UUID] = None
    ):
        """
        Log task completion activity.

        Args:
            deal_id: Deal UUID
            task_title: Task title
            author_id: User UUID
        """
        await self.activity_repo.create_activity(
            deal_id=deal_id,
            activity_type=ActivityType.TASK_COMPLETED,
            payload={'task_title': task_title},
            author_id=author_id
        )
        await self.db.commit()

    async def get_deal_timeline(
        self,
        deal_id: UUID,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list, int]:
        """
        Get activity timeline for a deal.

        Args:
            deal_id: Deal UUID
            organization_id: Organization UUID (for verification)
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            Tuple of (activities list, total count)

        Raises:
            NotFoundError: If deal does not exist
        """
        # Verify deal exists
        deal_repo = DealRepository(self.db)
        deal = await deal_repo.get_by_id(deal_id)
        if not deal:
            raise NotFoundError("Deal", deal_id)

        # Get activities
        activities = await self.activity_repo.get_deal_timeline(
            deal_id=deal_id,
            skip=skip,
            limit=limit
        )

        # Count total activities
        total = await self.activity_repo.count_activities(deal_id=deal_id)

        return activities, total
