"""
User repository for user management operations.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user repository.

        Args:
            db: Database session
        """
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email to check

        Returns:
            True if email exists
        """
        user = await self.get_by_email(email)
        return user is not None

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        name: str
    ) -> User:
        """
        Create new user.

        Args:
            email: User email
            hashed_password: Hashed password
            name: User full name

        Returns:
            Created user
        """
        return await self.create(
            email=email,
            hashed_password=hashed_password,
            name=name
        )
