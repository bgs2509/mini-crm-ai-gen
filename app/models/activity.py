"""
Activity model for tracking deal timeline and changes.
"""
from typing import TYPE_CHECKING, Optional, Any
from uuid import UUID
from enum import Enum

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.deal import Deal
    from app.models.user import User


class ActivityType(str, Enum):
    """
    Activity type enumeration.

    Types:
    - COMMENT: User-created comment
    - STATUS_CHANGED: Deal status changed
    - STAGE_CHANGED: Deal stage changed
    - TASK_CREATED: Task was created
    - TASK_COMPLETED: Task was marked as done
    - SYSTEM: System-generated activity
    """

    COMMENT = "comment"
    STATUS_CHANGED = "status_changed"
    STAGE_CHANGED = "stage_changed"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    SYSTEM = "system"


class Activity(Base, UUIDMixin, TimestampMixin):
    """
    Activity model for tracking deal timeline.

    Attributes:
        id: Activity UUID (primary key)
        deal_id: Deal UUID (foreign key)
        author_id: User UUID who created activity (foreign key, nullable for system activities)
        type: Activity type
        payload: JSON payload with activity details
        created_at: Activity creation timestamp
    """

    __tablename__ = "activities"

    deal_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_id: Mapped[Optional[UUID]] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    type: Mapped[ActivityType] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    # Relationships
    deal: Mapped["Deal"] = relationship(
        "Deal",
        back_populates="activities"
    )
    author: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="activities",
        foreign_keys=[author_id]
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, type={self.type}, deal_id={self.deal_id})>"
