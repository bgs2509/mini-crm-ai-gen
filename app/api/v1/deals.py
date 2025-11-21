"""
Deal API endpoints.
"""
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_organization
from app.api.helpers import verify_resource_organization
from app.core.exceptions import BusinessLogicError
from app.core.permissions import permissions
from app.schemas.deal_schemas import (
    DealCreate,
    DealUpdate,
    DealResponse,
    DealListResponse
)
from app.services.deal_service import DealService
from app.repositories.deal_repository import DealRepository
from app.models.user import User
from app.models.organization_member import MemberRole
from app.models.deal import DealStatus, DealStage


router = APIRouter(prefix="/deals", tags=["Deals"])


@router.get(
    "",
    response_model=DealListResponse,
    summary="List deals",
    description="Get paginated list of deals with filters."
)
async def list_deals(
    search: Optional[str] = Query(None, description="Search in title"),
    status: Optional[DealStatus] = Query(None, description="Filter by status"),
    stage: Optional[DealStage] = Query(None, description="Filter by stage"),
    contact_id: Optional[UUID] = Query(None, description="Filter by contact"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """List deals for organization with filters."""
    org_id, _ = org_info
    repo = DealRepository(db)

    deals = await repo.search_deals(
        organization_id=org_id,
        search_query=search,
        status=status,
        stage=stage,
        contact_id=contact_id,
        skip=skip,
        limit=limit
    )

    total = await repo.count(organization_id=org_id)

    return DealListResponse(
        items=[DealResponse.model_validate(d) for d in deals],
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(deals)) < total
    )


@router.post(
    "",
    response_model=DealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create deal",
    description="Create new deal for contact."
)
async def create_deal(
    data: DealCreate,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create new deal."""
    org_id, _ = org_info
    service = DealService(db)

    deal = await service.create_deal(
        organization_id=org_id,
        contact_id=data.contact_id,
        owner_id=user.id,
        title=data.title,
        amount=data.amount,
        currency=data.currency
    )

    return DealResponse.model_validate(deal)


@router.get(
    "/{deal_id}",
    response_model=DealResponse,
    summary="Get deal",
    description="Get deal by ID."
)
async def get_deal(
    deal_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get deal by ID."""
    org_id, _ = org_info
    repo = DealRepository(db)

    deal = await repo.get_by_id_or_404(deal_id)
    verify_resource_organization(deal, org_id, "Deal", deal_id)

    return DealResponse.model_validate(deal)


@router.patch(
    "/{deal_id}",
    response_model=DealResponse,
    summary="Update deal",
    description="Update deal fields (PATCH)."
)
async def update_deal(
    deal_id: UUID,
    data: DealUpdate,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update deal with partial data."""
    org_id, user_role = org_info
    repo = DealRepository(db)
    service = DealService(db)

    deal = await repo.get_by_id_or_404(deal_id)
    verify_resource_organization(deal, org_id, "Deal", deal_id)

    # Check permissions for basic fields
    if data.title or data.amount or data.currency:
        permissions.check_resource_ownership(
            user.id,
            deal.owner_id,
            user_role,
            "Deal",
            str(deal_id)
        )

    # Validate won status with amount
    if data.status == DealStatus.WON:
        # Check current amount or the new amount if being updated
        final_amount = data.amount if data.amount is not None else deal.amount
        if final_amount <= 0:
            raise BusinessLogicError(
                f"Cannot mark deal as won with amount {final_amount}. Amount must be greater than 0."
            )

    # Handle status change separately
    if data.status and data.status != deal.status:
        deal = await service.update_deal_status(
            deal_id=deal_id,
            new_status=data.status,
            user_id=user.id,
            user_role=user_role
        )

    # Handle stage change separately
    if data.stage and data.stage != deal.stage:
        deal = await service.update_deal_stage(
            deal_id=deal_id,
            new_stage=data.stage,
            user_id=user.id,
            user_role=user_role
        )

    # Update basic fields
    update_data: Dict[str, Any] = {}
    if data.title:
        update_data['title'] = data.title
    if data.amount is not None:
        update_data['amount'] = data.amount
    if data.currency:
        update_data['currency'] = data.currency.upper()

    if update_data:
        deal = await repo.update(deal_id, **update_data)
        await db.commit()

    return DealResponse.model_validate(deal)


@router.delete(
    "/{deal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete deal",
    description="Delete deal and all related data."
)
async def delete_deal(
    deal_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete deal."""
    org_id, user_role = org_info
    service = DealService(db)
    repo = DealRepository(db)

    deal = await repo.get_by_id_or_404(deal_id)
    verify_resource_organization(deal, org_id, "Deal", deal_id)

    # Check permissions
    permissions.check_resource_ownership(
        user.id,
        deal.owner_id,
        user_role,
        "Deal",
        str(deal_id)
    )

    await service.delete_deal(deal_id)
