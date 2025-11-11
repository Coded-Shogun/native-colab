"""
Workspace Management API Endpoints
Handles workspace creation, member management, and RBAC
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import User, Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceWithMembersResponse,
    WorkspaceMemberResponse,
    WorkspaceInviteRequest,
    WorkspaceRoleUpdate,
)
from app.core.deps import get_current_user

router = APIRouter()


async def get_workspace_member(
    workspace_id: int,
    user_id: int,
    db: AsyncSession
) -> WorkspaceMember | None:
    """Helper to get workspace membership"""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def check_workspace_permission(
    workspace_id: int,
    user: User,
    required_role: str,
    db: AsyncSession
) -> WorkspaceMember:
    """
    Check if user has required permission in workspace.
    Returns membership if authorized, raises HTTPException otherwise.
    """
    membership = await get_workspace_member(workspace_id, user.id, db)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this workspace"
        )

    # Check if user has required role
    role_hierarchy = {
        WorkspaceRole.GUEST.value: 0,
        WorkspaceRole.MEMBER.value: 1,
        WorkspaceRole.ADMIN.value: 2,
        WorkspaceRole.OWNER.value: 3,
    }

    user_role_level = role_hierarchy.get(membership.role, 0)
    required_role_level = role_hierarchy.get(required_role, 999)

    if user_role_level < required_role_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}"
        )

    return membership


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new workspace.
    User becomes the owner automatically.

    Args:
        workspace_data: Workspace creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created workspace

    Raises:
        HTTPException: If slug already exists
    """
    # Check if slug already exists
    result = await db.execute(
        select(Workspace).where(Workspace.slug == workspace_data.slug)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace slug already exists"
        )

    # Create workspace
    workspace = Workspace(
        name=workspace_data.name,
        slug=workspace_data.slug,
        description=workspace_data.description,
        owner_id=current_user.id
    )
    db.add(workspace)
    await db.flush()

    # Add creator as owner member
    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=WorkspaceRole.OWNER.value
    )
    db.add(membership)

    await db.commit()
    await db.refresh(workspace)

    return workspace


@router.get("/", response_model=List[WorkspaceResponse])
async def list_my_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all workspaces the current user is a member of.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of workspaces
    """
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember)
        .where(WorkspaceMember.user_id == current_user.id)
        .order_by(Workspace.created_at.desc())
    )
    workspaces = result.scalars().all()

    return workspaces


@router.get("/{workspace_id}", response_model=WorkspaceWithMembersResponse)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get workspace details with members list.

    Args:
        workspace_id: Workspace ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Workspace with members

    Raises:
        HTTPException: If not authorized or workspace not found
    """
    # Check membership
    await check_workspace_permission(workspace_id, current_user, WorkspaceRole.GUEST.value, db)

    # Get workspace with members
    result = await db.execute(
        select(Workspace)
        .options(selectinload(Workspace.members).selectinload(WorkspaceMember.user))
        .where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace_update: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update workspace details.
    Requires admin or owner role.

    Args:
        workspace_id: Workspace ID
        workspace_update: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated workspace

    Raises:
        HTTPException: If not authorized or workspace not found
    """
    # Check permission
    await check_workspace_permission(workspace_id, current_user, WorkspaceRole.ADMIN.value, db)

    # Get workspace
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Update fields
    if workspace_update.name is not None:
        workspace.name = workspace_update.name

    if workspace_update.description is not None:
        workspace.description = workspace_update.description

    if workspace_update.logo_url is not None:
        workspace.logo_url = workspace_update.logo_url

    await db.commit()
    await db.refresh(workspace)

    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (deactivate) a workspace.
    Only owners can delete workspaces.

    Args:
        workspace_id: Workspace ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException: If not authorized or workspace not found
    """
    # Check owner permission
    await check_workspace_permission(workspace_id, current_user, WorkspaceRole.OWNER.value, db)

    # Get workspace
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Soft delete
    workspace.is_active = False
    await db.commit()

    return None


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    workspace_id: int,
    invite_data: WorkspaceInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invite a user to the workspace.
    Requires admin or owner role.

    Args:
        workspace_id: Workspace ID
        invite_data: Invitation data (email and role)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created membership

    Raises:
        HTTPException: If not authorized, user not found, or already member
    """
    # Check permission
    await check_workspace_permission(workspace_id, current_user, WorkspaceRole.ADMIN.value, db)

    # Find user by email
    result = await db.execute(
        select(User).where(User.email == invite_data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already a member
    existing_membership = await get_workspace_member(workspace_id, user.id, db)
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace"
        )

    # Create membership
    membership = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=invite_data.role
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)

    # Load user relationship
    await db.refresh(membership, ["user"])

    return membership


@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all members of a workspace.

    Args:
        workspace_id: Workspace ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of workspace members

    Raises:
        HTTPException: If not authorized
    """
    # Check membership
    await check_workspace_permission(workspace_id, current_user, WorkspaceRole.GUEST.value, db)

    # Get members
    result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.user))
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.joined_at)
    )
    members = result.scalars().all()

    return members


@router.put("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_member_role(
    workspace_id: int,
    user_id: int,
    role_update: WorkspaceRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a member's role in the workspace.
    Requires owner role.

    Args:
        workspace_id: Workspace ID
        user_id: User ID to update
        role_update: New role data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated membership

    Raises:
        HTTPException: If not authorized or member not found
    """
    # Check owner permission
    await check_workspace_permission(workspace_id, current_user, WorkspaceRole.OWNER.value, db)

    # Get membership
    membership = await get_workspace_member(workspace_id, user_id, db)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this workspace"
        )

    # Update role
    membership.role = role_update.role
    await db.commit()
    await db.refresh(membership)

    # Load user relationship
    await db.refresh(membership, ["user"])

    return membership


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a member from the workspace.
    Requires admin or owner role, or the user removing themselves.

    Args:
        workspace_id: Workspace ID
        user_id: User ID to remove
        current_user: Current authenticated user
        db: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException: If not authorized or member not found
    """
    # Check if user is removing themselves or has admin permission
    if user_id != current_user.id:
        await check_workspace_permission(workspace_id, current_user, WorkspaceRole.ADMIN.value, db)

    # Get membership
    membership = await get_workspace_member(workspace_id, user_id, db)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this workspace"
        )

    # Prevent removing the last owner
    if membership.role == WorkspaceRole.OWNER.value:
        result = await db.execute(
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceRole.OWNER.value
            )
        )
        owner_count = len(result.scalars().all())

        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner of the workspace"
            )

    # Remove membership
    await db.delete(membership)
    await db.commit()

    return None
