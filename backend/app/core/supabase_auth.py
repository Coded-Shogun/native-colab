"""
Supabase Authentication Module
Verifies inbound Supabase-issued JWTs and resolves/creates local users.
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.user import User


@dataclass
class SupabaseClaims:
    sub: str
    email: Optional[str]
    aud: str
    role: str
    iat: float
    exp: float
    iss: str
    app_metadata: dict
    user_metadata: dict

    @classmethod
    def from_dict(cls, data: dict) -> "SupabaseClaims":
        return cls(
            sub=data["sub"],
            email=data.get("email"),
            aud=data.get("aud", ""),
            role=data.get("role", "authenticated"),
            iat=data.get("iat", 0),
            exp=data.get("exp", 0),
            iss=data.get("iss", ""),
            app_metadata=data.get("app_metadata", {}),
            user_metadata=data.get("user_metadata", {}),
        )


def verify_supabase_token(token: str) -> dict:
    """
    Decode and verify a Supabase-issued JWT.

    Args:
        token: JWT token string from the Supabase auth flow.

    Returns:
        Decoded payload dict.

    Raises:
        HTTPException: If the token is invalid, expired, or has an unexpected issuer.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Supabase token: {e}",
        )

    expected_issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"
    iss = payload.get("iss", "")
    if expected_issuer and iss and iss != expected_issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token issuer mismatch",
        )

    return payload


async def get_or_create_user(db: AsyncSession, claims: dict) -> User:
    """
    Look up a user by supabase_id, or create a new one from the JWT claims.

    Args:
        db: Async database session.
        claims: Decoded JWT payload (as returned by verify_supabase_token).

    Returns:
        Existing or newly created User instance.
    """
    supabase_id: str = claims["sub"]

    result = await db.execute(
        select(User).where(User.supabase_id == supabase_id)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        return user

    email = claims.get("email") or f"{supabase_id}@supabase.placeholder"
    user_metadata = claims.get("user_metadata", {})
    full_name = user_metadata.get("full_name") or user_metadata.get("name") or supabase_id
    avatar_url = user_metadata.get("avatar_url")

    user = User(
        supabase_id=supabase_id,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        hashed_password="!",
        is_active=True,
        is_verified=bool(claims.get("email")),
    )
    db.add(user)
    await db.flush()
    return user
