"""
Whiteboards API
Endpoints for collaborative whiteboard management
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    WorkspaceMember,
    Whiteboard,
    WhiteboardElement,
    WhiteboardParticipant,
    WhiteboardSnapshot,
    WhiteboardAccessLevel,
)
from app.schemas.whiteboard import (
    WhiteboardCreate,
    WhiteboardUpdate,
    WhiteboardResponse,
    WhiteboardListResponse,
    WhiteboardElementCreate,
    WhiteboardElementUpdate,
    WhiteboardElementResponse,
    WhiteboardElementListResponse,
    BulkElementCreate,
    BulkElementDelete,
    WhiteboardParticipantAdd,
    WhiteboardParticipantUpdate,
    WhiteboardParticipantResponse,
    WhiteboardParticipantListResponse,
    WhiteboardSnapshotCreate,
    WhiteboardSnapshotResponse,
    WhiteboardSnapshotDetailResponse,
    WhiteboardSnapshotListResponse,
    WhiteboardStats,
)
from app.core.deps import get_current_user

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_workspace_access(workspace_id: int, user: User, db: AsyncSession) -> bool:
    """Check if user has access to workspace"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def check_whiteboard_access(
    whiteboard_id: int,
    user: User,
    db: AsyncSession,
    required_level: WhiteboardAccessLevel = WhiteboardAccessLevel.VIEW
) -> Optional[Whiteboard]:
    """Check if user has access to whiteboard with required level"""
    stmt = select(Whiteboard).where(Whiteboard.id == whiteboard_id)
    result = await db.execute(stmt)
    whiteboard = result.scalar_one_or_none()

    if not whiteboard:
        return None

    # Check workspace access
    has_workspace_access = await check_workspace_access(whiteboard.workspace_id, user, db)
    if not has_workspace_access:
        return None

    # Check participant access level
    participant_stmt = select(WhiteboardParticipant).where(
        WhiteboardParticipant.whiteboard_id == whiteboard_id,
        WhiteboardParticipant.user_id == user.id
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    # Creator always has admin access
    if whiteboard.created_by_id == user.id:
        return whiteboard

    # Public whiteboards can be viewed by workspace members
    if whiteboard.is_public and required_level == WhiteboardAccessLevel.VIEW:
        return whiteboard

    # Check participant access level
    if not participant:
        return None

    # Check if participant has required level
    access_levels = {
        WhiteboardAccessLevel.VIEW: 0,
        WhiteboardAccessLevel.EDIT: 1,
        WhiteboardAccessLevel.ADMIN: 2,
    }

    if access_levels[participant.access_level] >= access_levels[required_level]:
        return whiteboard

    return None


async def build_whiteboard_response(whiteboard: Whiteboard, db: AsyncSession) -> WhiteboardResponse:
    """Build whiteboard response with nested information"""
    # Load relationships
    stmt = select(Whiteboard).options(
        selectinload(Whiteboard.created_by)
    ).where(Whiteboard.id == whiteboard.id)
    result = await db.execute(stmt)
    whiteboard = result.scalar_one()

    # Count elements
    element_stmt = select(func.count(WhiteboardElement.id)).where(
        WhiteboardElement.whiteboard_id == whiteboard.id,
        WhiteboardElement.is_deleted == False
    )
    element_result = await db.execute(element_stmt)
    element_count = element_result.scalar() or 0

    # Count participants
    participant_stmt = select(func.count(WhiteboardParticipant.id)).where(
        WhiteboardParticipant.whiteboard_id == whiteboard.id
    )
    participant_result = await db.execute(participant_stmt)
    participant_count = participant_result.scalar() or 0

    # Count active participants
    active_stmt = select(func.count(WhiteboardParticipant.id)).where(
        WhiteboardParticipant.whiteboard_id == whiteboard.id,
        WhiteboardParticipant.is_active == True
    )
    active_result = await db.execute(active_stmt)
    active_count = active_result.scalar() or 0

    return WhiteboardResponse(
        id=whiteboard.id,
        workspace_id=whiteboard.workspace_id,
        created_by_id=whiteboard.created_by_id,
        project_id=whiteboard.project_id,
        name=whiteboard.name,
        description=whiteboard.description,
        canvas_width=whiteboard.canvas_width,
        canvas_height=whiteboard.canvas_height,
        background_color=whiteboard.background_color,
        grid_enabled=whiteboard.grid_enabled,
        is_public=whiteboard.is_public,
        is_locked=whiteboard.is_locked,
        is_template=whiteboard.is_template,
        thumbnail_url=whiteboard.thumbnail_url,
        created_at=whiteboard.created_at,
        updated_at=whiteboard.updated_at,
        last_activity_at=whiteboard.last_activity_at,
        creator_name=whiteboard.created_by.full_name if whiteboard.created_by else None,
        creator_email=whiteboard.created_by.email if whiteboard.created_by else None,
        element_count=element_count,
        participant_count=participant_count,
        active_participant_count=active_count,
    )


# ============================================
# Whiteboard CRUD Endpoints
# ============================================
@router.post("/", response_model=WhiteboardResponse, status_code=status.HTTP_201_CREATED)
async def create_whiteboard(
    whiteboard_data: WhiteboardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new whiteboard in a workspace"""
    # Check workspace access
    has_access = await check_workspace_access(whiteboard_data.workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Create whiteboard
    new_whiteboard = Whiteboard(
        workspace_id=whiteboard_data.workspace_id,
        created_by_id=current_user.id,
        project_id=whiteboard_data.project_id,
        name=whiteboard_data.name,
        description=whiteboard_data.description,
        canvas_width=whiteboard_data.canvas_width,
        canvas_height=whiteboard_data.canvas_height,
        background_color=whiteboard_data.background_color,
        grid_enabled=whiteboard_data.grid_enabled,
        is_public=whiteboard_data.is_public,
    )

    db.add(new_whiteboard)
    await db.flush()

    # Add creator as admin participant
    creator_participant = WhiteboardParticipant(
        whiteboard_id=new_whiteboard.id,
        user_id=current_user.id,
        access_level=WhiteboardAccessLevel.ADMIN,
    )
    db.add(creator_participant)

    await db.commit()
    await db.refresh(new_whiteboard)

    return await build_whiteboard_response(new_whiteboard, db)


@router.get("/", response_model=WhiteboardListResponse)
async def list_whiteboards(
    workspace_id: int = Query(..., gt=0),
    project_id: Optional[int] = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List whiteboards in a workspace"""
    # Check workspace access
    has_access = await check_workspace_access(workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Build query - show whiteboards user has access to
    conditions = [Whiteboard.workspace_id == workspace_id]

    if project_id:
        conditions.append(Whiteboard.project_id == project_id)

    # Get whiteboards where user is creator or participant or public
    stmt = select(Whiteboard).where(and_(*conditions))
    stmt = stmt.where(
        (Whiteboard.created_by_id == current_user.id) |
        (Whiteboard.is_public == True) |
        (Whiteboard.id.in_(
            select(WhiteboardParticipant.whiteboard_id).where(
                WhiteboardParticipant.user_id == current_user.id
            )
        ))
    )
    stmt = stmt.order_by(desc(Whiteboard.last_activity_at))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    whiteboards = result.scalars().all()

    # Build responses
    whiteboard_responses = []
    for wb in whiteboards:
        whiteboard_responses.append(await build_whiteboard_response(wb, db))

    return WhiteboardListResponse(
        whiteboards=whiteboard_responses,
        total=total
    )


@router.get("/{whiteboard_id}", response_model=WhiteboardResponse)
async def get_whiteboard(
    whiteboard_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get whiteboard details"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.VIEW
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have access"
        )

    return await build_whiteboard_response(whiteboard, db)


@router.put("/{whiteboard_id}", response_model=WhiteboardResponse)
async def update_whiteboard(
    whiteboard_id: int,
    whiteboard_update: WhiteboardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update whiteboard settings"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.ADMIN
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have admin access"
        )

    # Update fields
    update_data = whiteboard_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(whiteboard, field, value)

    await db.commit()
    await db.refresh(whiteboard)

    return await build_whiteboard_response(whiteboard, db)


@router.delete("/{whiteboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_whiteboard(
    whiteboard_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a whiteboard"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.ADMIN
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have admin access"
        )

    await db.delete(whiteboard)
    await db.commit()


# ============================================
# Element Management Endpoints
# ============================================
@router.get("/{whiteboard_id}/elements", response_model=WhiteboardElementListResponse)
async def list_elements(
    whiteboard_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all elements in a whiteboard"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.VIEW
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have access"
        )

    # Get elements
    stmt = select(WhiteboardElement).options(
        selectinload(WhiteboardElement.created_by)
    ).where(
        WhiteboardElement.whiteboard_id == whiteboard_id,
        WhiteboardElement.is_deleted == False
    ).order_by(WhiteboardElement.z_index, WhiteboardElement.created_at)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    elements = result.scalars().all()

    element_responses = []
    for elem in elements:
        element_responses.append(WhiteboardElementResponse(
            id=elem.id,
            whiteboard_id=elem.whiteboard_id,
            created_by_id=elem.created_by_id,
            element_id=elem.element_id,
            element_type=elem.element_type,
            x_position=elem.x_position,
            y_position=elem.y_position,
            width=elem.width,
            height=elem.height,
            stroke_color=elem.stroke_color,
            fill_color=elem.fill_color,
            stroke_width=elem.stroke_width,
            opacity=elem.opacity,
            element_data=elem.element_data,
            z_index=elem.z_index,
            is_locked=elem.is_locked,
            is_deleted=elem.is_deleted,
            created_at=elem.created_at,
            updated_at=elem.updated_at,
            creator_name=elem.created_by.full_name if elem.created_by else None,
        ))

    return WhiteboardElementListResponse(
        elements=element_responses,
        total=total
    )


@router.post("/{whiteboard_id}/elements", response_model=WhiteboardElementResponse, status_code=status.HTTP_201_CREATED)
async def create_element(
    whiteboard_id: int,
    element_data: WhiteboardElementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new element on the whiteboard"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.EDIT
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have edit access"
        )

    if whiteboard.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Whiteboard is locked"
        )

    # Create element
    new_element = WhiteboardElement(
        whiteboard_id=whiteboard_id,
        created_by_id=current_user.id,
        element_id=element_data.element_id,
        element_type=element_data.element_type,
        x_position=element_data.x_position,
        y_position=element_data.y_position,
        width=element_data.width,
        height=element_data.height,
        stroke_color=element_data.stroke_color,
        fill_color=element_data.fill_color,
        stroke_width=element_data.stroke_width,
        opacity=element_data.opacity,
        element_data=element_data.element_data,
        z_index=element_data.z_index,
    )

    db.add(new_element)

    # Update whiteboard activity
    whiteboard.last_activity_at = datetime.utcnow()

    await db.commit()
    await db.refresh(new_element)

    # Load creator for response
    stmt = select(WhiteboardElement).options(
        selectinload(WhiteboardElement.created_by)
    ).where(WhiteboardElement.id == new_element.id)
    result = await db.execute(stmt)
    new_element = result.scalar_one()

    return WhiteboardElementResponse.model_validate(new_element)


@router.post("/{whiteboard_id}/elements/bulk", response_model=WhiteboardElementListResponse, status_code=status.HTTP_201_CREATED)
async def create_elements_bulk(
    whiteboard_id: int,
    bulk_data: BulkElementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create multiple elements at once"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.EDIT
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have edit access"
        )

    if whiteboard.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Whiteboard is locked"
        )

    created_elements = []
    for element_data in bulk_data.elements:
        new_element = WhiteboardElement(
            whiteboard_id=whiteboard_id,
            created_by_id=current_user.id,
            element_id=element_data.element_id,
            element_type=element_data.element_type,
            x_position=element_data.x_position,
            y_position=element_data.y_position,
            width=element_data.width,
            height=element_data.height,
            stroke_color=element_data.stroke_color,
            fill_color=element_data.fill_color,
            stroke_width=element_data.stroke_width,
            opacity=element_data.opacity,
            element_data=element_data.element_data,
            z_index=element_data.z_index,
        )
        db.add(new_element)
        created_elements.append(new_element)

    # Update whiteboard activity
    whiteboard.last_activity_at = datetime.utcnow()

    await db.commit()

    # Refresh and build responses
    element_responses = []
    for elem in created_elements:
        await db.refresh(elem)
        stmt = select(WhiteboardElement).options(
            selectinload(WhiteboardElement.created_by)
        ).where(WhiteboardElement.id == elem.id)
        result = await db.execute(stmt)
        elem = result.scalar_one()
        element_responses.append(WhiteboardElementResponse.model_validate(elem))

    return WhiteboardElementListResponse(
        elements=element_responses,
        total=len(element_responses)
    )


@router.put("/{whiteboard_id}/elements/{element_id}", response_model=WhiteboardElementResponse)
async def update_element(
    whiteboard_id: int,
    element_id: str,
    element_update: WhiteboardElementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an element"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.EDIT
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have edit access"
        )

    if whiteboard.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Whiteboard is locked"
        )

    # Get element
    stmt = select(WhiteboardElement).where(
        WhiteboardElement.whiteboard_id == whiteboard_id,
        WhiteboardElement.element_id == element_id,
        WhiteboardElement.is_deleted == False
    )
    result = await db.execute(stmt)
    element = result.scalar_one_or_none()

    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found"
        )

    if element.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Element is locked"
        )

    # Update fields
    update_data = element_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(element, field, value)

    # Update whiteboard activity
    whiteboard.last_activity_at = datetime.utcnow()

    await db.commit()
    await db.refresh(element)

    # Load creator for response
    stmt = select(WhiteboardElement).options(
        selectinload(WhiteboardElement.created_by)
    ).where(WhiteboardElement.id == element.id)
    result = await db.execute(stmt)
    element = result.scalar_one()

    return WhiteboardElementResponse.model_validate(element)


