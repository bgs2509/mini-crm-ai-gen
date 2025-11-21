"""
Member permission checker for organization membership operations.

This module handles permission checks related to organization member management,
following the Single Responsibility Principle.
"""
from app.models.organization_member import MemberRole
from app.core.exceptions import AuthorizationError


class MemberPermissionChecker:
    """
    Permission checker for organization member operations.

    Handles all permission checks related to member management,
    role assignments, and organization-level operations.
    """

    @staticmethod
    def check_minimum_role(
        user_role: MemberRole,
        required_role: MemberRole,
        raise_error: bool = True
    ) -> bool:
        """
        Check if user has minimum required role.

        Args:
            user_role: User's current role
            required_role: Minimum required role
            raise_error: Whether to raise error if check fails

        Returns:
            True if user has sufficient role

        Raises:
            AuthorizationError: If user doesn't have sufficient role and raise_error=True
        """
        has_permission = user_role >= required_role

        if not has_permission and raise_error:
            raise AuthorizationError(
                f"Requires {required_role.value} role or higher"
            )

        return has_permission

    @staticmethod
    def can_manage_members(user_role: MemberRole) -> bool:
        """
        Check if user can manage organization members.

        Args:
            user_role: User's role

        Returns:
            True if user can manage members (admin or owner)
        """
        return user_role in (MemberRole.ADMIN, MemberRole.OWNER)

    @staticmethod
    def can_delete_organization(user_role: MemberRole) -> bool:
        """
        Check if user can delete organization.

        Args:
            user_role: User's role

        Returns:
            True if user is owner
        """
        return user_role == MemberRole.OWNER

    @staticmethod
    def can_view_all_members(user_role: MemberRole) -> bool:
        """
        Check if user can view all organization members.

        Args:
            user_role: User's role

        Returns:
            True if user can view all members (manager, admin, owner)
        """
        return user_role in (MemberRole.MANAGER, MemberRole.ADMIN, MemberRole.OWNER)

    @staticmethod
    def can_change_member_role(
        actor_role: MemberRole,
        target_role: MemberRole,
        new_role: MemberRole
    ) -> tuple[bool, str]:
        """
        Check if user can change another member's role.

        Rules:
        - Only owners can change roles
        - Cannot change owner role (must transfer ownership)
        - Cannot promote to owner

        Args:
            actor_role: Role of user performing the action
            target_role: Current role of target member
            new_role: New role to assign

        Returns:
            Tuple of (can_change, reason)
        """
        if actor_role != MemberRole.OWNER:
            return False, "Only organization owners can change member roles"

        if target_role == MemberRole.OWNER:
            return False, "Cannot change owner role. Use transfer ownership instead."

        if new_role == MemberRole.OWNER:
            return False, "Cannot promote to owner. Use transfer ownership instead."

        return True, ""
