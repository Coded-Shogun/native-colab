"""
Pytest Configuration and Fixtures
Provides reusable test fixtures for the entire test suite
"""

import os
import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Load test environment variables before importing app
from dotenv import load_dotenv
env_file = os.path.join(os.path.dirname(__file__), '..', '.env.test')
load_dotenv(env_file, override=True)

from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings

# Test database URL
# Use in-memory SQLite for tests if DATABASE_URL is not set
if hasattr(settings, 'POSTGRES_DB') and settings.POSTGRES_DB:
    TEST_DATABASE_URL = settings.DATABASE_URL.replace(
        settings.POSTGRES_DB,
        f"{settings.POSTGRES_DB}_test"
    )
else:
    # Use the DATABASE_URL as-is (SQLite or other)
    TEST_DATABASE_URL = settings.DATABASE_URL


# ============================================
# Event Loop Fixture
# ============================================
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# Database Engine and Session Fixtures
# ============================================
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """
    Create a test database engine.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================
# FastAPI Test Client Fixture
# ============================================
@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test HTTP client with database session override.
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================
# Authentication Fixtures
# ============================================
@pytest.fixture
def test_user_data():
    """
    Provide test user data.
    """
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
    }


@pytest.fixture
def test_admin_data():
    """
    Provide test admin user data.
    """
    return {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Admin User",
    }


@pytest_asyncio.fixture
async def test_user(client: AsyncClient, test_user_data):
    """
    Create a test user in the database.
    """
    response = await client.post(
        "/api/v1/auth/register",
        json=test_user_data
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_user_token(client: AsyncClient, test_user_data):
    """
    Get an access token for the test user.
    """
    # Register user first
    await client.post("/api/v1/auth/register", json=test_user_data)

    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        }
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user_token: str
) -> AsyncClient:
    """
    Create an authenticated test client.
    """
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_user_token}"
    }
    return client


# ============================================
# Workspace Fixtures
# ============================================
@pytest.fixture
def test_workspace_data():
    """
    Provide test workspace data.
    """
    return {
        "name": "Test Workspace",
        "slug": "test-workspace",
    }


@pytest_asyncio.fixture
async def test_workspace(
    authenticated_client: AsyncClient,
    test_workspace_data
):
    """
    Create a test workspace.
    """
    response = await authenticated_client.post(
        "/api/v1/workspaces",
        json=test_workspace_data
    )
    assert response.status_code == 201
    return response.json()