@router.delete("/{whiteboard_id}/elements/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_element(
    whiteboard_id: int,
    element_id: str,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an element (soft delete by default)"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.EDIT
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have edit access"
        )

    if whiteboard.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Whiteboard is locked"
        )

    # Get element
    stmt = select(WhiteboardElement).where(
        WhiteboardElement.whiteboard_id == whiteboard_id,
        WhiteboardElement.element_id == element_id
    )
    result = await db.execute(stmt)
    element = result.scalar_one_or_none()

    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Element not found"
        )

    if element.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Element is locked"
        )

    if permanent:
        await db.delete(element)
    else:
        element.is_deleted = True

    # Update whiteboard activity
    whiteboard.last_activity_at = datetime.utcnow()

    await db.commit()


@router.post("/{whiteboard_id}/elements/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_elements_bulk(
    whiteboard_id: int,
    bulk_delete: BulkElementDelete,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple elements at once"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.EDIT
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have edit access"
        )

    if whiteboard.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Whiteboard is locked"
        )

    # Get elements
    stmt = select(WhiteboardElement).where(
        WhiteboardElement.whiteboard_id == whiteboard_id,
        WhiteboardElement.element_id.in_(bulk_delete.element_ids),
        WhiteboardElement.is_locked == False
    )
    result = await db.execute(stmt)
    elements = result.scalars().all()

    if permanent:
        for element in elements:
            await db.delete(element)
    else:
        for element in elements:
            element.is_deleted = True

    # Update whiteboard activity
    whiteboard.last_activity_at = datetime.utcnow()

    await db.commit()


