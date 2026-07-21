"""
Folders API
Endpoints for managing document folders
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    Workspace,
    WorkspaceMember,
    Folder,
    Document,
)
from app.schemas.document import (
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    FolderListResponse,
)
from app.core.deps import get_current_user
from app.core.organization_context import get_organization_context, OrganizationContext

router = APIRouter(dependencies=[Depends(get_organization_context)])


# ============================================
# Helper Functions
# ============================================
async def check_workspace_access(
    workspace_id: int,
    user: User,
    db: AsyncSession
) -> bool:
    """Check if user has access to workspace"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def check_folder_access(
    folder_id: int,
    user: User,
    db: AsyncSession
) -> Optional[Folder]:
    """Check if user has access to folder via workspace membership"""
    stmt = select(Folder).where(Folder.id == folder_id)
    result = await db.execute(stmt)
    folder = result.scalar_one_or_none()

    if not folder:
        return None

    # Check workspace access
    has_access = await check_workspace_access(folder.workspace_id, user, db)
    if not has_access:
        return None

    return folder


async def build_folder_response(folder: Folder, db: AsyncSession) -> FolderResponse:
    """Build folder response with nested information"""
    # Load relationships
    stmt = select(Folder).options(
        selectinload(Folder.created_by)
    ).where(Folder.id == folder.id)
    result = await db.execute(stmt)
    folder = result.scalar_one()

    # Count subfolders
    subfolder_stmt = select(func.count(Folder.id)).where(
        Folder.parent_folder_id == folder.id,
        Folder.is_deleted == False
    )
    subfolder_result = await db.execute(subfolder_stmt)
    subfolder_count = subfolder_result.scalar() or 0

    # Count documents
    document_stmt = select(func.count(Document.id)).where(
        Document.folder_id == folder.id,
        Document.is_deleted == False
    )
    document_result = await db.execute(document_stmt)
    document_count = document_result.scalar() or 0

    return FolderResponse(
        id=folder.id,
        workspace_id=folder.workspace_id,
        parent_folder_id=folder.parent_folder_id,
        created_by_id=folder.created_by_id,
        name=folder.name,
        description=folder.description,
        color=folder.color,
        is_deleted=folder.is_deleted,
        deleted_at=folder.deleted_at,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        creator_name=folder.created_by.full_name if folder.created_by else None,
        creator_email=folder.created_by.email if folder.created_by else None,
        subfolder_count=subfolder_count,
        document_count=document_count,
    )


# ============================================
# Folder CRUD Endpoints
# ============================================
@router.post("/", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new folder in a workspace.
    User must be a workspace member.
    """
    # Check workspace access
    has_access = await check_workspace_access(folder_data.workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # If parent_folder_id provided, verify it exists and user has access
    if folder_data.parent_folder_id:
        parent_folder = await check_folder_access(folder_data.parent_folder_id, current_user, db)
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found or you don't have access"
            )

        # Verify parent folder is in the same workspace
        if parent_folder.workspace_id != folder_data.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent folder must be in the same workspace"
            )

    # Create folder
    new_folder = Folder(
        workspace_id=folder_data.workspace_id,
        parent_folder_id=folder_data.parent_folder_id,
        created_by_id=current_user.id,
        name=folder_data.name,
        description=folder_data.description,
        color=folder_data.color,
    )

    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)

    return await build_folder_response(new_folder, db)


@router.get("/", response_model=FolderListResponse)
async def list_folders(
    workspace_id: int = Query(..., gt=0),
    parent_folder_id: Optional[int] = Query(None, gt=0),
    include_deleted: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List folders in a workspace or parent folder.
    User must be a workspace member.
    """
    # Check workspace access
    has_access = await check_workspace_access(workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Build query
    conditions = [Folder.workspace_id == workspace_id]

    if parent_folder_id:
        conditions.append(Folder.parent_folder_id == parent_folder_id)
    else:
        conditions.append(Folder.parent_folder_id.is_(None))

    if not include_deleted:
        conditions.append(Folder.is_deleted == False)

    stmt = select(Folder).where(and_(*conditions))
    stmt = stmt.order_by(Folder.name)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    folders = result.scalars().all()

    # Build responses
    folder_responses = []
    for folder in folders:
        folder_responses.append(await build_folder_response(folder, db))

    return FolderListResponse(
        folders=folder_responses,
        total=total
    )


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get folder details"""
    folder = await check_folder_access(folder_id, current_user, db)

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or you don't have access"
        )

    return await build_folder_response(folder, db)


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: int,
    folder_update: FolderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update folder metadata"""
    folder = await check_folder_access(folder_id, current_user, db)

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or you don't have access"
        )

    # Update fields
    update_data = folder_update.model_dump(exclude_unset=True)

    # If moving folder, verify new parent folder
    if 'parent_folder_id' in update_data and update_data['parent_folder_id']:
        new_parent = await check_folder_access(update_data['parent_folder_id'], current_user, db)
        if not new_parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found or you don't have access"
            )

        # Verify new parent is in the same workspace
        if new_parent.workspace_id != folder.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent folder must be in the same workspace"
            )

        # Prevent circular reference
        if new_parent.id == folder.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder cannot be its own parent"
            )

    for field, value in update_data.items():
        setattr(folder, field, value)

    await db.commit()
    await db.refresh(folder)

    return await build_folder_response(folder, db)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: int,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a folder (soft delete by default).
    Use ?permanent=true for hard delete.
    """
    folder = await check_folder_access(folder_id, current_user, db)

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or you don't have access"
        )

    if permanent:
        # Hard delete - also deletes all subfolders and documents (cascade)
        await db.delete(folder)
    else:
        # Soft delete
        from datetime import datetime
        folder.is_deleted = True
        folder.deleted_at = datetime.utcnow()

    await db.commit()


@router.post("/{folder_id}/restore", response_model=FolderResponse)
async def restore_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Restore a soft-deleted folder"""
    folder = await check_folder_access(folder_id, current_user, db)

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found or you don't have access"
        )

    if not folder.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder is not deleted"
        )

    folder.is_deleted = False
    folder.deleted_at = None

    await db.commit()
    await db.refresh(folder)

    return await build_folder_response(folder, db)
