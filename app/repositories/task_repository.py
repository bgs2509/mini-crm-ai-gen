"""
Task repository for task management operations.
"""
from typing import List
from uuid import UUID
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for Task model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize task repository.

        Args:
            db: Database session
        """
        super().__init__(Task, db)

    async def get_by_deal(
        self,
        deal_id: UUID,
        include_done: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Get tasks for a deal.

        Args:
            deal_id: Deal UUID
            include_done: Whether to include completed tasks
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of tasks
        """
        query = select(Task).where(Task.deal_id == deal_id)

        if not include_done:
            query = query.where(Task.is_done.is_(False))

        query = query.order_by(Task.due_date.asc(), Task.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_tasks(
        self,
        deal_id: UUID
    ) -> List[Task]:
        """
        Get overdue tasks for a deal.

        Args:
            deal_id: Deal UUID

        Returns:
            List of overdue tasks
        """
        today = date.today()
        result = await self.db.execute(
            select(Task).where(
                Task.deal_id == deal_id,
                Task.is_done.is_(False),
                Task.due_date < today
            ).order_by(Task.due_date.asc())
        )
        return list(result.scalars().all())

    async def mark_as_done(self, task_id: UUID) -> Task:
        """
        Mark task as done.

        Args:
            task_id: Task UUID

        Returns:
            Updated task
        """
        return await self.update(task_id, is_done=True)

    async def mark_as_undone(self, task_id: UUID) -> Task:
        """
        Mark task as not done.

        Args:
            task_id: Task UUID

        Returns:
            Updated task
        """
        return await self.update(task_id, is_done=False)

    async def count_pending_tasks(self, deal_id: UUID) -> int:
        """
        Count pending (not done) tasks for a deal.

        Args:
            deal_id: Deal UUID

        Returns:
            Count of pending tasks
        """
        return await self.count(deal_id=deal_id, is_done=False)