# ============================================
# Participant Management Endpoints
# ============================================
@router.get("/{whiteboard_id}/participants", response_model=WhiteboardParticipantListResponse)
async def list_participants(
    whiteboard_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all participants of a whiteboard"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.VIEW
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have access"
        )

    # Get participants
    stmt = select(WhiteboardParticipant).options(
        selectinload(WhiteboardParticipant.user)
    ).where(
        WhiteboardParticipant.whiteboard_id == whiteboard_id
    ).order_by(desc(WhiteboardParticipant.is_active), WhiteboardParticipant.joined_at)

    result = await db.execute(stmt)
    participants = result.scalars().all()

    participant_responses = []
    for p in participants:
        participant_responses.append(WhiteboardParticipantResponse(
            id=p.id,
            whiteboard_id=p.whiteboard_id,
            user_id=p.user_id,
            access_level=p.access_level,
            is_active=p.is_active,
            last_seen_at=p.last_seen_at,
            cursor_x=p.cursor_x,
            cursor_y=p.cursor_y,
            selected_element_id=p.selected_element_id,
            joined_at=p.joined_at,
            user_name=p.user.full_name if p.user else None,
            user_email=p.user.email if p.user else None,
            user_avatar=p.user.avatar_url if p.user else None,
        ))

    return WhiteboardParticipantListResponse(
        participants=participant_responses,
        total=len(participant_responses)
    )


