"""
Organization repository for organization management operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize organization repository.

        Args:
            db: Database session
        """
        super().__init__(Organization, db)

    async def create_organization(
        self,
        name: str,
        default_currency: Optional[str] = None
    ) -> Organization:
        """
        Create new organization.

        Args:
            name: Organization name
            default_currency: Default currency code (ISO 4217)

        Returns:
            Created organization
        """
        return await self.create(
            name=name,
            default_currency=default_currency
        )

    async def update_currency(
        self,
        organization_id: UUID,
        currency: str
    ) -> Organization:
        """
        Update organization default currency.

        Args:
            organization_id: Organization UUID
            currency: Currency code (ISO 4217)

        Returns:
            Updated organization
        """
        return await self.update(organization_id, default_currency=currency)
