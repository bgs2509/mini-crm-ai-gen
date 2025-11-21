"""
Organization member model for user-organization relationships and RBAC.
"""
from typing import TYPE_CHECKING
from uuid import UUID
from enum import Enum

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.organization import Organization


class MemberRole(str, Enum):
    """
    Organization member roles for RBAC.

    Hierarchy (highest to lowest):
    - OWNER: Full control, can delete organization
    - ADMIN: Can manage members and all resources
    - MANAGER: Can manage own and team resources
    - MEMBER: Can view and create own resources
    """

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"

    @classmethod
    def get_hierarchy_level(cls, role: "MemberRole") -> int:
        """
        Get numeric hierarchy level for role comparison.

        Args:
            role: Member role

        Returns:
            Hierarchy level (higher number = more permissions)
        """
        hierarchy = {
            cls.MEMBER: 1,
            cls.MANAGER: 2,
            cls.ADMIN: 3,
            cls.OWNER: 4,
        }
        return hierarchy[role]

    def __ge__(self, other: object) -> bool:
        """Check if this role has greater or equal permissions than other."""
        if not isinstance(other, MemberRole):
            return NotImplemented
        return self.get_hierarchy_level(self) >= self.get_hierarchy_level(other)

    def __gt__(self, other: object) -> bool:
        """Check if this role has greater permissions than other."""
        if not isinstance(other, MemberRole):
            return NotImplemented
        return self.get_hierarchy_level(self) > self.get_hierarchy_level(other)

    def __le__(self, other: object) -> bool:
        """Check if this role has less or equal permissions than other."""
        if not isinstance(other, MemberRole):
            return NotImplemented
        return self.get_hierarchy_level(self) <= self.get_hierarchy_level(other)

    def __lt__(self, other: object) -> bool:
        """Check if this role has less permissions than other."""
        if not isinstance(other, MemberRole):
            return NotImplemented
        return self.get_hierarchy_level(self) < self.get_hierarchy_level(other)


class OrganizationMember(Base, UUIDMixin, TimestampMixin):
    """
    Organization member model for user membership and roles.

    Attributes:
        id: Membership UUID (primary key)
        organization_id: Organization UUID (foreign key)
        user_id: User UUID (foreign key)
        role: Member role (owner, admin, manager, member)
        created_at: Membership creation timestamp
    """

    __tablename__ = "organization_members"

    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[MemberRole] = mapped_column(
        String(20),
        nullable=False,
        default=MemberRole.MEMBER
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="members"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="organization_memberships"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_member"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OrganizationMember(id={self.id}, "
            f"org={self.organization_id}, user={self.user_id}, role={self.role})>"
        )