@router.post("/{whiteboard_id}/participants", response_model=WhiteboardParticipantResponse, status_code=status.HTTP_201_CREATED)
async def add_participant(
    whiteboard_id: int,
    participant_data: WhiteboardParticipantAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a participant to the whiteboard"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.ADMIN
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have admin access"
        )

    # Check if user is workspace member
    has_workspace_access = await check_workspace_access(whiteboard.workspace_id, current_user, db)
    if not has_workspace_access:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a workspace member"
        )

    # Check if already participant
    existing_stmt = select(WhiteboardParticipant).where(
        WhiteboardParticipant.whiteboard_id == whiteboard_id,
        WhiteboardParticipant.user_id == participant_data.user_id
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant"
        )

    # Add participant
    new_participant = WhiteboardParticipant(
        whiteboard_id=whiteboard_id,
        user_id=participant_data.user_id,
        access_level=participant_data.access_level,
    )

    db.add(new_participant)
    await db.commit()
    await db.refresh(new_participant)

    # Load user for response
    stmt = select(WhiteboardParticipant).options(
        selectinload(WhiteboardParticipant.user)
    ).where(WhiteboardParticipant.id == new_participant.id)
    result = await db.execute(stmt)
    new_participant = result.scalar_one()

    return WhiteboardParticipantResponse.model_validate(new_participant)


