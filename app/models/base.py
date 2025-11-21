"""
Base model class with common fields for all database models.
"""
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Type annotation for type checkers
    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TimestampMixin:
    """Mixin that adds created_at timestamp field."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )


class UpdateTimestampMixin(TimestampMixin):
    """Mixin that adds created_at and updated_at timestamp fields."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class UUIDMixin:
    """Mixin that adds UUID primary key."""

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )
