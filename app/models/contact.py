"""
Contact model for CRM contacts management.
"""
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.deal import Deal


class Contact(Base, UUIDMixin, TimestampMixin):
    """
    Contact model for managing CRM contacts.

    Attributes:
        id: Contact UUID (primary key)
        organization_id: Organization UUID (foreign key)
        owner_id: User UUID who owns this contact (foreign key)
        name: Contact full name
        email: Contact email
        phone: Contact phone number
        created_at: Contact creation timestamp
    """

    __tablename__ = "contacts"

    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    owner_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="contacts"
    )
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_contacts",
        foreign_keys=[owner_id]
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="contact",
        passive_deletes='all'
        # No cascade - contacts with active deals should not be deleted
        # passive_deletes='all' lets database handle the RESTRICT constraint
    )

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, name={self.name}, email={self.email})>"
