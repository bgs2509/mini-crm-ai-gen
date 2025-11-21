"""
Permission strategies for resource access control.

This module implements the Strategy pattern for different permission
checking scenarios, following the Open/Closed Principle.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from app.models.organization_member import MemberRole


class ResourcePermissionStrategy(ABC):
    """
    Abstract base class for resource permission strategies.

    Implements the Strategy pattern to allow different permission
    checking logic without modifying existing code.
    """

    @abstractmethod
    def can_modify(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """
        Check if user can modify a resource.

        Args:
            user_id: Current user ID
            resource_owner_id: Resource owner ID
            user_role: User's role in organization

        Returns:
            True if user can modify resource
        """
        pass

    @abstractmethod
    def can_delete(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """
        Check if user can delete a resource.

        Args:
            user_id: Current user ID
            resource_owner_id: Resource owner ID
            user_role: User's role in organization

        Returns:
            True if user can delete resource
        """
        pass


class AdminOrOwnerStrategy(ResourcePermissionStrategy):
    """
    Strategy that allows only admins and owners to access resources.

    Used for sensitive operations like organization management.
    """

    def can_modify(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """Only admins and owners can modify."""
        return user_role in (MemberRole.ADMIN, MemberRole.OWNER)

    def can_delete(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """Only admins and owners can delete."""
        return user_role in (MemberRole.ADMIN, MemberRole.OWNER)


class OwnerOrResourceOwnerStrategy(ResourcePermissionStrategy):
    """
    Strategy that allows admins, owners, or resource owners to access resources.

    Used for most resource operations (contacts, deals, tasks).
    """

    def can_modify(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """Admins, owners, or resource owner can modify."""
        if user_role in (MemberRole.ADMIN, MemberRole.OWNER):
            return True
        return user_id == resource_owner_id

    def can_delete(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """Admins, owners, or resource owner can delete."""
        if user_role in (MemberRole.ADMIN, MemberRole.OWNER):
            return True
        return user_id == resource_owner_id


class ManagerOrResourceOwnerStrategy(ResourcePermissionStrategy):
    """
    Strategy that allows managers and higher, or resource owners to access resources.

    Used for team-level operations where managers need visibility.
    """

    def can_modify(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """Managers and above, or resource owner can modify."""
        if user_role in (MemberRole.MANAGER, MemberRole.ADMIN, MemberRole.OWNER):
            return True
        return user_id == resource_owner_id

    def can_delete(
        self,
        user_id: UUID,
        resource_owner_id: UUID,
        user_role: MemberRole
    ) -> bool:
        """Managers and above, or resource owner can delete."""
        if user_role in (MemberRole.MANAGER, MemberRole.ADMIN, MemberRole.OWNER):
            return True
        return user_id == resource_owner_id


class ViewPermissionStrategy(ABC):
    """Abstract base class for view permission strategies."""

    @abstractmethod
    def can_view(self, user_role: MemberRole) -> bool:
        """
        Check if user can view resources.

        Args:
            user_role: User's role in organization

        Returns:
            True if user can view resources
        """
        pass


class AllRolesCanViewStrategy(ViewPermissionStrategy):
    """Strategy that allows all roles to view resources."""

    def can_view(self, user_role: MemberRole) -> bool:
        """All roles can view."""
        return True


class ManagerAndAboveCanViewStrategy(ViewPermissionStrategy):
    """Strategy that allows only managers and above to view resources."""

    def can_view(self, user_role: MemberRole) -> bool:
        """Only managers and above can view."""
        return user_role in (MemberRole.MANAGER, MemberRole.ADMIN, MemberRole.OWNER)