@router.put("/{whiteboard_id}/participants/{user_id}", response_model=WhiteboardParticipantResponse)
async def update_participant(
    whiteboard_id: int,
    user_id: int,
    participant_update: WhiteboardParticipantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update participant access level"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.ADMIN
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have admin access"
        )

    # Get participant
    stmt = select(WhiteboardParticipant).where(
        WhiteboardParticipant.whiteboard_id == whiteboard_id,
        WhiteboardParticipant.user_id == user_id
    )
    result = await db.execute(stmt)
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    # Update access level
    participant.access_level = participant_update.access_level

    await db.commit()
    await db.refresh(participant)

    # Load user for response
    stmt = select(WhiteboardParticipant).options(
        selectinload(WhiteboardParticipant.user)
    ).where(WhiteboardParticipant.id == participant.id)
    result = await db.execute(stmt)
    participant = result.scalar_one()

    return WhiteboardParticipantResponse.model_validate(participant)


@router.delete("/{whiteboard_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_participant(
    whiteboard_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a participant from the whiteboard"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.ADMIN
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have admin access"
        )

    # Can't remove creator
    if user_id == whiteboard.created_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove whiteboard creator"
        )

    # Get participant
    stmt = select(WhiteboardParticipant).where(
        WhiteboardParticipant.whiteboard_id == whiteboard_id,
        WhiteboardParticipant.user_id == user_id
    )
    result = await db.execute(stmt)
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    await db.delete(participant)
    await db.commit()


