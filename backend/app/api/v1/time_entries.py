"""
Time Tracking API
Provides endpoints for managing time entries (timer and manual tracking)
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    TimeEntry,
    Workspace,
    WorkspaceMember,
    Project,
    Task,
)
from app.schemas.time_entry import (
    TimeEntryManualCreate,
    TimeEntryTimerStart,
    TimeEntryTimerStop,
    TimeEntryUpdate,
    TimeEntryResponse,
    TimeEntryListResponse,
    TimeSummary,
    TimeEntryFilters,
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
) -> WorkspaceMember:
    """
    Check if user has access to the workspace.
    Returns the workspace membership or raises 403.
    """
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


async def get_time_entry_with_access_check(
    entry_id: int,
    user: User,
    db: AsyncSession
) -> TimeEntry:
    """
    Get time entry and verify user has workspace access.
    Returns the time entry or raises 404/403.
    """
    stmt = select(TimeEntry).where(TimeEntry.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found"
        )

    # Check workspace access
    await check_workspace_access(entry.workspace_id, user, db)

    return entry


async def get_running_timer(user_id: int, db: AsyncSession) -> Optional[TimeEntry]:
    """
    Get the currently running timer for a user, if any.
    """
    stmt = select(TimeEntry).where(
        TimeEntry.user_id == user_id,
        TimeEntry.end_time.is_(None),
        TimeEntry.is_manual == False
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def build_time_entry_response(entry: TimeEntry, db: AsyncSession) -> TimeEntryResponse:
    """
    Build a TimeEntryResponse with nested user/project/task information.
    """
    # Load relationships if not already loaded
    stmt = select(TimeEntry).options(
        selectinload(TimeEntry.user),
        selectinload(TimeEntry.project),
        selectinload(TimeEntry.task)
    ).where(TimeEntry.id == entry.id)
    result = await db.execute(stmt)
    entry = result.scalar_one()

    return TimeEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        workspace_id=entry.workspace_id,
        project_id=entry.project_id,
        task_id=entry.task_id,
        description=entry.description,
        start_time=entry.start_time,
        end_time=entry.end_time,
        duration_minutes=entry.duration_minutes,
        is_billable=entry.is_billable,
        is_manual=entry.is_manual,
        is_running=entry.is_running,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        user_email=entry.user.email if entry.user else None,
        user_name=entry.user.full_name if entry.user else None,
        project_name=entry.project.name if entry.project else None,
        task_title=entry.task.title if entry.task else None,
    )


# ============================================
# Timer Endpoints
# ============================================
@router.post("/start", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def start_timer(
    timer_data: TimeEntryTimerStart,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new timer for time tracking.
    Only one timer can be running per user at a time.
    """
    # Check workspace access
    await check_workspace_access(timer_data.workspace_id, current_user, db)

    # Check if user already has a running timer
    running_timer = await get_running_timer(current_user.id, db)
    if running_timer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a running timer. Stop it before starting a new one."
        )

    # Verify project belongs to workspace if provided
    if timer_data.project_id:
        stmt = select(Project).where(
            Project.id == timer_data.project_id,
            Project.workspace_id == timer_data.workspace_id
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found or doesn't belong to this workspace"
            )

    # Verify task belongs to project if provided
    if timer_data.task_id:
        if not timer_data.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task requires a project to be specified"
            )

        stmt = select(Task).where(
            Task.id == timer_data.task_id,
            Task.project_id == timer_data.project_id
        )
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not found or doesn't belong to this project"
            )

    # Create time entry with timer running
    new_entry = TimeEntry(
        user_id=current_user.id,
        workspace_id=timer_data.workspace_id,
        project_id=timer_data.project_id,
        task_id=timer_data.task_id,
        description=timer_data.description,
        start_time=datetime.utcnow(),
        end_time=None,  # Running timer
        duration_minutes=None,
        is_billable=timer_data.is_billable,
        is_manual=False
    )

    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)

    return await build_time_entry_response(new_entry, db)


