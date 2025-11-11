"""
Calendars API
Endpoints for managing calendars (personal and workspace)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    Calendar,
    Event,
    Workspace,
    WorkspaceMember,
)
from app.schemas.calendar import (
    CalendarCreate,
    CalendarUpdate,
    CalendarResponse,
    CalendarListResponse,
)
from app.core.deps import get_current_user

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_workspace_access(
    workspace_id: int,
    user: User,
    db: AsyncSession
) -> WorkspaceMember:
    """Check if user has access to the workspace"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    return membership


async def get_calendar_with_access_check(
    calendar_id: int,
    user: User,
    db: AsyncSession
) -> Calendar:
    """Get calendar and verify user has access"""
    stmt = select(Calendar).where(Calendar.id == calendar_id)
    result = await db.execute(stmt)
    calendar = result.scalar_one_or_none()

    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )

    # Check access
    if calendar.owner_id:
        # Personal calendar - only owner can access
        if calendar.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this calendar"
            )
    elif calendar.workspace_id:
        # Workspace calendar - check workspace membership
        await check_workspace_access(calendar.workspace_id, user, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Calendar has no owner or workspace"
        )

    return calendar


async def build_calendar_response(calendar: Calendar, db: AsyncSession) -> CalendarResponse:
    """Build calendar response with statistics"""
    # Load owner relationship
    stmt = select(Calendar).options(
        selectinload(Calendar.owner)
    ).where(Calendar.id == calendar.id)
    result = await db.execute(stmt)
    calendar = result.scalar_one()

    # Count events
    event_count_stmt = select(func.count(Event.id)).where(
        Event.calendar_id == calendar.id,
        Event.is_cancelled == False
    )
    event_count_result = await db.execute(event_count_stmt)
    event_count = event_count_result.scalar()

    return CalendarResponse(
        id=calendar.id,
        name=calendar.name,
        description=calendar.description,
        color=calendar.color,
        timezone=calendar.timezone,
        owner_id=calendar.owner_id,
        workspace_id=calendar.workspace_id,
        is_default=calendar.is_default,
        is_public=calendar.is_public,
        created_at=calendar.created_at,
        updated_at=calendar.updated_at,
        owner_email=calendar.owner.email if calendar.owner else None,
        owner_name=calendar.owner.full_name if calendar.owner else None,
        event_count=event_count,
    )


