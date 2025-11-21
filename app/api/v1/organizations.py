"""
Organization API endpoints.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_organization
from app.schemas.organization_schemas import (
    OrganizationWithRole,
    OrganizationResponse,
    UpdateOrganizationRequest,
    AddMemberRequest,
    UpdateMemberRoleRequest,
    MemberListResponse,
    UserWithRole
)
from app.services.organization_service import OrganizationService
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.organization_repository import OrganizationRepository
from app.models.user import User
from app.models.organization_member import MemberRole


router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get(
    "/me",
    response_model=List[OrganizationWithRole],
    summary="Get my organizations",
    description="Get all organizations user is a member of."
)
async def get_my_organizations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all organizations for current user.

    Returns list of organizations with user's role in each.
    """
    repo = OrganizationMemberRepository(db)
    organizations = await repo.get_user_organizations(user.id)

    return [
        OrganizationWithRole(
            id=member.organization.id,
            name=member.organization.name,
            default_currency=member.organization.default_currency,
            role=member.role,
            created_at=member.organization.created_at
        )
        for member in organizations
    ]


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get organization details",
    description="Get organization information. Requires membership."
)
async def get_organization(
    org_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Get organization details by ID.

    Requires:
        - User must be a member of the organization
        - Valid organization ID

    Returns:
        Organization details
    """
    # Verify org_id matches the one from header
    current_org_id, _ = org_info

    repo = OrganizationRepository(db)
    organization = await repo.get_by_id_or_404(org_id)

    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        default_currency=organization.default_currency,
        created_at=organization.created_at
    )


@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Update organization settings. Requires OWNER or ADMIN role."
)
async def update_organization(
    org_id: UUID,
    data: UpdateOrganizationRequest,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Update organization settings (name, default_currency).

    Requires:
        - OWNER or ADMIN role
        - Valid organization ID

    Args:
        org_id: Organization UUID
        data: Update data (name, default_currency)

    Returns:
        Updated organization

    Raises:
        403: If user is not OWNER or ADMIN
        404: If organization not found
    """
    current_org_id, role = org_info

    service = OrganizationService(db)
    organization = await service.update_organization(
        organization_id=org_id,
        requester_id=user.id,
        name=data.name,
        default_currency=data.default_currency
    )

    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        default_currency=organization.default_currency,
        created_at=organization.created_at
    )


@router.get(
    "/{org_id}/members",
    response_model=MemberListResponse,
    summary="List organization members",
    description="Get all members of the organization with their roles."
)
async def list_members(
    org_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all organization members with their roles.

    Requires:
        - User must be a member of the organization

    Args:
        org_id: Organization UUID

    Returns:
        List of members with roles and total count

    Raises:
        403: If user is not a member
        404: If organization not found
    """
    current_org_id, _ = org_info

    service = OrganizationService(db)
    members = await service.get_organization_members(org_id, user.id)

    return MemberListResponse(
        members=[
            UserWithRole(
                id=member.user.id,
                email=member.user.email,
                name=member.user.name,
                role=member.role,
                joined_at=member.created_at
            )
            for member in members
        ],
        total=len(members)
    )


@router.post(
    "/{org_id}/members",
    response_model=UserWithRole,
    status_code=status.HTTP_201_CREATED,
    summary="Add organization member",
    description="Add new member to organization. Requires OWNER or ADMIN role."
)
async def add_member(
    org_id: UUID,
    data: AddMemberRequest,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Add new member to organization (invite).

    Requires:
        - OWNER or ADMIN role
        - Only OWNER can add other OWNERs
        - User email must exist in system

    Args:
        org_id: Organization UUID
        data: Member data (email, role)

    Returns:
        Created membership with user info

    Raises:
        400: If user already a member
        403: If requester is not OWNER/ADMIN or trying to add OWNER without permission
        404: If organization or user not found
    """
    current_org_id, role = org_info

    service = OrganizationService(db)
    membership = await service.add_member(
        organization_id=org_id,
        requester_id=user.id,
        user_email=data.user_email,
        role=data.role
    )

    return UserWithRole(
        id=membership.user.id,
        email=membership.user.email,
        name=membership.user.name,
        role=membership.role,
        joined_at=membership.created_at
    )


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove organization member",
    description="Remove member from organization. Requires OWNER or ADMIN role."
)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove member from organization.

    Requires:
        - OWNER or ADMIN role
        - Only OWNER can remove other OWNERs
        - Cannot remove the last OWNER

    Args:
        org_id: Organization UUID
        user_id: User UUID to remove

    Raises:
        403: If requester is not OWNER/ADMIN or trying to remove OWNER without permission
        404: If organization or membership not found
        409: If trying to remove the last owner
    """
    current_org_id, role = org_info

    service = OrganizationService(db)
    await service.remove_member(
        organization_id=org_id,
        requester_id=user.id,
        user_id=user_id
    )


@router.patch(
    "/{org_id}/members/{user_id}/role",
    response_model=UserWithRole,
    summary="Update member role",
    description="Change member's role in organization. Requires OWNER role."
)
async def update_member_role(
    org_id: UUID,
    user_id: UUID,
    data: UpdateMemberRoleRequest,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Update member's role in organization.

    Requires:
        - OWNER role (only OWNER can change roles)
        - Cannot downgrade the last OWNER

    Args:
        org_id: Organization UUID
        user_id: User UUID whose role to change
        data: New role

    Returns:
        Updated membership with new role

    Raises:
        403: If requester is not OWNER
        404: If organization or membership not found
        409: If trying to downgrade the last owner
    """
    current_org_id, role = org_info

    service = OrganizationService(db)
    membership = await service.update_member_role(
        organization_id=org_id,
        requester_id=user.id,
        user_id=user_id,
        new_role=data.role
    )

    return UserWithRole(
        id=membership.user.id,
        email=membership.user.email,
        name=membership.user.name,
        role=membership.role,
        joined_at=membership.created_at
    )