@router.put("/{entry_id}/stop", response_model=TimeEntryResponse)
async def stop_timer(
    entry_id: int,
    stop_data: TimeEntryTimerStop,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stop a running timer.
    Calculates and saves the duration.
    """
    entry = await get_time_entry_with_access_check(entry_id, current_user, db)

    # Verify this is the user's timer
    if entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only stop your own timers"
        )

    # Verify timer is running
    if not entry.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This timer is not running"
        )

    # Stop the timer
    entry.end_time = datetime.utcnow()
    entry.duration_minutes = Decimal(str(entry.calculate_duration()))

    # Update description if provided
    if stop_data.description is not None:
        entry.description = stop_data.description

    await db.commit()
    await db.refresh(entry)

    return await build_time_entry_response(entry, db)


@router.get("/current", response_model=Optional[TimeEntryResponse])
async def get_current_timer(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the currently running timer for the authenticated user.
    Returns null if no timer is running.
    """
    running_timer = await get_running_timer(current_user.id, db)

    if not running_timer:
        return None

    return await build_time_entry_response(running_timer, db)


# ============================================
# Manual Entry Endpoints
# ============================================
@router.post("/manual", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_entry(
    entry_data: TimeEntryManualCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a manual time entry with specified start and end times.
    """
    # Check workspace access
    await check_workspace_access(entry_data.workspace_id, current_user, db)

    # Verify project belongs to workspace if provided
    if entry_data.project_id:
        stmt = select(Project).where(
            Project.id == entry_data.project_id,
            Project.workspace_id == entry_data.workspace_id
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found or doesn't belong to this workspace"
            )

    # Verify task belongs to project if provided
    if entry_data.task_id:
        if not entry_data.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task requires a project to be specified"
            )

        stmt = select(Task).where(
            Task.id == entry_data.task_id,
            Task.project_id == entry_data.project_id
        )
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not found or doesn't belong to this project"
            )

    # Calculate duration if not provided
    duration = entry_data.duration_minutes
    if duration is None:
        delta = entry_data.end_time - entry_data.start_time
        duration = Decimal(str(round(delta.total_seconds() / 60, 2)))

    # Create manual time entry
    new_entry = TimeEntry(
        user_id=current_user.id,
        workspace_id=entry_data.workspace_id,
        project_id=entry_data.project_id,
        task_id=entry_data.task_id,
        description=entry_data.description,
        start_time=entry_data.start_time,
        end_time=entry_data.end_time,
        duration_minutes=duration,
        is_billable=entry_data.is_billable,
        is_manual=True
    )

    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)

    return await build_time_entry_response(new_entry, db)


# ============================================
# CRUD Endpoints
# ============================================
@router.get("/", response_model=TimeEntryListResponse)
async def list_time_entries(
    workspace_id: int = Query(..., gt=0),
    user_id: Optional[int] = Query(None, gt=0),
    project_id: Optional[int] = Query(None, gt=0),
    task_id: Optional[int] = Query(None, gt=0),
    is_billable: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List time entries with optional filters.
    User must have access to the workspace.
    """
    # Check workspace access
    await check_workspace_access(workspace_id, current_user, db)

    # Build query
    stmt = select(TimeEntry).where(TimeEntry.workspace_id == workspace_id)

    # Apply filters
    if user_id:
        stmt = stmt.where(TimeEntry.user_id == user_id)

    if project_id:
        stmt = stmt.where(TimeEntry.project_id == project_id)

    if task_id:
        stmt = stmt.where(TimeEntry.task_id == task_id)

    if is_billable is not None:
        stmt = stmt.where(TimeEntry.is_billable == is_billable)

    if start_date:
        stmt = stmt.where(TimeEntry.start_time >= start_date)

    if end_date:
        stmt = stmt.where(TimeEntry.start_time <= end_date)

    # Order by start time descending (most recent first)
    stmt = stmt.order_by(TimeEntry.start_time.desc())

    # Count total before pagination
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Build responses
    entry_responses = []
    for entry in entries:
        entry_responses.append(await build_time_entry_response(entry, db))

    # Calculate total duration
    duration_stmt = select(func.sum(TimeEntry.duration_minutes)).where(
        TimeEntry.workspace_id == workspace_id
    )
    if user_id:
        duration_stmt = duration_stmt.where(TimeEntry.user_id == user_id)
    if project_id:
        duration_stmt = duration_stmt.where(TimeEntry.project_id == project_id)
    if task_id:
        duration_stmt = duration_stmt.where(TimeEntry.task_id == task_id)
    if is_billable is not None:
        duration_stmt = duration_stmt.where(TimeEntry.is_billable == is_billable)
    if start_date:
        duration_stmt = duration_stmt.where(TimeEntry.start_time >= start_date)
    if end_date:
        duration_stmt = duration_stmt.where(TimeEntry.start_time <= end_date)

    duration_result = await db.execute(duration_stmt)
    total_duration = duration_result.scalar() or Decimal('0')

    return TimeEntryListResponse(
        entries=entry_responses,
        total=total,
        total_duration_minutes=total_duration
    )


@router.get("/{entry_id}", response_model=TimeEntryResponse)
async def get_time_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific time entry.
    User must have access to the workspace.
    """
    entry = await get_time_entry_with_access_check(entry_id, current_user, db)
    return await build_time_entry_response(entry, db)


@router.put("/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(
    entry_id: int,
    entry_update: TimeEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a time entry.
    Only the owner can update their entries.
    Cannot update a running timer (stop it first).
    """
    entry = await get_time_entry_with_access_check(entry_id, current_user, db)

    # Verify ownership
    if entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own time entries"
        )

    # Cannot update running timer
    if entry.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a running timer. Stop it first."
        )

    # Update fields
    update_data = entry_update.model_dump(exclude_unset=True)

    # If start_time or end_time changed, recalculate duration
    if 'start_time' in update_data or 'end_time' in update_data:
        start = update_data.get('start_time', entry.start_time)
        end = update_data.get('end_time', entry.end_time)

        if start and end:
            if end <= start:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time must be after start time"
                )

            # Recalculate duration
            delta = end - start
            update_data['duration_minutes'] = Decimal(str(round(delta.total_seconds() / 60, 2)))

    for field, value in update_data.items():
        setattr(entry, field, value)

    await db.commit()
    await db.refresh(entry)

    return await build_time_entry_response(entry, db)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a time entry.
    Only the owner can delete their entries.
    """
    entry = await get_time_entry_with_access_check(entry_id, current_user, db)

    # Verify ownership
    if entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own time entries"
        )

    await db.delete(entry)
    await db.commit()


# ============================================
# Summary/Statistics Endpoints
# ============================================
@router.get("/summary/stats", response_model=TimeSummary)
async def get_time_summary(
    workspace_id: int = Query(..., gt=0),
    user_id: Optional[int] = Query(None, gt=0),
    project_id: Optional[int] = Query(None, gt=0),
    task_id: Optional[int] = Query(None, gt=0),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get time tracking statistics/summary.
    Includes total entries, total duration, billable/non-billable breakdown.
    """
    # Check workspace access
    await check_workspace_access(workspace_id, current_user, db)

    # Build base query
    base_query = select(TimeEntry).where(TimeEntry.workspace_id == workspace_id)

    # Apply filters
    if user_id:
        base_query = base_query.where(TimeEntry.user_id == user_id)
    if project_id:
        base_query = base_query.where(TimeEntry.project_id == project_id)
    if task_id:
        base_query = base_query.where(TimeEntry.task_id == task_id)
    if start_date:
        base_query = base_query.where(TimeEntry.start_time >= start_date)
    if end_date:
        base_query = base_query.where(TimeEntry.start_time <= end_date)

    # Total entries count
    count_stmt = select(func.count()).select_from(base_query.alias())
    count_result = await db.execute(count_stmt)
    total_entries = count_result.scalar()

    # Total duration
    total_duration_stmt = select(func.sum(TimeEntry.duration_minutes)).select_from(
        base_query.alias()
    )
    total_duration_result = await db.execute(total_duration_stmt)
    total_duration = total_duration_result.scalar() or Decimal('0')

    # Billable duration
    billable_query = base_query.where(TimeEntry.is_billable == True)
    billable_duration_stmt = select(func.sum(TimeEntry.duration_minutes)).select_from(
        billable_query.alias()
    )
    billable_duration_result = await db.execute(billable_duration_stmt)
    billable_duration = billable_duration_result.scalar() or Decimal('0')

    # Non-billable duration
    non_billable_duration = total_duration - billable_duration

    return TimeSummary(
        user_id=user_id,
        workspace_id=workspace_id,
        project_id=project_id,
        task_id=task_id,
        total_entries=total_entries,
        total_duration_minutes=total_duration,
        billable_duration_minutes=billable_duration,
        non_billable_duration_minutes=non_billable_duration,
        start_date=start_date,
        end_date=end_date
    )
