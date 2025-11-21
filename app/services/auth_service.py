"""
Authentication service for user registration and login.
"""
from typing import List, Tuple, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.core.jwt import create_token_pair
from app.core.exceptions import AuthenticationError, AlreadyExistsError
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.protocols import (
    IUserRepository,
    IOrganizationRepository,
    IOrganizationMemberRepository
)
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import MemberRole


class AuthService:
    """Service for authentication operations with dependency inversion."""

    def __init__(
        self,
        db: AsyncSession,
        user_repo: Optional[IUserRepository] = None,
        org_repo: Optional[IOrganizationRepository] = None,
        member_repo: Optional[IOrganizationMemberRepository] = None
    ):
        """
        Initialize auth service.

        Args:
            db: Database session
            user_repo: User repository (uses default if None)
            org_repo: Organization repository (uses default if None)
            member_repo: Organization member repository (uses default if None)
        """
        self.db = db
        self.user_repo = user_repo or UserRepository(db)
        self.org_repo = org_repo or OrganizationRepository(db)
        self.member_repo = member_repo or OrganizationMemberRepository(db)

    async def register_user(
        self,
        email: str,
        password: str,
        name: str,
        organization_name: str
    ) -> Tuple[User, Organization, dict]:
        """
        Register new user with organization.

        Creates user, organization, and adds user as owner.

        Args:
            email: User email
            password: Plain password
            name: User full name
            organization_name: Organization name

        Returns:
            Tuple of (user, organization, tokens)

        Raises:
            AlreadyExistsError: If email already exists
        """
        # Check if email exists
        if await self.user_repo.email_exists(email):
            raise AlreadyExistsError("User", "email", email)

        # Hash password
        hashed_password = hash_password(password)

        # Create user
        user = await self.user_repo.create_user(
            email=email,
            hashed_password=hashed_password,
            name=name
        )

        # Create organization
        organization = await self.org_repo.create_organization(
            name=organization_name
        )

        # Add user as owner
        await self.member_repo.add_member(
            organization_id=organization.id,
            user_id=user.id,
            role=MemberRole.OWNER
        )

        # Commit transaction
        await self.db.commit()

        # Generate tokens
        tokens = create_token_pair(user.id)

        return user, organization, tokens

    async def login_user(
        self,
        email: str,
        password: str
    ) -> Tuple[User, List, dict]:
        """
        Authenticate user and return tokens.

        Args:
            email: User email
            password: Plain password

        Returns:
            Tuple of (user, organization_members, tokens)
            where organization_members is List[OrganizationMember]

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)

        if not user:
            raise AuthenticationError("Invalid email or password")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        # Get user organizations
        organizations = await self.member_repo.get_user_organizations(user.id)

        # Generate tokens
        tokens = create_token_pair(user.id)

        return user, organizations, tokens

    async def refresh_tokens(self, user_id: UUID) -> dict:
        """
        Refresh access and refresh tokens.

        Args:
            user_id: User UUID

        Returns:
            New token pair

        Raises:
            AuthenticationError: If user not found
        """
        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        # Generate new tokens
        return create_token_pair(user_id)
