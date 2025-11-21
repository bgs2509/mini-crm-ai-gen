"""
Task model for deal-related tasks management.
"""
from typing import TYPE_CHECKING, Optional
from uuid import UUID
from datetime import date

from sqlalchemy import String, ForeignKey, Boolean, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.deal import Deal


class Task(Base, UUIDMixin, TimestampMixin):
    """
    Task model for managing deal-related tasks.

    Attributes:
        id: Task UUID (primary key)
        deal_id: Deal UUID (foreign key)
        title: Task title
        description: Task description (optional)
        due_date: Task due date (optional)
        is_done: Task completion status
        created_at: Task creation timestamp
    """

    __tablename__ = "tasks"

    deal_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True
    )
    is_done: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship(
        "Deal",
        back_populates="tasks"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, is_done={self.is_done})>"
