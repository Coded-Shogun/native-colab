"""
Unit tests for the supabase_auth module.
"""

from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from jose import jwt
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.supabase_auth import verify_supabase_token, get_or_create_user
from app.db.models.user import User

_TEST_DB_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    supabase_id VARCHAR(255) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_verified BOOLEAN NOT NULL DEFAULT 0,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    last_login DATETIME
)
"""

# These must match the values in conftest.py's _patch_supabase_settings
TEST_SECRET = "test-supabase-jwt-secret-conftest"
TEST_SUPABASE_URL = "https://test-project.supabase.co"
TEST_ISSUER = f"{TEST_SUPABASE_URL}/auth/v1"


def _make_token(
    sub: str = "user-uuid-123",
    email: str = "test@example.com",
    exp_delta: timedelta = timedelta(hours=1),
    audience: str = "authenticated",
    extra: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "email": email,
        "aud": audience,
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
        "iss": TEST_ISSUER,
        "app_metadata": {},
        "user_metadata": {"full_name": "Test User", "avatar_url": None},
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


# ── Local db fixture (avoids broken conftest import chain) ─────────


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.execute(text(_TEST_DB_DDL))

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS users"))
    await engine.dispose()


# ── verify_supabase_token ──────────────────────────────────────────


def test_valid_token_returns_claims():
    token = _make_token()
    claims = verify_supabase_token(token)
    assert claims["sub"] == "user-uuid-123"
    assert claims["email"] == "test@example.com"
    assert claims["aud"] == "authenticated"


def test_expired_token_rejected():
    token = _make_token(exp_delta=timedelta(hours=-1))
    with pytest.raises(Exception) as exc_info:
        verify_supabase_token(token)
    assert exc_info.value.status_code == 401


def test_malformed_token_rejected():
    with pytest.raises(Exception) as exc_info:
        verify_supabase_token("not.a.valid.jwt")
    assert exc_info.value.status_code == 401


def test_invalid_signature_rejected():
    token = _make_token()
    # Re-encode with a wrong secret to simulate bad signature
    from jose import jwt as _jwt
    bad_token = _jwt.encode(
        {"sub": "x", "aud": "authenticated", "exp": 9999999999, "iss": TEST_ISSUER, "role": "authenticated"},
        "wrong-secret",
        algorithm="HS256",
    )
    with pytest.raises(Exception) as exc_info:
        verify_supabase_token(bad_token)
    assert exc_info.value.status_code == 401


def test_issuer_mismatch_rejected():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-uuid-123",
            "email": "test@example.com",
            "aud": "authenticated",
            "role": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iss": "https://wrong.supabase.co/auth/v1",
            "app_metadata": {},
            "user_metadata": {},
        },
        TEST_SECRET,
        algorithm="HS256",
    )
    with pytest.raises(Exception) as exc_info:
        verify_supabase_token(token)
    assert exc_info.value.status_code == 401


# ── get_or_create_user ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_existing_user_by_supabase_id(db_session: AsyncSession):
    user = User(
        supabase_id="existing-uuid",
        email="existing@example.com",
        full_name="Existing User",
        hashed_password="!",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    claims = {"sub": "existing-uuid", "email": "existing@example.com"}
    result = await get_or_create_user(db_session, claims)

    assert result.id == user.id
    assert result.supabase_id == "existing-uuid"


@pytest.mark.asyncio
async def test_create_new_user_with_unknown_supabase_id(db_session: AsyncSession):
    claims = {
        "sub": "new-uuid-999",
        "email": "new@example.com",
        "user_metadata": {"full_name": "New User", "avatar_url": "https://example.com/avatar.png"},
    }
    result = await get_or_create_user(db_session, claims)

    assert result.supabase_id == "new-uuid-999"
    assert result.email == "new@example.com"
    assert result.full_name == "New User"
    assert result.avatar_url == "https://example.com/avatar.png"
    assert result.is_verified is True
    assert result.hashed_password == "!"


@pytest.mark.asyncio
async def test_create_user_generates_placeholder_email_when_missing(db_session: AsyncSession):
    claims = {"sub": "no-email-uuid", "user_metadata": {}}
    result = await get_or_create_user(db_session, claims)

    assert result.email == "no-email-uuid@supabase.placeholder"
    assert result.supabase_id == "no-email-uuid"
