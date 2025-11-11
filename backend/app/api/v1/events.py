"""
Events API
Endpoints for managing calendar events, attendees, and RSVPs
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    Calendar,
    Event,
    EventAttendee,
    EventReminder,
    RSVPStatus,
)
from app.schemas.calendar import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    EventAttendeeAdd,
    EventAttendeeUpdate,
    RSVPUpdate,
    EventReminderCreate,
    EventReminderResponse,
    EventSearchFilters,
    AvailabilityQuery,
    UserAvailability,
    AvailabilityResponse,
)
from app.core.deps import get_current_user

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def get_event_with_access_check(
    event_id: int,
    user: User,
    db: AsyncSession
) -> Event:
    """Get event and verify user has access"""
    stmt = select(Event).where(Event.id == event_id)
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Load calendar
    calendar_stmt = select(Calendar).where(Calendar.id == event.calendar_id)
    calendar_result = await db.execute(calendar_stmt)
    calendar = calendar_result.scalar_one()

    # Check access based on event visibility
    if event.visibility == "private":
        # Private - only creator and attendees
        if event.created_by_id != user.id:
            attendee_stmt = select(EventAttendee).where(
                EventAttendee.event_id == event_id,
                EventAttendee.user_id == user.id
            )
            attendee_result = await db.execute(attendee_stmt)
            if not attendee_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this private event"
                )
    elif event.visibility == "workspace":
        # Workspace - check workspace access
        if calendar.workspace_id:
            from app.db.models import WorkspaceMember
            workspace_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == calendar.workspace_id,
                WorkspaceMember.user_id == user.id
            )
            workspace_result = await db.execute(workspace_stmt)
            if not workspace_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this workspace event"
                )
    # Public events are accessible to all

    return event


async def build_event_response(event: Event, db: AsyncSession) -> EventResponse:
    """Build event response with nested attendees"""
    # Load relationships
    stmt = select(Event).options(
        selectinload(Event.creator),
        selectinload(Event.calendar),
        selectinload(Event.attendees).selectinload(EventAttendee.user)
    ).where(Event.id == event.id)
    result = await db.execute(stmt)
    event = result.scalar_one()

    # Build attendee info
    from app.schemas.calendar import EventAttendeeInfo
    attendees = []
    for attendee in event.attendees:
        attendees.append(EventAttendeeInfo(
            id=attendee.id,
            user_id=attendee.user_id,
            rsvp_status=attendee.rsvp_status,
            is_organizer=attendee.is_organizer,
            is_optional=attendee.is_optional,
            comment=attendee.comment,
            responded_at=attendee.responded_at,
            user_email=attendee.user.email if attendee.user else None,
            user_name=attendee.user.full_name if attendee.user else None,
            user_avatar=attendee.user.avatar_url if attendee.user else None,
        ))

    return EventResponse(
        id=event.id,
        calendar_id=event.calendar_id,
        created_by_id=event.created_by_id,
        project_id=event.project_id,
        task_id=event.task_id,
        title=event.title,
        description=event.description,
        location=event.location,
        event_type=event.event_type,
        visibility=event.visibility,
        start_time=event.start_time,
        end_time=event.end_time,
        is_all_day=event.is_all_day,
        timezone=event.timezone,
        recurrence_rule=event.recurrence_rule,
        color=event.color,
        is_cancelled=event.is_cancelled,
        created_at=event.created_at,
        updated_at=event.updated_at,
        creator_email=event.creator.email if event.creator else None,
        creator_name=event.creator.full_name if event.creator else None,
        calendar_name=event.calendar.name if event.calendar else None,
        calendar_color=event.calendar.color if event.calendar else None,
        attendees=attendees,
        attendee_count=len(attendees),
    )


# ============================================
# Event CRUD Endpoints
# ============================================
@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new event in a calendar.
    Creator is automatically added as organizer attendee.
    """
    # Verify calendar access
    calendar_stmt = select(Calendar).where(Calendar.id == event_data.calendar_id)
    calendar_result = await db.execute(calendar_stmt)
    calendar = calendar_result.scalar_one_or_none()

    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )

    # Check calendar access
    if calendar.owner_id and calendar.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this calendar"
        )

    if calendar.workspace_id:
        from app.db.models import WorkspaceMember
        workspace_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == calendar.workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        workspace_result = await db.execute(workspace_stmt)
        if not workspace_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this workspace calendar"
            )

    # Create event
    new_event = Event(
        calendar_id=event_data.calendar_id,
        created_by_id=current_user.id,
        project_id=event_data.project_id,
        task_id=event_data.task_id,
        title=event_data.title,
        description=event_data.description,
        location=event_data.location,
        event_type=event_data.event_type,
        visibility=event_data.visibility,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        is_all_day=event_data.is_all_day,
        timezone=event_data.timezone,
        recurrence_rule=event_data.recurrence_rule,
        color=event_data.color,
    )

    db.add(new_event)
    await db.flush()

    # Add creator as organizer
    creator_attendee = EventAttendee(
        event_id=new_event.id,
        user_id=current_user.id,
        is_organizer=True,
        rsvp_status=RSVPStatus.ACCEPTED
    )
    db.add(creator_attendee)

    # Add other attendees
    if event_data.attendee_ids:
        for attendee_id in event_data.attendee_ids:
            if attendee_id != current_user.id:
                attendee = EventAttendee(
                    event_id=new_event.id,
                    user_id=attendee_id,
                    is_organizer=False,
                    rsvp_status=RSVPStatus.PENDING
                )
                db.add(attendee)

    await db.commit()
    await db.refresh(new_event)

    return await build_event_response(new_event, db)


