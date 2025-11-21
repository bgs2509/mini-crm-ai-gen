"""
Resource permission checker for entity-level access control.

This module handles permission checks for resources like contacts, deals, and tasks,
following the Single Responsibility Principle.
"""
from typing import Optional
from uuid import UUID

from app.models.organization_member import MemberRole
from app.core.exceptions import OwnershipError
from app.core.permissions.strategies import (
    ResourcePermissionStrategy,
    OwnerOrResourceOwnerStrategy
)


class ResourcePermissionChecker:
    """
    Permission checker for resource operations.

    Handles permission checks for contacts, deals, tasks, and other
    organization resources using strategy pattern.
    """

    def __init__(self, strategy: Optional[ResourcePermissionStrategy] = None):
        """
        Initialize resource permission checker.

        Args:
            strategy: Permission strategy to use (defaults to OwnerOrResourceOwnerStrategy)
        """
        self.strategy = strategy or OwnerOrResourceOwnerStrategy()

    def can_view_all_resources(self, user_role: MemberRole) -> bool:
        """
        Check if user can view all organization resources.

        Args:
            user_role: User's role

        Returns:
            True if user can view all resources (manager, admin, owner)
        """
        return user_role in (MemberRole.MANAGER, MemberRole.ADMIN, MemberRole.OWNER)

    def can_create_resource(self, user_role: MemberRole) -> bool:
        """
        Check if user can create resources.

        Args:
            user_role: User's role

        Returns:
            True (all roles can create resources)
        """
        return True

    def can_modify_resource(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """
        Check if user can modify a resource using the configured strategy.

        Args:
            user_id: Current user ID
            resource_owner_id: ID of resource owner
            user_role: User's role

        Returns:
            True if user can modify resource
        """
        return self.strategy.can_modify(user_id, resource_owner_id, user_role)

    def can_delete_resource(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """
        Check if user can delete a resource using the configured strategy.

        Args:
            user_id: Current user ID
            resource_owner_id: ID of resource owner
            user_role: User's role

        Returns:
            True if user can delete resource
        """
        return self.strategy.can_delete(user_id, resource_owner_id, user_role)

    def check_resource_ownership(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole,
        resource_type: str,
        resource_id: str
    ) -> None:
        """
        Check if user has ownership or sufficient role to access resource.

        Args:
            user_id: Current user ID
            resource_owner_id: Resource owner ID
            user_role: User's role
            resource_type: Type of resource (for error message)
            resource_id: Resource ID (for error message)

        Raises:
            OwnershipError: If user doesn't have permission
        """
        if not self.can_modify_resource(user_id, resource_owner_id, user_role):
            raise OwnershipError(resource_type, resource_id)
