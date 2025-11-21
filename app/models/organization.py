"""
Organization model for multi-tenancy.
"""
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization_member import OrganizationMember
    from app.models.contact import Contact
    from app.models.deal import Deal


class Organization(Base, UUIDMixin, TimestampMixin):
    """
    Organization model for multi-tenant isolation.

    Attributes:
        id: Organization UUID (primary key)
        name: Organization name
        default_currency: Default currency for deals (ISO 4217 code)
        created_at: Organization creation timestamp
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    default_currency: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        default=None
    )

    # Relationships
    members: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
