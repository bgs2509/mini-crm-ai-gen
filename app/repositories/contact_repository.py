"""
Contact repository for contact management operations.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    """Repository for Contact model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize contact repository.

        Args:
            db: Database session
        """
        super().__init__(Contact, db)

    async def get_by_email_in_org(
        self,
        organization_id: UUID,
        email: str
    ) -> Optional[Contact]:
        """
        Get contact by email in specific organization.

        Args:
            organization_id: Organization UUID
            email: Contact email

        Returns:
            Contact or None if not found
        """
        result = await self.db.execute(
            select(Contact).where(
                Contact.organization_id == organization_id,
                Contact.email == email
            )
        )
        return result.scalar_one_or_none()

    async def email_exists_in_org(
        self,
        organization_id: UUID,
        email: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if email exists for organization (excluding specific contact).

        Args:
            organization_id: Organization UUID
            email: Email to check
            exclude_id: Contact ID to exclude from check

        Returns:
            True if email exists
        """
        query = select(Contact).where(
            Contact.organization_id == organization_id,
            Contact.email == email
        )

        if exclude_id:
            query = query.where(Contact.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def search_contacts(
        self,
        organization_id: UUID,
        search_query: Optional[str] = None,
        owner_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Contact]:
        """
        Search contacts with filters.

        Args:
            organization_id: Organization UUID
            search_query: Search query for name/email
            owner_id: Filter by owner
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of contacts
        """
        query = select(Contact).where(
            Contact.organization_id == organization_id
        )

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    Contact.name.ilike(search_pattern),
                    Contact.email.ilike(search_pattern)
                )
            )

        if owner_id:
            query = query.where(Contact.owner_id == owner_id)

        query = query.order_by(Contact.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_owner(
        self,
        owner_id: UUID,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Contact]:
        """
        Get contacts by owner in organization.

        Args:
            owner_id: Owner user UUID
            organization_id: Organization UUID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of contacts
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            owner_id=owner_id,
            organization_id=organization_id
        )