@router.get("/", response_model=EventListResponse)
async def list_events(
    calendar_ids: Optional[str] = Query(None, description="Comma-separated calendar IDs"),
    event_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search_query: Optional[str] = Query(None, max_length=200),
    include_cancelled: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List events with filters.
    Returns events from accessible calendars within date range.
    """
    # Build query
    stmt = select(Event)

    # Filter by calendar IDs
    if calendar_ids:
        cal_id_list = [int(id.strip()) for id in calendar_ids.split(",")]
        stmt = stmt.where(Event.calendar_id.in_(cal_id_list))
    else:
        # Get all accessible calendars
        from app.db.models import WorkspaceMember
        calendar_conditions = [Calendar.owner_id == current_user.id]

        # Add workspace calendars
        workspace_stmt = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == current_user.id
        )
        workspace_result = await db.execute(workspace_stmt)
        workspace_ids = [row[0] for row in workspace_result.fetchall()]

        if workspace_ids:
            calendar_conditions.append(Calendar.workspace_id.in_(workspace_ids))

        # Public calendars
        calendar_conditions.append(Calendar.is_public == True)

        calendar_stmt = select(Calendar.id).where(or_(*calendar_conditions))
        calendar_result = await db.execute(calendar_stmt)
        accessible_calendar_ids = [row[0] for row in calendar_result.fetchall()]

        stmt = stmt.where(Event.calendar_id.in_(accessible_calendar_ids))

    # Filter by event type
    if event_type:
        stmt = stmt.where(Event.event_type == event_type)

    # Filter by date range
    if start_date:
        stmt = stmt.where(Event.end_time >= start_date)
    if end_date:
        stmt = stmt.where(Event.start_time <= end_date)

    # Filter by search query
    if search_query:
        stmt = stmt.where(
            or_(
                Event.title.ilike(f"%{search_query}%"),
                Event.description.ilike(f"%{search_query}%"),
                Event.location.ilike(f"%{search_query}%")
            )
        )

    # Filter cancelled events
    if not include_cancelled:
        stmt = stmt.where(Event.is_cancelled == False)

    # Order by start time
    stmt = stmt.order_by(Event.start_time.asc())

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    events = result.scalars().all()

    # Build responses
    event_responses = []
    for event in events:
        event_responses.append(await build_event_response(event, db))

    return EventListResponse(
        events=event_responses,
        total=total
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get event details"""
    event = await get_event_with_access_check(event_id, current_user, db)
    return await build_event_response(event, db)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update event details.
    Only creator or organizers can update events.
    """
    event = await get_event_with_access_check(event_id, current_user, db)

    # Check if user is creator or organizer
    is_creator = event.created_by_id == current_user.id
    organizer_stmt = select(EventAttendee).where(
        EventAttendee.event_id == event_id,
        EventAttendee.user_id == current_user.id,
        EventAttendee.is_organizer == True
    )
    organizer_result = await db.execute(organizer_stmt)
    is_organizer = organizer_result.scalar_one_or_none() is not None

    if not (is_creator or is_organizer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creators and organizers can update events"
        )

    # Update fields
    update_data = event_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    return await build_event_response(event, db)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an event.
    Only creator can delete events.
    """
    event = await get_event_with_access_check(event_id, current_user, db)

    # Only creator can delete
    if event.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event creator can delete the event"
        )

    await db.delete(event)
    await db.commit()


