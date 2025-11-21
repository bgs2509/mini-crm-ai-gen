"""
API helper utilities for common operations.

This module provides reusable utility functions for API endpoints to avoid code duplication
and maintain consistency across different endpoints.
"""
from uuid import UUID
from typing import Any

from app.core.exceptions import NotFoundError


def verify_resource_organization(
    resource: Any,
    org_id: UUID,
    resource_type: str,
    resource_id: UUID
) -> None:
    """
    Verify that a resource belongs to the specified organization.

    This is a common pattern used across multiple API endpoints to ensure
    that users can only access resources within their current organization context.

    Args:
        resource: Resource entity with organization_id attribute
        org_id: Expected organization ID
        resource_type: Resource type name for error message (e.g., "Deal", "Contact", "Task")
        resource_id: Resource ID for error message

    Raises:
        NotFoundError: If resource doesn't belong to the specified organization

    Example:
        >>> deal = await repo.get_by_id_or_404(deal_id)
        >>> verify_resource_organization(deal, org_id, "Deal", deal_id)
    """
    if resource.organization_id != org_id:
        raise NotFoundError(resource_type, resource_id)
