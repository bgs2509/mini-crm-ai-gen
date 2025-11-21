"""
Pytest configuration and fixtures for testing.
"""
import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.main import app
from app.core.database import get_db
from app.core.security import hash_password

# Import Base and all models from models package to ensure they are registered with SQLAlchemy
from app.models import (  # noqa: F401
    Base,
    User,
    Organization,
    OrganizationMember,
    MemberRole,
    Contact,
    Deal,
    Task,
    Activity,
)


# Test database URL
TEST_DATABASE_URL = settings.database_url.replace("/crm_db", "/crm_test_db")

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.

    Creates all tables before each test and drops them after.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with database override.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Create test user.
    """
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=hash_password("TestPass123"),
        name="Test User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """
    Create test organization.
    """
    org = Organization(
        id=uuid4(),
        name="Test Organization",
        default_currency="USD"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_membership(
    db_session: AsyncSession,
    test_user: User,
    test_organization: Organization
) -> OrganizationMember:
    """
    Create test organization membership.
    """
    membership = OrganizationMember(
        id=uuid4(),
        organization_id=test_organization.id,
        user_id=test_user.id,
        role=MemberRole.OWNER
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)
    return membership


@pytest_asyncio.fixture
async def auth_headers(
    test_user: User,
    test_organization: Organization,
    test_membership: OrganizationMember
) -> dict:
    """
    Create authentication headers for test requests.

    Depends on test_membership to ensure user-organization relationship exists in DB.
    """
    from app.core.jwt import create_access_token

    access_token = create_access_token(test_user.id)

    return {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-Id": str(test_organization.id)
    }


@pytest_asyncio.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """
    Create test user with ADMIN role.
    """
    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123"),
        name="Admin User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin_membership(
    db_session: AsyncSession,
    test_admin_user: User,
    test_organization: Organization
) -> OrganizationMember:
    """
    Create test admin membership.
    """
    membership = OrganizationMember(
        id=uuid4(),
        organization_id=test_organization.id,
        user_id=test_admin_user.id,
        role=MemberRole.ADMIN
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)
    return membership


@pytest_asyncio.fixture
async def admin_auth_headers(
    test_admin_user: User,
    test_organization: Organization,
    test_admin_membership: OrganizationMember
) -> dict:
    """
    Create authentication headers for admin user.
    """
    from app.core.jwt import create_access_token

    access_token = create_access_token(test_admin_user.id)

    return {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-Id": str(test_organization.id)
    }


@pytest_asyncio.fixture
async def test_manager_user(db_session: AsyncSession) -> User:
    """
    Create test user with MANAGER role.
    """
    user = User(
        id=uuid4(),
        email="manager@example.com",
        hashed_password=hash_password("ManagerPass123"),
        name="Manager User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_manager_membership(
    db_session: AsyncSession,
    test_manager_user: User,
    test_organization: Organization
) -> OrganizationMember:
    """
    Create test manager membership.
    """
    membership = OrganizationMember(
        id=uuid4(),
        organization_id=test_organization.id,
        user_id=test_manager_user.id,
        role=MemberRole.MANAGER
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)
    return membership


@pytest_asyncio.fixture
async def manager_auth_headers(
    test_manager_user: User,
    test_organization: Organization,
    test_manager_membership: OrganizationMember
) -> dict:
    """
    Create authentication headers for manager user.
    """
    from app.core.jwt import create_access_token

    access_token = create_access_token(test_manager_user.id)

    return {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-Id": str(test_organization.id)
    }


@pytest_asyncio.fixture
async def test_member_user(db_session: AsyncSession) -> User:
    """
    Create test user with MEMBER role.
    """
    user = User(
        id=uuid4(),
        email="member@example.com",
        hashed_password=hash_password("MemberPass123"),
        name="Member User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_member_membership(
    db_session: AsyncSession,
    test_member_user: User,
    test_organization: Organization
) -> OrganizationMember:
    """
    Create test member membership.
    """
    membership = OrganizationMember(
        id=uuid4(),
        organization_id=test_organization.id,
        user_id=test_member_user.id,
        role=MemberRole.MEMBER
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)
    return membership


@pytest_asyncio.fixture
async def member_auth_headers(
    test_member_user: User,
    test_organization: Organization,
    test_member_membership: OrganizationMember
) -> dict:
    """
    Create authentication headers for member user.
    """
    from app.core.jwt import create_access_token

    access_token = create_access_token(test_member_user.id)

    return {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-Id": str(test_organization.id)
    }
