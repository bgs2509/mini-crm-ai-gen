"""
Task API endpoints.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_organization
from app.core.exceptions import NotFoundError
from app.core.permissions import permissions
from app.services.task_service import TaskService
from app.schemas.task_schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse
)
from app.schemas.base import MessageResponse
from app.models.user import User
from app.models.organization_member import MemberRole


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks",
    description="Get tasks for a specific deal."
)
async def list_tasks(
    deal_id: UUID = Query(..., description="Deal ID to get tasks for"),
    include_done: bool = Query(True, description="Include completed tasks"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    List tasks for a deal.

    Query parameters:
    - **deal_id**: Deal ID (required)
    - **include_done**: Include completed tasks
    - **skip**: Pagination offset
    - **limit**: Max items per page
    """
    org_id, _ = org_info
    service = TaskService(db)

    # Get tasks (service will verify deal belongs to org)
    tasks = await service.get_deal_tasks(
        deal_id=deal_id,
        include_done=include_done,
        skip=skip,
        limit=limit
    )

    # Count total tasks
    from app.repositories.task_repository import TaskRepository
    repo = TaskRepository(db)
    total = await repo.count(deal_id=deal_id)

    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Create new task for a deal."
)
async def create_task(
    data: TaskCreate,
    deal_id: UUID = Query(..., description="Deal ID to create task for"),
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new task.

    - **deal_id**: Deal ID (query parameter)
    - **title**: Task title
    - **description**: Optional task description
    - **due_date**: Optional due date
    """
    org_id, user_role = org_info
    service = TaskService(db)

    # Get deal to check ownership
    from app.repositories.deal_repository import DealRepository
    from app.api.helpers import verify_resource_organization

    deal_repo = DealRepository(db)
    deal = await deal_repo.get_by_id(deal_id)
    if not deal:
        raise NotFoundError("Deal", deal_id)
    verify_resource_organization(deal, org_id, "Deal", deal_id)

    # Check if user can modify this deal (and therefore create tasks for it)
    if deal:
        permissions.check_resource_ownership(
            user.id,
            deal.owner_id,
            user_role,
            "Deal",
            str(deal_id)
        )

    # Create task
    task = await service.create_task(
        deal_id=deal_id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        user_id=user.id
    )

    return TaskResponse.model_validate(task)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task",
    description="Get task by ID."
)
async def get_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get task by ID."""
    org_id, _ = org_info
    service = TaskService(db)

    task = await service.get_task_by_id(task_id, org_id)
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update task information."
)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update task."""
    org_id, user_role = org_info
    service = TaskService(db)

    # Get task and verify organization
    task = await service.get_task_by_id(task_id, org_id)

    # Update task
    update_data = data.model_dump(exclude_unset=True)

    # Handle is_done separately
    if 'is_done' in update_data:
        is_done = update_data.pop('is_done')
        if is_done != task.is_done:
            if is_done:
                task = await service.mark_task_done(task_id, user.id)
            else:
                task = await service.mark_task_undone(task_id, user.id)

    # Update other fields
    if update_data:
        task = await service.update_task(task_id, **update_data)

    return TaskResponse.model_validate(task)


@router.post(
    "/{task_id}/done",
    response_model=TaskResponse,
    summary="Mark task as done",
    description="Mark task as completed."
)
async def mark_done(
    task_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Mark task as done."""
    org_id, _ = org_info
    service = TaskService(db)

    # Verify task belongs to organization
    await service.get_task_by_id(task_id, org_id)

    # Mark as done
    task = await service.mark_task_done(task_id, user.id)
    return TaskResponse.model_validate(task)


@router.post(
    "/{task_id}/undone",
    response_model=TaskResponse,
    summary="Mark task as not done",
    description="Mark task as not completed."
)
async def mark_undone(
    task_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Mark task as not done."""
    org_id, _ = org_info
    service = TaskService(db)

    # Verify task belongs to organization
    await service.get_task_by_id(task_id, org_id)

    # Mark as undone
    task = await service.mark_task_undone(task_id, user.id)
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
    summary="Delete task",
    description="Delete task from deal."
)
async def delete_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete task."""
    org_id, user_role = org_info
    service = TaskService(db)

    # Verify task belongs to organization
    task = await service.get_task_by_id(task_id, org_id)

    # Check permissions (need to get deal to check ownership)
    from app.repositories.deal_repository import DealRepository
    deal_repo = DealRepository(db)
    deal = await deal_repo.get_by_id(task.deal_id)

    if deal:
        permissions.check_resource_ownership(
            user.id,
            deal.owner_id,
            user_role,
            "Task",
            str(task_id)
        )

    # Delete task
    await service.delete_task(task_id, user.id)

    return MessageResponse(message="Task deleted successfully")


@router.get(
    "/overdue/by-deal/{deal_id}",
    response_model=TaskListResponse,
    summary="Get overdue tasks",
    description="Get overdue tasks for a deal."
)
async def get_overdue_tasks(
    deal_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get overdue tasks for a deal."""
    org_id, _ = org_info
    service = TaskService(db)

    # Get overdue tasks
    tasks = await service.get_overdue_tasks(deal_id)

    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=len(tasks)
    )
