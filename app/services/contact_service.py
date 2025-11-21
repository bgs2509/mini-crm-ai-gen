"""
Contact service for contact management and business logic.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.repositories.contact_repository import ContactRepository
from app.repositories.deal_repository import DealRepository
from app.repositories.protocols import IContactRepository, IDealRepository
from app.models.contact import Contact
from app.models.deal import DealStatus


class ContactService:
    """Service for contact operations with dependency inversion."""

    def __init__(
        self,
        db: AsyncSession,
        contact_repo: Optional[IContactRepository] = None,
        deal_repo: Optional[IDealRepository] = None
    ):
        """
        Initialize contact service.

        Args:
            db: Database session
            contact_repo: Contact repository (uses default if None)
            deal_repo: Deal repository (uses default if None)
        """
        self.db = db
        self.contact_repo = contact_repo or ContactRepository(db)
        self.deal_repo = deal_repo or DealRepository(db)

    async def create_contact(
        self,
        organization_id: UUID,
        owner_id: UUID,
        name: str,
        email: str,
        phone: Optional[str] = None
    ) -> Contact:
        """
        Create new contact with validation.

        Args:
            organization_id: Organization UUID
            owner_id: Owner user UUID
            name: Contact name
            email: Contact email
            phone: Contact phone (optional)

        Returns:
            Created contact

        Raises:
            ValidationError: If email already exists in organization
        """
        # Check if email already exists in organization
        if await self.contact_repo.email_exists_in_org(organization_id, email):
            raise ValidationError(
                f"Contact with email '{email}' already exists in this organization",
                field="email"
            )

        # Create contact
        contact = await self.contact_repo.create(
            organization_id=organization_id,
            owner_id=owner_id,
            name=name,
            email=email,
            phone=phone
        )

        await self.db.commit()
        return contact

    async def update_contact(
        self,
        contact_id: UUID,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Contact:
        """
        Update contact with validation.

        Args:
            contact_id: Contact UUID
            name: New name (optional)
            email: New email (optional)
            phone: New phone (optional)

        Returns:
            Updated contact

        Raises:
            NotFoundError: If contact not found
            ValidationError: If new email already exists
        """
        contact = await self.contact_repo.get_by_id(contact_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)

        updates = {}

        if name is not None:
            updates['name'] = name

        if email is not None and email != contact.email:
            # Check if new email already exists
            if await self.contact_repo.email_exists_in_org(
                contact.organization_id,
                email,
                exclude_id=contact_id
            ):
                raise ValidationError(
                    f"Contact with email '{email}' already exists in this organization",
                    field="email"
                )
            updates['email'] = email

        if phone is not None:
            updates['phone'] = phone

        if not updates:
            return contact

        contact = await self.contact_repo.update(contact_id, **updates)
        await self.db.commit()
        return contact

    async def delete_contact(
        self,
        contact_id: UUID,
        force: bool = False
    ) -> bool:
        """
        Delete contact with validation.

        Args:
            contact_id: Contact UUID
            force: Force delete even if there are active deals

        Returns:
            True if deleted

        Raises:
            BusinessLogicError: If contact has active deals and force is False
        """
        contact = await self.contact_repo.get_by_id(contact_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)

        # Check if contact has active deals
        if not force:
            active_deals_count = await self.deal_repo.count_by_contact(
                contact_id,
                exclude_status=[DealStatus.WON, DealStatus.LOST]
            )

            if active_deals_count > 0:
                raise BusinessLogicError(
                    f"Cannot delete contact with {active_deals_count} active deal(s). "
                    "Close or reassign deals first, or use force=True."
                )

        result = await self.contact_repo.delete(contact_id)
        await self.db.commit()
        return result

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
        return await self.contact_repo.search_contacts(
            organization_id=organization_id,
            search_query=search_query,
            owner_id=owner_id,
            skip=skip,
            limit=limit
        )

    async def get_contact_by_id(
        self,
        contact_id: UUID,
        organization_id: UUID
    ) -> Contact:
        """
        Get contact by ID with organization check.

        Args:
            contact_id: Contact UUID
            organization_id: Organization UUID

        Returns:
            Contact

        Raises:
            NotFoundError: If contact not found or belongs to different organization
        """
        contact = await self.contact_repo.get_by_id(contact_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)

        if contact.organization_id != organization_id:
            raise NotFoundError("Contact", contact_id)

        return contact
