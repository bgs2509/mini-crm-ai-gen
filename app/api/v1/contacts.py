"""
Contact API endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_organization
from app.api.helpers import verify_resource_organization
from app.core.exceptions import AlreadyExistsError
from app.core.permissions import permissions
from app.schemas.contact_schemas import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse
)
from app.repositories.contact_repository import ContactRepository
from app.services.contact_service import ContactService
from app.models.user import User
from app.models.organization_member import MemberRole


router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get(
    "",
    response_model=ContactListResponse,
    summary="List contacts",
    description="Get paginated list of contacts with optional search."
)
async def list_contacts(
    search: Optional[str] = Query(None, description="Search query for name/email"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    List contacts for organization.

    Query parameters:
    - **search**: Search in name and email fields
    - **skip**: Pagination offset
    - **limit**: Max items per page
    """
    org_id, user_role = org_info
    repo = ContactRepository(db)

    # Get contacts
    contacts = await repo.search_contacts(
        organization_id=org_id,
        search_query=search,
        skip=skip,
        limit=limit
    )

    # Get total count
    total = await repo.count(organization_id=org_id)

    return ContactListResponse(
        items=[ContactResponse.model_validate(c) for c in contacts],
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(contacts)) < total
    )


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create contact",
    description="Create new contact in organization."
)
async def create_contact(
    data: ContactCreate,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new contact.

    - **name**: Contact full name
    - **email**: Contact email (must be unique in organization)
    - **phone**: Optional phone number
    """
    org_id, _ = org_info
    repo = ContactRepository(db)

    # Check email uniqueness
    if await repo.email_exists_in_org(org_id, data.email):
        raise AlreadyExistsError("Contact", "email", data.email)

    # Create contact
    contact = await repo.create(
        organization_id=org_id,
        owner_id=user.id,
        name=data.name,
        email=data.email,
        phone=data.phone
    )

    await db.commit()
    return ContactResponse.model_validate(contact)


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Get contact",
    description="Get contact by ID."
)
async def get_contact(
    contact_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get contact by ID."""
    org_id, _ = org_info
    repo = ContactRepository(db)

    contact = await repo.get_by_id_or_404(contact_id)
    verify_resource_organization(contact, org_id, "Contact", contact_id)

    return ContactResponse.model_validate(contact)


@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Update contact",
    description="Update contact information."
)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update contact."""
    org_id, user_role = org_info
    repo = ContactRepository(db)

    contact = await repo.get_by_id_or_404(contact_id)
    verify_resource_organization(contact, org_id, "Contact", contact_id)

    # Check permissions
    permissions.check_resource_ownership(
        user.id,
        contact.owner_id,
        user_role,
        "Contact",
        str(contact_id)
    )

    # Check email uniqueness if changed
    if data.email and data.email != contact.email:
        if await repo.email_exists_in_org(org_id, data.email, exclude_id=contact_id):
            raise AlreadyExistsError("Contact", "email", data.email)

    # Update
    update_data = data.model_dump(exclude_unset=True)
    contact = await repo.update(contact_id, **update_data)

    await db.commit()
    return ContactResponse.model_validate(contact)


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete contact",
    description="Delete contact from organization."
)
async def delete_contact(
    contact_id: UUID,
    user: User = Depends(get_current_user),
    org_info: tuple[UUID, MemberRole] = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete contact."""
    org_id, user_role = org_info
    service = ContactService(db)

    # Get contact and verify belongs to organization
    contact = await service.get_contact_by_id(contact_id, org_id)

    # Check permissions
    permissions.check_resource_ownership(
        user.id,
        contact.owner_id,
        user_role,
        "Contact",
        str(contact_id)
    )

    # Delete contact (service will check for active deals)
    await service.delete_contact(contact_id, force=False)
