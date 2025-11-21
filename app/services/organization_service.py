"""
Organization service for organization management and member operations.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    BusinessLogicError,
    AuthorizationError,
    ConflictError
)
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.user_repository import UserRepository
from app.repositories.protocols import (
    IOrganizationRepository,
    IOrganizationMemberRepository,
    IUserRepository
)
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, MemberRole
from app.core.permissions.member_permissions import MemberPermissionChecker


class OrganizationService:
    """Service for organization operations with dependency inversion."""

    def __init__(
        self,
        db: AsyncSession,
        org_repo: Optional[IOrganizationRepository] = None,
        member_repo: Optional[IOrganizationMemberRepository] = None,
        user_repo: Optional[IUserRepository] = None
    ):
        """
        Initialize organization service.

        Args:
            db: Database session
            org_repo: Organization repository (uses default if None)
            member_repo: Organization member repository (uses default if None)
            user_repo: User repository (uses default if None)
        """
        self.db = db
        self.org_repo = org_repo or OrganizationRepository(db)
        self.member_repo = member_repo or OrganizationMemberRepository(db)
        self.user_repo = user_repo or UserRepository(db)
        self.permission_checker = MemberPermissionChecker()

    async def get_user_organizations(
        self,
        user_id: UUID
    ) -> List[dict]:
        """
        Get all organizations for user with roles.

        Args:
            user_id: User UUID

        Returns:
            List of dicts with organization and role info
        """
        memberships = await self.member_repo.get_user_organizations(user_id)

        result = []
        for membership in memberships:
            result.append({
                'organization': membership.organization,
                'role': membership.role,
                'joined_at': membership.created_at
            })

        return result

    async def add_member(
        self,
        organization_id: UUID,
        user_email: str,
        role: MemberRole,
        requester_id: UUID
    ) -> OrganizationMember:
        """
        Add member to organization.

        Args:
            organization_id: Organization UUID
            user_email: Email of user to add
            role: Role to assign
            requester_id: User making the request

        Returns:
            Created membership

        Raises:
            NotFoundError: If user not found
            ValidationError: If user is already a member
            BusinessLogicError: If requester doesn't have permission
        """
        # Check requester permission
        requester_membership = await self.member_repo.get_membership(
            organization_id,
            requester_id
        )

        if not requester_membership:
            raise AuthorizationError(
                "You are not a member of this organization"
            )

        # Only owners and admins can add members
        if requester_membership.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
            raise AuthorizationError(
                "Only owners and admins can add members"
            )

        # Find user by email
        user = await self.user_repo.get_by_email(user_email)
        if not user:
            raise NotFoundError("User", user_email)

        # Check if already a member
        existing = await self.member_repo.get_membership(
            organization_id,
            user.id
        )

        if existing:
            raise BusinessLogicError(
                "User is already a member of this organization"
            )

        # Only owners can add other owners
        if role == MemberRole.OWNER and requester_membership.role != MemberRole.OWNER:
            raise AuthorizationError(
                "Only owners can add other owners"
            )

        # Create membership
        membership = await self.member_repo.add_member(
            organization_id=organization_id,
            user_id=user.id,
            role=role
        )

        await self.db.commit()
        return membership

    async def remove_member(
        self,
        organization_id: UUID,
        user_id: UUID,
        requester_id: UUID
    ) -> bool:
        """
        Remove member from organization.

        Args:
            organization_id: Organization UUID
            user_id: User to remove
            requester_id: User making the request

        Returns:
            True if removed

        Raises:
            BusinessLogicError: If operation not allowed
        """
        # Check requester permission
        requester_membership = await self.member_repo.get_membership(
            organization_id,
            requester_id
        )

        if not requester_membership:
            raise AuthorizationError(
                "You are not a member of this organization"
            )

        # Get target membership
        target_membership = await self.member_repo.get_membership(
            organization_id,
            user_id
        )

        if not target_membership:
            raise NotFoundError("Membership", user_id)

        # Only owners and admins can remove members
        if requester_membership.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
            raise AuthorizationError(
                "Only owners and admins can remove members"
            )

        # Only owners can remove owners or admins
        if target_membership.role in [MemberRole.OWNER, MemberRole.ADMIN] and requester_membership.role != MemberRole.OWNER:
            raise AuthorizationError(
                "Only owners can remove owners or admins"
            )

        # Can't remove the last owner
        if target_membership.role == MemberRole.OWNER:
            owners_count = await self.member_repo.count_by_role(
                organization_id,
                MemberRole.OWNER
            )
            if owners_count <= 1:
                raise ConflictError(
                    "Cannot remove the last owner of the organization"
                )

        result = await self.member_repo.remove_member(
            organization_id,
            user_id
        )

        await self.db.commit()
        return result

    async def update_member_role(
        self,
        organization_id: UUID,
        user_id: UUID,
        new_role: MemberRole,
        requester_id: UUID
    ) -> OrganizationMember:
        """
        Update member role.

        Args:
            organization_id: Organization UUID
            user_id: User to update
            new_role: New role
            requester_id: User making the request

        Returns:
            Updated membership

        Raises:
            BusinessLogicError: If operation not allowed
        """
        # Check requester permission
        requester_membership = await self.member_repo.get_membership(
            organization_id,
            requester_id
        )

        if not requester_membership:
            raise AuthorizationError(
                "You are not a member of this organization"
            )

        # Get target membership
        target_membership = await self.member_repo.get_membership(
            organization_id,
            user_id
        )

        if not target_membership:
            raise NotFoundError("Membership", user_id)

        # Only owners can change roles
        if requester_membership.role != MemberRole.OWNER:
            raise AuthorizationError(
                "Only owners can change member roles"
            )

        # Can't change the last owner
        if target_membership.role == MemberRole.OWNER and new_role != MemberRole.OWNER:
            owners_count = await self.member_repo.count_by_role(
                organization_id,
                MemberRole.OWNER
            )
            if owners_count <= 1:
                raise ConflictError(
                    "Cannot change the role of the last owner"
                )

        membership = await self.member_repo.update_role(
            organization_id,
            user_id,
            new_role
        )

        await self.db.commit()
        return membership

    async def get_organization_members(
        self,
        organization_id: UUID,
        requester_id: UUID
    ) -> List[OrganizationMember]:
        """
        Get all members of an organization.

        Args:
            organization_id: Organization UUID
            requester_id: User making the request

        Returns:
            List of memberships with user info

        Raises:
            BusinessLogicError: If requester is not a member
        """
        # Check requester is a member
        requester_membership = await self.member_repo.get_membership(
            organization_id,
            requester_id
        )

        if not requester_membership:
            raise AuthorizationError(
                "You are not a member of this organization"
            )

        return await self.member_repo.get_organization_members(organization_id)

    async def update_organization(
        self,
        organization_id: UUID,
        requester_id: UUID,
        name: Optional[str] = None,
        default_currency: Optional[str] = None
    ) -> Organization:
        """
        Update organization settings.

        Args:
            organization_id: Organization UUID
            requester_id: User making the request
            name: New name (optional)
            default_currency: New default currency (optional)

        Returns:
            Updated organization

        Raises:
            BusinessLogicError: If requester doesn't have permission
        """
        # Check requester permission
        requester_membership = await self.member_repo.get_membership(
            organization_id,
            requester_id
        )

        if not requester_membership:
            raise AuthorizationError(
                "You are not a member of this organization"
            )

        # Only owners and admins can update organization
        if requester_membership.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
            raise AuthorizationError(
                "Only owners and admins can update organization settings"
            )

        updates = {}

        if name is not None:
            updates['name'] = name

        if default_currency is not None:
            # Validate currency
            from app.core.config import settings
            if default_currency.upper() not in settings.supported_currencies:
                raise ValidationError(
                    f"Currency '{default_currency}' is not supported",
                    field="default_currency"
                )
            updates['default_currency'] = default_currency.upper()

        if not updates:
            org = await self.org_repo.get_by_id(organization_id)
            if not org:
                raise NotFoundError("Organization", organization_id)
            return org

        org = await self.org_repo.update(organization_id, **updates)
        await self.db.commit()
        return org
