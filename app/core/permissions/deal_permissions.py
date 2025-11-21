"""
Deal-specific permission checker.

This module handles permission checks specific to deal operations,
following the Single Responsibility Principle.
"""
from app.models.organization_member import MemberRole


class DealPermissionChecker:
    """
    Permission checker for deal-specific operations.

    Handles permission checks unique to deal management like
    stage transitions, status changes, and deal-specific workflows.
    """

    @staticmethod
    def can_change_stage_backward(user_role: MemberRole) -> bool:
        """
        Check if user can move deal stage backward.

        Args:
            user_role: User's role

        Returns:
            True if user can move stage backward (admin or owner)
        """
        return user_role in (MemberRole.ADMIN, MemberRole.OWNER)

    @staticmethod
    def can_create_deal(user_role: MemberRole) -> bool:
        """
        Check if user can create deals.

        Args:
            user_role: User's role

        Returns:
            True (all roles can create deals)
        """
        return True

    @staticmethod
    def can_force_close_deal(user_role: MemberRole) -> bool:
        """
        Check if user can force close a deal regardless of rules.

        Args:
            user_role: User's role

        Returns:
            True if user is admin or owner
        """
        return user_role in (MemberRole.ADMIN, MemberRole.OWNER)

    @staticmethod
    def can_change_deal_owner(user_role: MemberRole) -> bool:
        """
        Check if user can change deal ownership.

        Args:
            user_role: User's role

        Returns:
            True if user is manager, admin, or owner
        """
        return user_role in (MemberRole.MANAGER, MemberRole.ADMIN, MemberRole.OWNER)

    @staticmethod
    def can_view_deal_analytics(user_role: MemberRole) -> bool:
        """
        Check if user can view deal analytics.

        Args:
            user_role: User's role

        Returns:
            True if user is manager, admin, or owner
        """
        return user_role in (MemberRole.MANAGER, MemberRole.ADMIN, MemberRole.OWNER)
