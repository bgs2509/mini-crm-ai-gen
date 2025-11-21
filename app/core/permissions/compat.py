"""
Role-based access control (RBAC) system for authorization.

DEPRECATED: This module is kept for backward compatibility.
Use app.core.permissions package instead.
"""
from uuid import UUID

from app.models.organization_member import MemberRole


class PermissionChecker:
    """
    Permission checker for role-based access control.

    DEPRECATED: Use specialized permission checkers from app.core.permissions package:
    - MemberPermissionChecker for member operations
    - ResourcePermissionChecker for resource operations
    - DealPermissionChecker for deal-specific operations

    This class is kept for backward compatibility and delegates to new modules.

    Role hierarchy (highest to lowest):
    - OWNER: Full control over organization
    - ADMIN: Can manage members and all resources
    - MANAGER: Can manage own and team resources, forward stage changes
    - MEMBER: Can view and create own resources
    """

    _instance = None

    def __init__(self):
        """Initialize with new permission checkers."""
        from app.core.permissions.member_permissions import MemberPermissionChecker
        from app.core.permissions.resource_permissions import ResourcePermissionChecker
        from app.core.permissions.deal_permissions import DealPermissionChecker

        self._member_checker = MemberPermissionChecker()
        self._resource_checker = ResourcePermissionChecker()
        self._deal_checker = DealPermissionChecker()

    @classmethod
    def _get_instance(cls):
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def check_minimum_role(
        user_role: MemberRole,
        required_role: MemberRole,
        raise_error: bool = True
    ) -> bool:
        """
        Check if user has minimum required role.

        Delegates to MemberPermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._member_checker.check_minimum_role(user_role, required_role, raise_error)

    @staticmethod
    def can_manage_members(user_role: MemberRole) -> bool:
        """
        Check if user can manage organization members.

        Delegates to MemberPermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._member_checker.can_manage_members(user_role)

    @staticmethod
    def can_delete_organization(user_role: MemberRole) -> bool:
        """
        Check if user can delete organization.

        Delegates to MemberPermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._member_checker.can_delete_organization(user_role)

    @staticmethod
    def can_view_all_resources(user_role: MemberRole) -> bool:
        """
        Check if user can view all organization resources.

        Delegates to ResourcePermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._resource_checker.can_view_all_resources(user_role)

    @staticmethod
    def can_modify_resource(
        user_role: MemberRole,
        resource_owner_id: UUID,
        current_user_id: UUID
    ) -> bool:
        """
        Check if user can modify a resource.

        Delegates to ResourcePermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._resource_checker.can_modify_resource(
            current_user_id, resource_owner_id, user_role
        )

    @staticmethod
    def can_delete_resource(
        user_role: MemberRole,
        resource_owner_id: UUID,
        current_user_id: UUID
    ) -> bool:
        """
        Check if user can delete a resource.

        Delegates to ResourcePermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._resource_checker.can_delete_resource(
            current_user_id, resource_owner_id, user_role
        )

    @staticmethod
    def can_change_deal_stage_backward(user_role: MemberRole) -> bool:
        """
        Check if user can move deal stage backward.

        Delegates to DealPermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._deal_checker.can_change_stage_backward(user_role)

    @staticmethod
    def can_create_contact(user_role: MemberRole) -> bool:
        """
        Check if user can create contacts.

        Delegates to ResourcePermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._resource_checker.can_create_resource(user_role)

    @staticmethod
    def can_create_deal(user_role: MemberRole) -> bool:
        """
        Check if user can create deals.

        Delegates to DealPermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        return instance._deal_checker.can_create_deal(user_role)

    @staticmethod
    def check_resource_ownership(
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole,
        resource_type: str,
        resource_id: str
    ) -> None:
        """
        Check if user has ownership or sufficient role to access resource.

        Delegates to ResourcePermissionChecker.
        """
        instance = PermissionChecker._get_instance()
        instance._resource_checker.check_resource_ownership(
            user_id, resource_owner_id, user_role, resource_type, resource_id
        )


# Global permission checker instance for backward compatibility
permissions = PermissionChecker()
