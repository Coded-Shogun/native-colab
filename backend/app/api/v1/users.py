"""
User Management API Endpoints
Handles user profile updates, password changes, and user queries
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.deps import get_current_user, get_current_superuser
from app.core.security import get_password_hash, verify_password, validate_password_strength

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile.

    Args:
        user_update: Profile update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user profile
    """
    # Update fields if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.bio is not None:
        current_user.bio = user_update.bio

    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password.

    Args:
        current_password: User's current password
        new_password: New password to set
        current_user: Current authenticated user
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException: If current password is incorrect or new password is weak
    """
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    is_valid, error_message = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    await db.commit()

    return None


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_account(
    password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete current user's account (soft delete - sets is_active to False).

    Args:
        password: User's password for confirmation
        current_user: Current authenticated user
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException: If password is incorrect
    """
    # Verify password for security
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )

    # Soft delete: deactivate account
    current_user.is_active = False
    await db.commit()

    return None


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user by ID.
    Users can view their own profile or profiles of users in their workspaces.

    Args:
        user_id: User ID to retrieve
        db: Database session
        current_user: Current authenticated user

    Returns:
        User profile information

    Raises:
        HTTPException: If user not found or not authorized
    """
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check authorization: users can view themselves or super admins can view anyone
    if user.id != current_user.id and not current_user.is_super_admin():
        # TODO: Add check for workspace membership
        # For now, only allow viewing own profile or if super admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )

    return user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    List all users (admin only).

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        db: Database session
        current_user: Current authenticated super admin

    Returns:
        List of users
    """
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return users


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Update any user's profile (admin only).

    Args:
        user_id: User ID to update
        user_update: Profile update data
        db: Database session
        current_user: Current authenticated super admin

    Returns:
        Updated user profile

    Raises:
        HTTPException: If user not found
    """
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields if provided
    if user_update.full_name is not None:
        user.full_name = user_update.full_name

    if user_update.bio is not None:
        user.bio = user_update.bio

    if user_update.avatar_url is not None:
        user.avatar_url = user_update.avatar_url

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Delete (deactivate) any user (admin only).

    Args:
        user_id: User ID to delete
        db: Database session
        current_user: Current authenticated super admin

    Returns:
        204 No Content on success

    Raises:
        HTTPException: If user not found
    """
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent deleting own account through admin endpoint
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account through admin endpoint. Use DELETE /users/me instead."
        )

    # Soft delete: deactivate account
    user.is_active = False
    await db.commit()

    return None