# ============================================
# Calendar CRUD Endpoints
# ============================================
@router.post("/", response_model=CalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar(
    calendar_data: CalendarCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new calendar (personal or workspace).
    If workspace_id is provided, creates workspace calendar.
    Otherwise, creates personal calendar.
    """
    # If workspace calendar, check access
    if calendar_data.workspace_id:
        await check_workspace_access(calendar_data.workspace_id, current_user, db)
        owner_id = None
        workspace_id = calendar_data.workspace_id
    else:
        # Personal calendar
        owner_id = current_user.id
        workspace_id = None

    # If setting as default, unset other defaults
    if calendar_data.is_default and owner_id:
        stmt = select(Calendar).where(
            Calendar.owner_id == owner_id,
            Calendar.is_default == True
        )
        result = await db.execute(stmt)
        existing_defaults = result.scalars().all()

        for cal in existing_defaults:
            cal.is_default = False

    # Create calendar
    new_calendar = Calendar(
        name=calendar_data.name,
        description=calendar_data.description,
        color=calendar_data.color,
        timezone=calendar_data.timezone,
        owner_id=owner_id,
        workspace_id=workspace_id,
        is_default=calendar_data.is_default,
        is_public=calendar_data.is_public
    )

    db.add(new_calendar)
    await db.commit()
    await db.refresh(new_calendar)

    return await build_calendar_response(new_calendar, db)


@router.get("/", response_model=CalendarListResponse)
async def list_calendars(
    workspace_id: Optional[int] = Query(None, gt=0),
    include_public: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List calendars accessible to the user.
    Includes personal calendars and workspace calendars.
    """
    # Build query
    conditions = []

    # Personal calendars
    conditions.append(Calendar.owner_id == current_user.id)

    # Workspace calendars if specified
    if workspace_id:
        await check_workspace_access(workspace_id, current_user, db)
        conditions.append(Calendar.workspace_id == workspace_id)
    else:
        # Get all workspace calendars user has access to
        workspace_stmt = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == current_user.id
        )
        workspace_result = await db.execute(workspace_stmt)
        workspace_ids = [row[0] for row in workspace_result.fetchall()]

        if workspace_ids:
            conditions.append(Calendar.workspace_id.in_(workspace_ids))

    # Public calendars if requested
    if include_public:
        conditions.append(Calendar.is_public == True)

    # Combine conditions with OR
    stmt = select(Calendar).where(or_(*conditions))

    # Order by default first, then created_at
    stmt = stmt.order_by(Calendar.is_default.desc(), Calendar.created_at.desc())

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    calendars = result.scalars().all()

    # Build responses
    calendar_responses = []
    for calendar in calendars:
        calendar_responses.append(await build_calendar_response(calendar, db))

    return CalendarListResponse(
        calendars=calendar_responses,
        total=total
    )


@router.get("/{calendar_id}", response_model=CalendarResponse)
async def get_calendar(
    calendar_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get calendar details"""
    calendar = await get_calendar_with_access_check(calendar_id, current_user, db)
    return await build_calendar_response(calendar, db)


@router.put("/{calendar_id}", response_model=CalendarResponse)
async def update_calendar(
    calendar_id: int,
    calendar_update: CalendarUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update calendar details.
    Only owner can update personal calendars.
    Workspace members can update workspace calendars.
    """
    calendar = await get_calendar_with_access_check(calendar_id, current_user, db)

    # Update fields
    update_data = calendar_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(calendar, field, value)

    await db.commit()
    await db.refresh(calendar)

    return await build_calendar_response(calendar, db)


@router.delete("/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(
    calendar_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a calendar.
    Only owner can delete personal calendars.
    Workspace admins can delete workspace calendars.
    """
    calendar = await get_calendar_with_access_check(calendar_id, current_user, db)

    # Additional check for workspace calendars - only admins can delete
    if calendar.workspace_id:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == calendar.workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        result = await db.execute(stmt)
        membership = result.scalar_one_or_none()

        if not membership or membership.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace admins can delete workspace calendars"
            )

    await db.delete(calendar)
    await db.commit()


@router.post("/{calendar_id}/set-default", response_model=CalendarResponse)
async def set_default_calendar(
    calendar_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set a personal calendar as the default calendar.
    Only works for personal calendars.
    """
    calendar = await get_calendar_with_access_check(calendar_id, current_user, db)

    # Must be personal calendar
    if not calendar.owner_id or calendar.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only set personal calendars as default"
        )

    # Unset other defaults
    stmt = select(Calendar).where(
        Calendar.owner_id == current_user.id,
        Calendar.is_default == True
    )
    result = await db.execute(stmt)
    existing_defaults = result.scalars().all()

    for cal in existing_defaults:
        cal.is_default = False

    # Set as default
    calendar.is_default = True

    await db.commit()
    await db.refresh(calendar)

    return await build_calendar_response(calendar, db)


@router.get("/user/default", response_model=CalendarResponse)
async def get_default_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's default calendar.
    Creates one if it doesn't exist.
    """
    # Try to find default calendar
    stmt = select(Calendar).where(
        Calendar.owner_id == current_user.id,
        Calendar.is_default == True
    )
    result = await db.execute(stmt)
    default_calendar = result.scalar_one_or_none()

    # If no default, create one
    if not default_calendar:
        default_calendar = Calendar(
            name="My Calendar",
            description="Personal calendar",
            color="#3B82F6",
            timezone="UTC",
            owner_id=current_user.id,
            workspace_id=None,
            is_default=True,
            is_public=False
        )

        db.add(default_calendar)
        await db.commit()
        await db.refresh(default_calendar)

    return await build_calendar_response(default_calendar, db)