# ============================================
# Snapshot Management Endpoints
# ============================================
@router.get("/{whiteboard_id}/snapshots", response_model=WhiteboardSnapshotListResponse)
async def list_snapshots(
    whiteboard_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all snapshots of a whiteboard"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.VIEW
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have access"
        )

    # Get snapshots
    stmt = select(WhiteboardSnapshot).options(
        selectinload(WhiteboardSnapshot.created_by)
    ).where(
        WhiteboardSnapshot.whiteboard_id == whiteboard_id
    ).order_by(desc(WhiteboardSnapshot.created_at))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    snapshots = result.scalars().all()

    snapshot_responses = []
    for snap in snapshots:
        element_count = len(snap.elements_data) if snap.elements_data else 0
        snapshot_responses.append(WhiteboardSnapshotResponse(
            id=snap.id,
            whiteboard_id=snap.whiteboard_id,
            created_by_id=snap.created_by_id,
            name=snap.name,
            description=snap.description,
            thumbnail_url=snap.thumbnail_url,
            is_auto_save=snap.is_auto_save,
            created_at=snap.created_at,
            creator_name=snap.created_by.full_name if snap.created_by else None,
            element_count=element_count,
        ))

    return WhiteboardSnapshotListResponse(
        snapshots=snapshot_responses,
        total=total
    )


@router.post("/{whiteboard_id}/snapshots", response_model=WhiteboardSnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    whiteboard_id: int,
    snapshot_data: WhiteboardSnapshotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a snapshot of the current whiteboard state"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.EDIT
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have access"
        )

    # Get all current elements
    elements_stmt = select(WhiteboardElement).where(
        WhiteboardElement.whiteboard_id == whiteboard_id,
        WhiteboardElement.is_deleted == False
    )
    elements_result = await db.execute(elements_stmt)
    elements = elements_result.scalars().all()

    # Serialize elements
    elements_data = []
    for elem in elements:
        elements_data.append({
            "element_id": elem.element_id,
            "element_type": elem.element_type,
            "x_position": elem.x_position,
            "y_position": elem.y_position,
            "width": elem.width,
            "height": elem.height,
            "stroke_color": elem.stroke_color,
            "fill_color": elem.fill_color,
            "stroke_width": elem.stroke_width,
            "opacity": elem.opacity,
            "element_data": elem.element_data,
            "z_index": elem.z_index,
        })

    # Canvas settings
    canvas_settings = {
        "canvas_width": whiteboard.canvas_width,
        "canvas_height": whiteboard.canvas_height,
        "background_color": whiteboard.background_color,
        "grid_enabled": whiteboard.grid_enabled,
    }

    # Create snapshot
    new_snapshot = WhiteboardSnapshot(
        whiteboard_id=whiteboard_id,
        created_by_id=current_user.id,
        name=snapshot_data.name,
        description=snapshot_data.description,
        elements_data=elements_data,
        canvas_settings=canvas_settings,
    )

    db.add(new_snapshot)
    await db.commit()
    await db.refresh(new_snapshot)

    # Load creator for response
    stmt = select(WhiteboardSnapshot).options(
        selectinload(WhiteboardSnapshot.created_by)
    ).where(WhiteboardSnapshot.id == new_snapshot.id)
    result = await db.execute(stmt)
    new_snapshot = result.scalar_one()

    return WhiteboardSnapshotResponse(
        id=new_snapshot.id,
        whiteboard_id=new_snapshot.whiteboard_id,
        created_by_id=new_snapshot.created_by_id,
        name=new_snapshot.name,
        description=new_snapshot.description,
        thumbnail_url=new_snapshot.thumbnail_url,
        is_auto_save=new_snapshot.is_auto_save,
        created_at=new_snapshot.created_at,
        creator_name=new_snapshot.created_by.full_name if new_snapshot.created_by else None,
        element_count=len(elements_data),
    )