@router.post("/{event_id}/cancel", response_model=EventResponse)
async def cancel_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an event (soft delete).
    Only creator or organizers can cancel.
    """
    event = await get_event_with_access_check(event_id, current_user, db)

    # Check if user is creator or organizer
    is_creator = event.created_by_id == current_user.id
    organizer_stmt = select(EventAttendee).where(
        EventAttendee.event_id == event_id,
        EventAttendee.user_id == current_user.id,
        EventAttendee.is_organizer == True
    )
    organizer_result = await db.execute(organizer_stmt)
    is_organizer = organizer_result.scalar_one_or_none() is not None

    if not (is_creator or is_organizer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creators and organizers can cancel events"
        )

    event.is_cancelled = True
    await db.commit()
    await db.refresh(event)

    return await build_event_response(event, db)


# ============================================
# Event Attendee Endpoints
# ============================================
@router.post("/{event_id}/attendees", response_model=EventResponse)
async def add_attendee(
    event_id: int,
    attendee_data: EventAttendeeAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add an attendee to an event.
    Only creator or organizers can add attendees.
    """
    event = await get_event_with_access_check(event_id, current_user, db)

    # Check if user is creator or organizer
    is_creator = event.created_by_id == current_user.id
    organizer_stmt = select(EventAttendee).where(
        EventAttendee.event_id == event_id,
        EventAttendee.user_id == current_user.id,
        EventAttendee.is_organizer == True
    )
    organizer_result = await db.execute(organizer_stmt)
    is_organizer = organizer_result.scalar_one_or_none() is not None

    if not (is_creator or is_organizer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creators and organizers can add attendees"
        )

    # Check if already attendee
    existing_stmt = select(EventAttendee).where(
        EventAttendee.event_id == event_id,
        EventAttendee.user_id == attendee_data.user_id
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an attendee"
        )

    # Add attendee
    new_attendee = EventAttendee(
        event_id=event_id,
        user_id=attendee_data.user_id,
        is_organizer=False,
        is_optional=attendee_data.is_optional,
        rsvp_status=RSVPStatus.PENDING
    )

    db.add(new_attendee)
    await db.commit()

    return await build_event_response(event, db)


@router.delete("/{event_id}/attendees/{user_id}", response_model=EventResponse)
async def remove_attendee(
    event_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an attendee from an event.
    Creators/organizers can remove others, users can remove themselves.
    """
    event = await get_event_with_access_check(event_id, current_user, db)

    # Get attendee
    attendee_stmt = select(EventAttendee).where(
        EventAttendee.event_id == event_id,
        EventAttendee.user_id == user_id
    )
    attendee_result = await db.execute(attendee_stmt)
    attendee = attendee_result.scalar_one_or_none()

    if not attendee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendee not found"
        )

    # Check permissions
    is_self = user_id == current_user.id
    is_creator = event.created_by_id == current_user.id
    organizer_stmt = select(EventAttendee).where(
        EventAttendee.event_id == event_id,
        EventAttendee.user_id == current_user.id,
        EventAttendee.is_organizer == True
    )
    organizer_result = await db.execute(organizer_stmt)
    is_organizer = organizer_result.scalar_one_or_none() is not None

    if not (is_self or is_creator or is_organizer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove this attendee"
        )

    # Cannot remove creator/organizer
    if attendee.is_organizer and not is_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove organizers from event"
        )

    await db.delete(attendee)
    await db.commit()

    return await build_event_response(event, db)


@router.put("/{event_id}/rsvp", response_model=EventResponse)
async def update_rsvp(
    event_id: int,
    rsvp_data: RSVPUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update RSVP status for an event.
    Users can only update their own RSVP.
    """
    event = await get_event_with_access_check(event_id, current_user, db)

    # Get attendee record
    attendee_stmt = select(EventAttendee).where(
        EventAttendee.event_id == event_id,
        EventAttendee.user_id == current_user.id
    )
    attendee_result = await db.execute(attendee_stmt)
    attendee = attendee_result.scalar_one_or_none()

    if not attendee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not an attendee of this event"
        )

    # Update RSVP
    attendee.rsvp_status = rsvp_data.rsvp_status
    attendee.comment = rsvp_data.comment
    attendee.responded_at = datetime.utcnow()

    await db.commit()

    return await build_event_response(event, db)


@router.get("/user/upcoming", response_model=EventListResponse)
async def get_upcoming_events(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get upcoming events for the current user.
    Returns events user is attending or organizing.
    """
    from datetime import timedelta

    # Get events where user is attendee
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=days)

    stmt = select(Event).join(EventAttendee).where(
        EventAttendee.user_id == current_user.id,
        Event.start_time >= start_date,
        Event.start_time <= end_date,
        Event.is_cancelled == False
    ).order_by(Event.start_time.asc()).limit(limit)

    result = await db.execute(stmt)
    events = result.scalars().all()

    # Build responses
    event_responses = []
    for event in events:
        event_responses.append(await build_event_response(event, db))

    return EventListResponse(
        events=event_responses,
        total=len(event_responses)
    )
