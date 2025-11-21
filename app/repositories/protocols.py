"""
Repository protocol definitions for dependency inversion.

This module defines Protocol interfaces for repositories to enable
loose coupling and easier testing.
"""
from typing import Protocol, Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, MemberRole
from app.models.contact import Contact
from app.models.deal import Deal, DealStatus, DealStage
from app.models.task import Task
from app.models.activity import Activity, ActivityType


class IBaseRepository(Protocol):
    """Base repository protocol with common CRUD operations."""

    async def get_by_id(self, id: UUID) -> Optional[Any]:
        """Get entity by ID."""
        ...

    async def get_by_id_or_404(self, id: UUID) -> Any:
        """Get entity by ID or raise 404 error."""
        ...

    async def create(self, **data) -> Any:
        """Create new entity."""
        ...

    async def update(self, id: UUID, **data) -> Any:
        """Update entity by ID."""
        ...

    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        ...

    async def count(self, **filters) -> int:
        """Count entities with optional filters."""
        ...


class IUserRepository(IBaseRepository, Protocol):
    """User repository protocol."""

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        ...

    async def email_exists(self, email: str) -> bool:
        """Check if email exists."""
        ...

    async def create_user(self, email: str, hashed_password: str, name: str) -> User:
        """Create new user."""
        ...


class IOrganizationRepository(IBaseRepository, Protocol):
    """Organization repository protocol."""

    async def create_organization(self, name: str, default_currency: Optional[str] = None) -> Organization:
        """Create new organization."""
        ...

    async def update_organization(self, org_id: UUID, **data) -> Organization:
        """Update organization."""
        ...


class IOrganizationMemberRepository(IBaseRepository, Protocol):
    """Organization member repository protocol."""

    async def add_member(self, organization_id: UUID, user_id: UUID, role: MemberRole) -> OrganizationMember:
        """Add member to organization."""
        ...

    async def get_user_organizations(self, user_id: UUID) -> List[OrganizationMember]:
        """Get all organizations for user."""
        ...

    async def get_member(self, organization_id: UUID, user_id: UUID) -> Optional[OrganizationMember]:
        """Get organization member."""
        ...

    async def remove_member(self, organization_id: UUID, user_id: UUID) -> bool:
        """Remove member from organization."""
        ...

    async def get_organization_members(self, organization_id: UUID) -> List[OrganizationMember]:
        """Get all members of an organization."""
        ...

    async def get_membership(
        self, organization_id: UUID, user_id: UUID
    ) -> Optional[OrganizationMember]:
        """Get membership by organization and user."""
        ...

    async def update_role(
        self, organization_id: UUID, user_id: UUID, role: MemberRole
    ) -> OrganizationMember:
        """Update member role."""
        ...

    async def count_by_role(self, organization_id: UUID, role: MemberRole) -> int:
        """Count members by role in organization."""
        ...


class IContactRepository(IBaseRepository, Protocol):
    """Contact repository protocol."""

    async def email_exists_in_org(
        self,
        organization_id: UUID,
        email: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if email exists in organization."""
        ...

    async def search_contacts(
        self,
        organization_id: UUID,
        search_query: Optional[str] = None,
        owner_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Contact]:
        """Search contacts with filters."""
        ...


class IDealRepository(IBaseRepository, Protocol):
    """Deal repository protocol."""

    async def search_deals(
        self,
        organization_id: UUID,
        search_query: Optional[str] = None,
        status: Optional[DealStatus] = None,
        stage: Optional[DealStage] = None,
        owner_id: Optional[UUID] = None,
        contact_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Deal]:
        """Search deals with filters."""
        ...

    async def count_by_contact(
        self,
        contact_id: UUID,
        exclude_status: Optional[List[DealStatus]] = None
    ) -> int:
        """Count deals for a contact."""
        ...

    async def get_summary_by_status(self, organization_id: UUID) -> List[Dict[str, Any]]:
        """Get deal summary grouped by status."""
        ...

    async def get_summary_by_stage(self, organization_id: UUID) -> List[Dict[str, Any]]:
        """Get deal summary grouped by stage."""
        ...

    async def get_total_value(
        self,
        organization_id: UUID,
        status: Optional[DealStatus] = None
    ) -> Decimal:
        """Get total value of deals."""
        ...

    async def get_average_deal_value(
        self,
        organization_id: UUID,
        status: Optional[DealStatus] = None
    ) -> Decimal:
        """Get average deal value."""
        ...


class ITaskRepository(IBaseRepository, Protocol):
    """Task repository protocol."""

    async def get_tasks_by_deal(
        self,
        deal_id: UUID,
        only_open: bool = False
    ) -> List[Task]:
        """Get tasks for a deal."""
        ...

    async def search_tasks(
        self,
        organization_id: UUID,
        deal_id: Optional[UUID] = None,
        only_open: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Search tasks with filters."""
        ...

    async def get_by_deal(
        self,
        deal_id: UUID,
        include_done: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks by deal ID."""
        ...

    async def get_overdue_tasks(self, deal_id: UUID) -> List[Task]:
        """Get overdue tasks for a deal."""
        ...

    async def mark_as_done(self, task_id: UUID) -> Task:
        """Mark task as done."""
        ...

    async def mark_as_undone(self, task_id: UUID) -> Task:
        """Mark task as not done."""
        ...


class IActivityRepository(IBaseRepository, Protocol):
    """Activity repository protocol."""

    async def create_activity(
        self,
        deal_id: UUID,
        activity_type: ActivityType,
        payload: Dict[str, Any],
        author_id: Optional[UUID] = None
    ) -> Activity:
        """Create activity for a deal."""
        ...

    async def get_deal_activities(
        self,
        deal_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Activity]:
        """Get activities for a deal."""
        ...

    async def get_deal_timeline(
        self,
        deal_id: UUID,
        activity_type: Optional[ActivityType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Activity]:
        """Get activity timeline for a deal."""
        ...

    async def count_activities(
        self,
        deal_id: UUID,
        activity_type: Optional[ActivityType] = None
    ) -> int:
        """Count activities for a deal."""
        ...
