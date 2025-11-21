"""
Database configuration and session management using SQLAlchemy 2.0 async.
"""
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Create async engine with connection pooling
# For testing, use NullPool without pool parameters
engine: AsyncEngine
if settings.is_testing:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        poolclass=NullPool,  # Disable pooling for tests
    )
else:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=settings.db_pool_pre_ping,
        pool_recycle=3600,  # Recycle connections after 1 hour
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager to get async database session.

    Yields:
        AsyncSession: Database session

    Example:
        async with get_db_context() as db:
            result = await db.execute(select(User))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    Note: In production, use Alembic migrations instead.
    """
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all database tables.
    Warning: This will delete all data!
    """
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db() -> None:
    """Close database engine and all connections."""
    await engine.dispose()
