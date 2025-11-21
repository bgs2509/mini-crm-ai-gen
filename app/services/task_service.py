"""
Task service for task management and business logic.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError, NotFoundError
from app.repositories.task_repository import TaskRepository
from app.repositories.deal_repository import DealRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.protocols import (
    ITaskRepository,
    IDealRepository,
    IActivityRepository
)
from app.models.task import Task
from app.models.activity import ActivityType


class TaskService:
    """Service for task operations with dependency inversion."""

    def __init__(
        self,
        db: AsyncSession,
        task_repo: Optional[ITaskRepository] = None,
        deal_repo: Optional[IDealRepository] = None,
        activity_repo: Optional[IActivityRepository] = None
    ):
        """
        Initialize task service.

        Args:
            db: Database session
            task_repo: Task repository (uses default if None)
            deal_repo: Deal repository (uses default if None)
            activity_repo: Activity repository (uses default if None)
        """
        self.db = db
        self.task_repo = task_repo or TaskRepository(db)
        self.deal_repo = deal_repo or DealRepository(db)
        self.activity_repo = activity_repo or ActivityRepository(db)

    async def create_task(
        self,
        deal_id: UUID,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Task:
        """
        Create new task with validation.

        Args:
            deal_id: Deal UUID
            title: Task title
            description: Task description (optional)
            due_date: Task due date (optional)
            user_id: User creating the task (for activity log)

        Returns:
            Created task

        Raises:
            NotFoundError: If deal not found
            ValidationError: If due date is in the past
        """
        # Verify deal exists
        deal = await self.deal_repo.get_by_id(deal_id)
        if not deal:
            raise NotFoundError("Deal", deal_id)

        # Validate due date
        if due_date and due_date < date.today():
            raise ValidationError(
                "Due date cannot be in the past",
                field="due_date"
            )

        # Create task
        task = await self.task_repo.create(
            deal_id=deal_id,
            title=title,
            description=description,
            due_date=due_date,
            is_done=False
        )

        # Create system activity
        await self.activity_repo.create_activity(
            deal_id=deal_id,
            activity_type=ActivityType.TASK_CREATED,
            payload={
                'task_id': str(task.id),
                'task_title': title,
                'due_date': due_date.isoformat() if due_date else None
            },
            author_id=user_id
        )

        await self.db.commit()
        return task

    async def update_task(
        self,
        task_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[date] = None
    ) -> Task:
        """
        Update task with validation.

        Args:
            task_id: Task UUID
            title: New title (optional)
            description: New description (optional)
            due_date: New due date (optional)

        Returns:
            Updated task

        Raises:
            NotFoundError: If task not found
            ValidationError: If new due date is in the past
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)

        updates: Dict[str, Any] = {}

        if title is not None:
            updates['title'] = title

        if description is not None:
            updates['description'] = description

        if due_date is not None:
            # Validate due date (allow past dates if task is done)
            if not task.is_done and due_date < date.today():
                raise ValidationError(
                    "Due date cannot be in the past for pending tasks",
                    field="due_date"
                )
            updates['due_date'] = due_date

        if not updates:
            return task

        task = await self.task_repo.update(task_id, **updates)
        await self.db.commit()
        return task

    async def mark_task_done(
        self,
        task_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Task:
        """
        Mark task as done.

        Args:
            task_id: Task UUID
            user_id: User completing the task (for activity log)

        Returns:
            Updated task

        Raises:
            NotFoundError: If task not found
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)

        if task.is_done:
            return task

        task = await self.task_repo.mark_as_done(task_id)

        # Create system activity
        await self.activity_repo.create_activity(
            deal_id=task.deal_id,
            activity_type=ActivityType.SYSTEM,
            payload={
                'message': f'Task "{task.title}" marked as done',
                'task_id': str(task_id)
            },
            author_id=user_id
        )

        await self.db.commit()
        return task

    async def mark_task_undone(
        self,
        task_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Task:
        """
        Mark task as not done.

        Args:
            task_id: Task UUID
            user_id: User unmarking the task (for activity log)

        Returns:
            Updated task

        Raises:
            NotFoundError: If task not found
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)

        if not task.is_done:
            return task

        task = await self.task_repo.mark_as_undone(task_id)

        # Create system activity
        await self.activity_repo.create_activity(
            deal_id=task.deal_id,
            activity_type=ActivityType.SYSTEM,
            payload={
                'message': f'Task "{task.title}" marked as not done',
                'task_id': str(task_id)
            },
            author_id=user_id
        )

        await self.db.commit()
        return task

    async def delete_task(
        self,
        task_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bool:
        """
        Delete task.

        Args:
            task_id: Task UUID
            user_id: User deleting the task (for activity log)

        Returns:
            True if deleted

        Raises:
            NotFoundError: If task not found
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)

        deal_id = task.deal_id
        task_title = task.title

        result = await self.task_repo.delete(task_id)

        # Create system activity
        await self.activity_repo.create_activity(
            deal_id=deal_id,
            activity_type=ActivityType.SYSTEM,
            payload={
                'message': f'Task "{task_title}" deleted',
                'task_id': str(task_id)
            },
            author_id=user_id
        )

        await self.db.commit()
        return result

    async def get_deal_tasks(
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
        # Verify deal exists
        deal = await self.deal_repo.get_by_id(deal_id)
        if not deal:
            raise NotFoundError("Deal", deal_id)

        return await self.task_repo.get_by_deal(
            deal_id=deal_id,
            include_done=include_done,
            skip=skip,
            limit=limit
        )

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
        # Verify deal exists
        deal = await self.deal_repo.get_by_id(deal_id)
        if not deal:
            raise NotFoundError("Deal", deal_id)

        return await self.task_repo.get_overdue_tasks(deal_id)

    async def get_task_by_id(
        self,
        task_id: UUID,
        organization_id: UUID
    ) -> Task:
        """
        Get task by ID with organization check.

        Args:
            task_id: Task UUID
            organization_id: Organization UUID (for security)

        Returns:
            Task

        Raises:
            NotFoundError: If task not found or belongs to different organization
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)

        # Get deal to verify organization
        deal = await self.deal_repo.get_by_id(task.deal_id)
        if not deal or deal.organization_id != organization_id:
            raise NotFoundError("Task", task_id)

        return task
