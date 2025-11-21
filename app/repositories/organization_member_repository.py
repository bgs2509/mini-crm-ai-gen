"""
Organization member repository for membership management operations.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.organization_member import OrganizationMember, MemberRole
from app.repositories.base import BaseRepository


class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    """Repository for OrganizationMember model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize organization member repository.

        Args:
            db: Database session
        """
        super().__init__(OrganizationMember, db)

    async def get_user_organizations(self, user_id: UUID) -> List[OrganizationMember]:
        """
        Get all organizations user is a member of with roles.

        Args:
            user_id: User UUID

        Returns:
            List of OrganizationMember with organization loaded
        """
        result = await self.db.execute(
            select(OrganizationMember)
            .options(joinedload(OrganizationMember.organization))
            .where(OrganizationMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_organization_members(
        self,
        organization_id: UUID
    ) -> List[OrganizationMember]:
        """
        Get all members of an organization with roles.

        Args:
            organization_id: Organization UUID

        Returns:
            List of OrganizationMember with user loaded
        """
        result = await self.db.execute(
            select(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == organization_id)
        )
        return list(result.scalars().all())

    async def get_membership(
        self,
        organization_id: UUID,
        user_id: UUID
    ) -> Optional[OrganizationMember]:
        """
        Get membership for user in organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            OrganizationMember or None if not found
        """
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def is_member(
        self,
        organization_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Check if user is a member of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is a member
        """
        membership = await self.get_membership(organization_id, user_id)
        return membership is not None

    async def get_user_role(
        self,
        organization_id: UUID,
        user_id: UUID
    ) -> Optional[MemberRole]:
        """
        Get user's role in organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            MemberRole or None if not a member
        """
        membership = await self.get_membership(organization_id, user_id)
        return membership.role if membership else None

    async def add_member(
        self,
        organization_id: UUID,
        user_id: UUID,
        role: MemberRole = MemberRole.MEMBER
    ) -> OrganizationMember:
        """
        Add user as member to organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID
            role: Member role

        Returns:
            Created membership
        """
        return await self.create(
            organization_id=organization_id,
            user_id=user_id,
            role=role
        )

    async def update_role(
        self,
        organization_id: UUID,
        user_id: UUID,
        role: MemberRole
    ) -> OrganizationMember:
        """
        Update member role in organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID
            role: New role

        Returns:
            Updated membership
        """
        membership = await self.get_membership(organization_id, user_id)
        if not membership:
            raise ValueError("Membership not found")

        return await self.update(membership.id, role=role)

    async def remove_member(
        self,
        organization_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Remove user from organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if member was removed
        """
        membership = await self.get_membership(organization_id, user_id)
        if not membership:
            return False

        await self.delete(membership.id)
        return True

    async def count_organization_members(self, organization_id: UUID) -> int:
        """
        Count members in organization.

        Args:
            organization_id: Organization UUID

        Returns:
            Number of members
        """
        return await self.count(organization_id=organization_id)

    async def count_by_role(
        self,
        organization_id: UUID,
        role: MemberRole
    ) -> int:
        """
        Count members in organization with specific role.

        Args:
            organization_id: Organization UUID
            role: Member role to count

        Returns:
            Number of members with this role
        """
        return await self.count(organization_id=organization_id, role=role)
