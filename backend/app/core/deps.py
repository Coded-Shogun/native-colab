"""
FastAPI Dependencies
Reusable dependencies for authentication, authorization, and database access
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User
from app.core.supabase_auth import verify_supabase_token, get_or_create_user

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from a Supabase JWT.

    Args:
        token: Supabase JWT access token from request header
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        claims = verify_supabase_token(token)
    except HTTPException:
        raise credentials_exception

    if claims.get("role") != "authenticated":
        raise credentials_exception

    supabase_id = claims.get("sub")
    if not supabase_id:
        raise credentials_exception

    user = await get_or_create_user(db, claims)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User object

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current super admin user.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User object

    Raises:
        HTTPException: If user is not a super admin
    """
    if not current_user.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have sufficient privileges"
        )
    return current_user


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.

    Args:
        token: Optional JWT access token
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if token is None:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
