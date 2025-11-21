"""
Activity API endpoints.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_organization
from app.services.activity_service import ActivityService
from app.schemas.activity_schemas import (
    CommentCreate,
    ActivityResponse,
    TimelineResponse
)
from app.models.user import User
from app.models.organization_member import MemberRole


router = APIRouter(prefix="/deals", tags=["Activities"])


@router.get(
    "/{deal_id}/activities",
    response_model=TimelineResponse,
    summary="Get deal timeline",
    description="Get activity timeline for a deal."
)
async def get_deal_timeline(
    deal_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity timeline for a deal.

    Query parameters:
    - **skip**: Pagination offset
    - **limit**: Max items per page
    """
    org_id, _ = org_info
    service = ActivityService(db)

    # Get timeline (service will verify deal belongs to org)
    activities, total = await service.get_deal_timeline(
        deal_id=deal_id,
        organization_id=org_id,
        skip=skip,
        limit=limit
    )

    return TimelineResponse(
        items=[ActivityResponse.model_validate(a) for a in activities],
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(activities)) < total
    )


@router.post(
    "/{deal_id}/activities",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
    description="Add comment to deal timeline."
)
async def add_comment(
    deal_id: UUID,
    data: CommentCreate,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Add comment to deal.

    - **text**: Comment text
    """
    org_id, _ = org_info
    service = ActivityService(db)

    # Create comment (service will verify deal belongs to org through deal_id)
    activity = await service.add_comment(
        deal_id=deal_id,
        author_id=user.id,
        text=data.text
    )

    return ActivityResponse.model_validate(activity)
