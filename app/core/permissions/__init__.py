"""
Permission system for role-based access control.

This package provides a modular permission system following SOLID principles.
"""
from app.core.permissions.member_permissions import MemberPermissionChecker
from app.core.permissions.resource_permissions import ResourcePermissionChecker
from app.core.permissions.deal_permissions import DealPermissionChecker
from app.core.permissions.compat import PermissionChecker, permissions
from app.core.permissions.strategies import (
    ResourcePermissionStrategy,
    AdminOrOwnerStrategy,
    OwnerOrResourceOwnerStrategy,
    ManagerOrResourceOwnerStrategy,
    ViewPermissionStrategy,
    AllRolesCanViewStrategy,
    ManagerAndAboveCanViewStrategy
)

# Global instances for backward compatibility
member_permissions = MemberPermissionChecker()
resource_permissions = ResourcePermissionChecker()
deal_permissions = DealPermissionChecker()

__all__ = [
    "MemberPermissionChecker",
    "ResourcePermissionChecker",
    "DealPermissionChecker",
    "ResourcePermissionStrategy",
    "AdminOrOwnerStrategy",
    "OwnerOrResourceOwnerStrategy",
    "ManagerOrResourceOwnerStrategy",
    "ViewPermissionStrategy",
    "AllRolesCanViewStrategy",
    "ManagerAndAboveCanViewStrategy",
    "member_permissions",
    "resource_permissions",
    "deal_permissions",
    "PermissionChecker",
    "permissions",
]
