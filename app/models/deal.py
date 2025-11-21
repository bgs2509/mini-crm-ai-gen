"""
Deal model for CRM pipeline management.
"""
from typing import TYPE_CHECKING
from uuid import UUID
from enum import Enum
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Numeric, Enum as SQLAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.models.base import Base, UUIDMixin, UpdateTimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.contact import Contact
    from app.models.user import User
    from app.models.task import Task
    from app.models.activity import Activity


class DealStatus(str, Enum):
    """
    Deal status enumeration.

    Flow: new → in_progress → won/lost (terminal states)
    """

    NEW = "new"
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"

    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (won or lost)."""
        return self in (DealStatus.WON, DealStatus.LOST)


class DealStage(str, Enum):
    """
    Deal stage enumeration for pipeline visualization.

    Sequential flow: qualification → proposal → negotiation → closed
    """

    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED = "closed"


class Deal(Base, UUIDMixin, UpdateTimestampMixin):
    """
    Deal model for managing sales opportunities.

    Attributes:
        id: Deal UUID (primary key)
        organization_id: Organization UUID (foreign key)
        contact_id: Contact UUID (foreign key)
        owner_id: User UUID who owns this deal (foreign key)
        title: Deal title/name
        amount: Deal value
        currency: Currency code (ISO 4217)
        status: Deal status (new, in_progress, won, lost)
        stage: Deal stage (qualification, proposal, negotiation, closed)
        created_at: Deal creation timestamp
        updated_at: Deal last update timestamp
    """

    __tablename__ = "deals"

    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contact_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    owner_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
        index=True
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD"
    )
    status: Mapped[DealStatus] = mapped_column(
        SQLAEnum(DealStatus, native_enum=False, length=20, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DealStatus.NEW,
        index=True
    )
    stage: Mapped[DealStage] = mapped_column(
        SQLAEnum(DealStage, native_enum=False, length=20, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DealStage.QUALIFICATION,
        index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="deals"
    )
    contact: Mapped["Contact"] = relationship(
        "Contact",
        back_populates="deals"
    )
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_deals",
        foreign_keys=[owner_id]
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="deal",
        cascade="all, delete-orphan"
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        back_populates="deal",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Deal(id={self.id}, title={self.title}, "
            f"amount={self.amount}, status={self.status})>"
        )
