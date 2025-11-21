"""
Database models package.
Import all models here to ensure they are registered with SQLAlchemy.
"""
from app.models.base import Base, UUIDMixin, TimestampMixin, UpdateTimestampMixin
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, MemberRole
from app.models.contact import Contact
from app.models.deal import Deal, DealStatus, DealStage
from app.models.task import Task
from app.models.activity import Activity, ActivityType

__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "UpdateTimestampMixin",
    "User",
    "Organization",
    "OrganizationMember",
    "MemberRole",
    "Contact",
    "Deal",
    "DealStatus",
    "DealStage",
    "Task",
    "Activity",
    "ActivityType",
]
