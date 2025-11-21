"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.jwt import get_user_id_from_token
from app.core.exceptions import (
    InvalidTokenError,
    AuthenticationError,
    OrganizationAccessError,
    NotFoundError
)
from app.models.user import User
from app.models.organization_member import OrganizationMember, MemberRole


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        AuthenticationError: If token is missing or invalid
        NotFoundError: If user not found
    """
    if not credentials:
        raise AuthenticationError("Authentication required")

    token = credentials.credentials

    try:
        user_id = get_user_id_from_token(token)
    except InvalidTokenError:
        raise AuthenticationError("Invalid or expired token")

    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User", user_id)

    return user


async def get_current_organization(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> tuple[UUID, MemberRole]:
    """
    Get current organization from X-Organization-Id header and verify user membership.

    Args:
        x_organization_id: Organization ID from header
        user: Current authenticated user
        db: Database session

    Returns:
        Tuple of (organization_id, user_role)

    Raises:
        AuthenticationError: If X-Organization-Id header is missing or invalid
        OrganizationAccessError: If user is not a member of the organization
    """
    if not x_organization_id:
        raise AuthenticationError("X-Organization-Id header is required")

    try:
        org_id = UUID(x_organization_id)
    except ValueError:
        raise AuthenticationError("Invalid X-Organization-Id format")

    # Check if user is member of organization
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise OrganizationAccessError(str(org_id))

    return org_id, membership.role


class RoleChecker:
    """
    Dependency to check if user has minimum required role.

    Example:
        @app.get("/admin", dependencies=[Depends(RoleChecker(MemberRole.ADMIN))])
        async def admin_endpoint():
            ...
    """

    def __init__(self, minimum_role: MemberRole):
        """
        Initialize role checker.

        Args:
            minimum_role: Minimum required role
        """
        self.minimum_role = minimum_role

    async def __call__(
        self,
        org_info: tuple[UUID, MemberRole] = Depends(get_current_organization)
    ) -> tuple[UUID, MemberRole]:
        """
        Check if user has minimum required role.

        Args:
            org_info: Tuple of (organization_id, user_role)

        Returns:
            Organization info tuple

        Raises:
            AuthorizationError: If user doesn't have sufficient role
        """
        org_id, user_role = org_info

        from app.core.permissions import permissions
        permissions.check_minimum_role(user_role, self.minimum_role)

        return org_info


def require_admin() -> RoleChecker:
    """
    Dependency to require admin role.

    Returns:
        RoleChecker dependency
    """
    return RoleChecker(MemberRole.ADMIN)


def require_manager() -> RoleChecker:
    """
    Dependency to require manager role or higher.

    Returns:
        RoleChecker dependency
    """
    return RoleChecker(MemberRole.MANAGER)


def require_owner() -> RoleChecker:
    """
    Dependency to require owner role.

    Returns:
        RoleChecker dependency
    """
    return RoleChecker(MemberRole.OWNER)
