"""
Authentication API Endpoints
Handles user logout and current user info.
Registration, login, and token refresh are managed by Supabase.
"""

from fastapi import APIRouter, Depends, status

from app.db.models import User
from app.schemas.user import UserResponse
from app.core.deps import get_current_user

router = APIRouter()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user (client-side token invalidation).

    Note: Supabase handles token management via supabase.auth.signOut().
    This endpoint exists for API consistency.

    Args:
        current_user: Current authenticated user

    Returns:
        204 No Content
    """
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return current_user