@router.get("/{whiteboard_id}/snapshots/{snapshot_id}", response_model=WhiteboardSnapshotDetailResponse)
async def get_snapshot(
    whiteboard_id: int,
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get snapshot details with full data"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.VIEW
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have access"
        )

    # Get snapshot
    stmt = select(WhiteboardSnapshot).options(
        selectinload(WhiteboardSnapshot.created_by)
    ).where(
        WhiteboardSnapshot.id == snapshot_id,
        WhiteboardSnapshot.whiteboard_id == whiteboard_id
    )
    result = await db.execute(stmt)
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found"
        )

    return WhiteboardSnapshotDetailResponse(
        id=snapshot.id,
        whiteboard_id=snapshot.whiteboard_id,
        created_by_id=snapshot.created_by_id,
        name=snapshot.name,
        description=snapshot.description,
        thumbnail_url=snapshot.thumbnail_url,
        is_auto_save=snapshot.is_auto_save,
        created_at=snapshot.created_at,
        creator_name=snapshot.created_by.full_name if snapshot.created_by else None,
        element_count=len(snapshot.elements_data) if snapshot.elements_data else 0,
        elements_data=snapshot.elements_data,
        canvas_settings=snapshot.canvas_settings,
    )


@router.delete("/{whiteboard_id}/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snapshot(
    whiteboard_id: int,
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a snapshot"""
    whiteboard = await check_whiteboard_access(
        whiteboard_id,
        current_user,
        db,
        WhiteboardAccessLevel.ADMIN
    )

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found or you don't have admin access"
        )

    # Get snapshot
    stmt = select(WhiteboardSnapshot).where(
        WhiteboardSnapshot.id == snapshot_id,
        WhiteboardSnapshot.whiteboard_id == whiteboard_id
    )
    result = await db.execute(stmt)
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found"
        )

    await db.delete(snapshot)
    await db.commit()


# ============================================
# Statistics Endpoint
# ============================================
@router.get("/workspace/{workspace_id}/stats", response_model=WhiteboardStats)
async def get_whiteboard_stats(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get whiteboard statistics for a workspace"""
    # Check workspace access
    has_access = await check_workspace_access(workspace_id, current_user, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    # Total whiteboards
    total_stmt = select(func.count(Whiteboard.id)).where(
        Whiteboard.workspace_id == workspace_id
    )
    total_result = await db.execute(total_stmt)
    total_whiteboards = total_result.scalar() or 0

    # Total elements
    elements_stmt = select(func.count(WhiteboardElement.id)).where(
        WhiteboardElement.whiteboard_id.in_(
            select(Whiteboard.id).where(Whiteboard.workspace_id == workspace_id)
        ),
        WhiteboardElement.is_deleted == False
    )
    elements_result = await db.execute(elements_stmt)
    total_elements = elements_result.scalar() or 0

    # Active participants
    active_stmt = select(func.count(WhiteboardParticipant.id)).where(
        WhiteboardParticipant.whiteboard_id.in_(
            select(Whiteboard.id).where(Whiteboard.workspace_id == workspace_id)
        ),
        WhiteboardParticipant.is_active == True
    )
    active_result = await db.execute(active_stmt)
    active_participants = active_result.scalar() or 0

    # Recent activity
    recent_stmt = select(Whiteboard).where(
        Whiteboard.workspace_id == workspace_id
    ).order_by(desc(Whiteboard.last_activity_at)).limit(5)
    recent_result = await db.execute(recent_stmt)
    recent_whiteboards = recent_result.scalars().all()

    recent_activity = []
    for wb in recent_whiteboards:
        recent_activity.append(await build_whiteboard_response(wb, db))

    return WhiteboardStats(
        total_whiteboards=total_whiteboards,
        total_elements=total_elements,
        active_participants=active_participants,
        recent_activity=recent_activity,
    )
