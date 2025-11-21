"""
User model for authentication and user management.
"""
from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization_member import OrganizationMember
    from app.models.contact import Contact
    from app.models.deal import Deal
    from app.models.activity import Activity


class User(Base, UUIDMixin, TimestampMixin):
    """
    User model for system users.

    Attributes:
        id: User UUID (primary key)
        email: User email (unique)
        hashed_password: Bcrypt hashed password
        name: User full name
        created_at: Account creation timestamp
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Relationships
    organization_memberships: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    owned_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="owner",
        foreign_keys="Contact.owner_id"
    )
    owned_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="owner",
        foreign_keys="Deal.owner_id"
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        back_populates="author",
        foreign_keys="Activity.author_id"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
