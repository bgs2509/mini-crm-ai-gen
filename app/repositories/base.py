"""
Base repository class with generic CRUD operations.
"""
from typing import Generic, TypeVar, Type, Optional, List, Any, Protocol, cast
from uuid import UUID

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.exceptions import NotFoundError


class HasId(Protocol):
    """Protocol for models that have an id attribute."""
    id: UUID


# Type variable for model class
ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with generic CRUD operations.

    Provides common database operations for all models.
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get entity by ID.

        Args:
            id: Entity UUID

        Returns:
            Entity or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_by_id_or_404(self, id: UUID) -> ModelType:
        """
        Get entity by ID or raise 404 error.

        Args:
            id: Entity UUID

        Returns:
            Entity

        Raises:
            NotFoundError: If entity not found
        """
        entity = await self.get_by_id(id)
        if not entity:
            raise NotFoundError(self.model.__name__, id)
        return entity

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """
        Get all entities with optional filters.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            **filters: Additional filter conditions

        Returns:
            List of entities
        """
        query = select(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, **filters) -> int:
        """
        Count entities with optional filters.

        Args:
            **filters: Filter conditions

        Returns:
            Count of entities
        """
        query = select(func.count()).select_from(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, **data) -> ModelType:
        """
        Create new entity.

        Args:
            **data: Entity data

        Returns:
            Created entity
        """
        entity = self.model(**data)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, id: UUID, **data) -> ModelType:
        """
        Update entity by ID.

        Args:
            id: Entity UUID
            **data: Update data

        Returns:
            Updated entity

        Raises:
            NotFoundError: If entity not found
        """
        entity = await self.get_by_id_or_404(id)

        for field, value in data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update_by_query(self, values: dict[str, Any], **filters) -> int:
        """
        Update entities matching filters.

        Args:
            values: Values to update
            **filters: Filter conditions

        Returns:
            Number of updated rows
        """
        query = update(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        query = query.values(**values)
        result = await self.db.execute(query)
        return result.rowcount

    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity UUID

        Returns:
            True if entity was deleted

        Raises:
            NotFoundError: If entity not found
        """
        entity = await self.get_by_id_or_404(id)
        await self.db.delete(entity)
        await self.db.flush()
        return True

    async def delete_by_query(self, **filters) -> int:
        """
        Delete entities matching filters.

        Args:
            **filters: Filter conditions

        Returns:
            Number of deleted rows
        """
        query = delete(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.db.execute(query)
        return result.rowcount

    async def exists(self, **filters) -> bool:
        """
        Check if entity exists with given filters.

        Args:
            **filters: Filter conditions

        Returns:
            True if entity exists
        """
        count = await self.count(**filters)
        return count > 0
