"""
Meetings API
Endpoints for video/audio meetings with WebRTC support
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
import secrets

from app.db.session import get_db
from app.db.models import (
    User,
    Meeting,
    MeetingParticipant,
    MeetingRecording,
    MeetingChatMessage,
    MeetingType,
    MeetingStatus,
    ParticipantRole,
    ParticipantStatus,
    RecordingStatus,
    Workspace,
    WorkspaceMember,
)
from app.schemas.meeting import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingListResponse,
    MeetingJoinResponse,
    MeetingSettingsUpdate,
    MeetingParticipantInvite,
    MeetingParticipantUpdate,
    MeetingParticipantStateUpdate,
    MeetingParticipantResponse,
    MeetingParticipantListResponse,
    MeetingRecordingCreate,
    MeetingRecordingUpdate,
    MeetingRecordingResponse,
    MeetingRecordingListResponse,
    MeetingChatMessageCreate,
    MeetingChatMessageResponse,
    MeetingChatMessageListResponse,
    MeetingStats,
)
from app.api.deps import get_current_user

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_meeting_access(
    meeting_id: int,
    user: User,
    db: AsyncSession,
    required_role: Optional[ParticipantRole] = None
) -> Optional[Meeting]:
    """Check if user has access to meeting"""
    # Load meeting
    stmt = select(Meeting).where(Meeting.id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        return None

    # Check workspace membership
    workspace_stmt = select(WorkspaceMember).where(
        and_(
            WorkspaceMember.workspace_id == meeting.workspace_id,
            WorkspaceMember.user_id == user.id
        )
    )
    workspace_result = await db.execute(workspace_stmt)
    workspace_member = workspace_result.scalar_one_or_none()

    if not workspace_member:
        return None

    # Creator always has access
    if meeting.created_by_id == user.id:
        return meeting

    # Check participant access
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == user.id
        )
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    # If meeting is public, workspace members can view
    if meeting.is_public and not required_role:
        return meeting

    # If not participant and not public, no access
    if not participant:
        return None

    # Check role requirement
    if required_role:
        role_hierarchy = {
            ParticipantRole.ATTENDEE: 1,
            ParticipantRole.CO_HOST: 2,
            ParticipantRole.HOST: 3,
        }
        if role_hierarchy.get(participant.role, 0) < role_hierarchy.get(required_role, 0):
            return None

    return meeting


async def build_meeting_response(meeting: Meeting, db: AsyncSession) -> MeetingResponse:
    """Build meeting response with nested information"""
    # Load creator
    if not meeting.created_by:
        await db.refresh(meeting, ['created_by'])

    # Count participants
    participant_stmt = select(func.count(MeetingParticipant.id)).where(
        MeetingParticipant.meeting_id == meeting.id
    )
    participant_result = await db.execute(participant_stmt)
    total_participants = participant_result.scalar() or 0

    # Count active participants
    active_stmt = select(func.count(MeetingParticipant.id)).where(
        and_(
            MeetingParticipant.meeting_id == meeting.id,
            MeetingParticipant.status == ParticipantStatus.JOINED
        )
    )
    active_result = await db.execute(active_stmt)
    active_participants = active_result.scalar() or 0

    # Count recordings
    recording_stmt = select(func.count(MeetingRecording.id)).where(
        MeetingRecording.meeting_id == meeting.id
    )
    recording_result = await db.execute(recording_stmt)
    recording_count = recording_result.scalar() or 0

    response = MeetingResponse.model_validate(meeting)
    response.creator_name = meeting.created_by.full_name if meeting.created_by else None
    response.creator_email = meeting.created_by.email if meeting.created_by else None
    response.active_participant_count = active_participants
    response.recording_count = recording_count

    return response


async def build_participant_response(participant: MeetingParticipant, db: AsyncSession) -> MeetingParticipantResponse:
    """Build participant response with nested information"""
    # Load user if present
    if participant.user_id and not participant.user:
        await db.refresh(participant, ['user'])

    response = MeetingParticipantResponse.model_validate(participant)
    if participant.user:
        response.user_name = participant.user.full_name
        response.user_email = participant.user.email
        response.user_avatar = participant.user.avatar_url

    return response


# ============================================
# Meeting CRUD Endpoints
# ============================================
@router.post("/", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_data: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new meeting.
    Automatically adds creator as host participant.
    """
    # Check workspace membership
    workspace_stmt = select(WorkspaceMember).where(
        and_(
            WorkspaceMember.workspace_id == meeting_data.workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
    )
    workspace_result = await db.execute(workspace_stmt)
    workspace_member = workspace_result.scalar_one_or_none()

    if not workspace_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    # Generate meeting URL
    meeting_url = f"/meetings/{secrets.token_urlsafe(16)}"

    # Create meeting
    new_meeting = Meeting(
        workspace_id=meeting_data.workspace_id,
        created_by_id=current_user.id,
        project_id=meeting_data.project_id,
        event_id=meeting_data.event_id,
        whiteboard_id=meeting_data.whiteboard_id,
        title=meeting_data.title,
        description=meeting_data.description,
        meeting_type=meeting_data.meeting_type,
        status=MeetingStatus.SCHEDULED if meeting_data.scheduled_start_time else MeetingStatus.WAITING,
        scheduled_start_time=meeting_data.scheduled_start_time,
        scheduled_end_time=meeting_data.scheduled_end_time,
        duration_minutes=meeting_data.duration_minutes,
        meeting_url=meeting_url,
        meeting_passcode=meeting_data.meeting_passcode,
        waiting_room_enabled=meeting_data.waiting_room_enabled,
        mute_on_join=meeting_data.mute_on_join,
        video_on_join=meeting_data.video_on_join,
        allow_screen_share=meeting_data.allow_screen_share,
        allow_chat=meeting_data.allow_chat,
        allow_recording=meeting_data.allow_recording,
        max_participants=meeting_data.max_participants,
        auto_record=meeting_data.auto_record,
        record_audio=meeting_data.record_audio,
        record_video=meeting_data.record_video,
        record_screen_share=meeting_data.record_screen_share,
        is_public=meeting_data.is_public,
        require_authentication=meeting_data.require_authentication,
    )

    db.add(new_meeting)
    await db.flush()

    # Add creator as host
    host_participant = MeetingParticipant(
        meeting_id=new_meeting.id,
        user_id=current_user.id,
        role=ParticipantRole.HOST,
        status=ParticipantStatus.INVITED,
    )
    db.add(host_participant)

    # Invite participants
    if meeting_data.participant_user_ids:
        for user_id in meeting_data.participant_user_ids:
            if user_id != current_user.id:  # Don't re-invite creator
                participant = MeetingParticipant(
                    meeting_id=new_meeting.id,
                    user_id=user_id,
                    role=ParticipantRole.ATTENDEE,
                    status=ParticipantStatus.INVITED,
                )
                db.add(participant)

    await db.commit()
    await db.refresh(new_meeting)

    return await build_meeting_response(new_meeting, db)


@router.get("/", response_model=MeetingListResponse)
async def list_meetings(
    workspace_id: int = Query(..., gt=0),
    project_id: Optional[int] = Query(None, gt=0),
    status: Optional[MeetingStatus] = None,
    meeting_type: Optional[MeetingType] = None,
    upcoming: bool = Query(False, description="Show only upcoming meetings"),
    active: bool = Query(False, description="Show only active meetings"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List meetings in a workspace.
    Shows meetings user has access to (participant, public, or creator).
    """
    # Check workspace membership
    workspace_stmt = select(WorkspaceMember).where(
        and_(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
    )
    workspace_result = await db.execute(workspace_stmt)
    workspace_member = workspace_result.scalar_one_or_none()

    if not workspace_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    # Build query
    conditions = [Meeting.workspace_id == workspace_id]

    if project_id:
        conditions.append(Meeting.project_id == project_id)

    if status:
        conditions.append(Meeting.status == status)

    if meeting_type:
        conditions.append(Meeting.meeting_type == meeting_type)

    if upcoming:
        conditions.append(Meeting.scheduled_start_time > datetime.utcnow())
        conditions.append(Meeting.status == MeetingStatus.SCHEDULED)

    if active:
        conditions.append(Meeting.status == MeetingStatus.IN_PROGRESS)

    # Get meetings where user is participant or creator or meeting is public
    stmt = select(Meeting).where(
        and_(*conditions),
        or_(
            Meeting.created_by_id == current_user.id,
            Meeting.is_public == True,
            Meeting.id.in_(
                select(MeetingParticipant.meeting_id).where(
                    MeetingParticipant.user_id == current_user.id
                )
            )
        )
    ).order_by(
        desc(Meeting.scheduled_start_time)
    ).offset(skip).limit(limit)

    result = await db.execute(stmt)
    meetings = result.scalars().all()

    # Get total count
    count_stmt = select(func.count(Meeting.id)).where(
        and_(*conditions),
        or_(
            Meeting.created_by_id == current_user.id,
            Meeting.is_public == True,
            Meeting.id.in_(
                select(MeetingParticipant.meeting_id).where(
                    MeetingParticipant.user_id == current_user.id
                )
            )
        )
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    meeting_responses = []
    for meeting in meetings:
        meeting_responses.append(await build_meeting_response(meeting, db))

    return MeetingListResponse(meetings=meeting_responses, total=total)


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get meeting details"""
    meeting = await check_meeting_access(meeting_id, current_user, db)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or access denied"
        )

    return await build_meeting_response(meeting, db)


@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: int,
    meeting_update: MeetingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update meeting settings - requires host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    # Update fields
    update_data = meeting_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)

    meeting.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(meeting)

    return await build_meeting_response(meeting, db)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete or cancel a meeting - requires host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    # If meeting hasn't started, delete it
    # If meeting is active or past, mark as cancelled
    if meeting.status in [MeetingStatus.SCHEDULED, MeetingStatus.WAITING]:
        await db.delete(meeting)
    else:
        meeting.status = MeetingStatus.CANCELLED
        meeting.updated_at = datetime.utcnow()

    await db.commit()


@router.post("/{meeting_id}/start", response_model=MeetingResponse)
async def start_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a meeting - requires host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    if meeting.status == MeetingStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting is already in progress"
        )

    meeting.status = MeetingStatus.IN_PROGRESS
    meeting.actual_start_time = datetime.utcnow()
    meeting.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(meeting)

    return await build_meeting_response(meeting, db)


@router.post("/{meeting_id}/end", response_model=MeetingResponse)
async def end_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """End a meeting - requires host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    if meeting.status != MeetingStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting is not in progress"
        )

    meeting.status = MeetingStatus.ENDED
    meeting.actual_end_time = datetime.utcnow()
    meeting.updated_at = datetime.utcnow()

    # Calculate total duration
    if meeting.actual_start_time:
        duration = (meeting.actual_end_time - meeting.actual_start_time).total_seconds()
        meeting.total_duration_seconds = int(duration)

    # Stop recording if active
    if meeting.is_recording:
        meeting.is_recording = False
        # Update active recordings
        recording_stmt = select(MeetingRecording).where(
            and_(
                MeetingRecording.meeting_id == meeting_id,
                MeetingRecording.status == RecordingStatus.RECORDING
            )
        )
        recording_result = await db.execute(recording_stmt)
        active_recordings = recording_result.scalars().all()

        for recording in active_recordings:
            recording.status = RecordingStatus.PROCESSING
            recording.recording_ended_at = datetime.utcnow()

    # Update all joined participants to left
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.status == ParticipantStatus.JOINED
        )
    )
    participant_result = await db.execute(participant_stmt)
    participants = participant_result.scalars().all()

    for participant in participants:
        participant.status = ParticipantStatus.LEFT
        participant.left_at = datetime.utcnow()
        if participant.joined_at:
            duration = (participant.left_at - participant.joined_at).total_seconds()
            participant.total_duration_seconds = int(duration)

    await db.commit()
    await db.refresh(meeting)

    return await build_meeting_response(meeting, db)


@router.put("/{meeting_id}/settings", response_model=MeetingResponse)
async def update_meeting_settings(
    meeting_id: int,
    settings_update: MeetingSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update meeting settings during active meeting - requires host or co-host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.CO_HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    # Update settings
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)

    meeting.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(meeting)

    return await build_meeting_response(meeting, db)


# ============================================
# Meeting Join Endpoint
# ============================================
@router.post("/{meeting_id}/join", response_model=MeetingJoinResponse)
async def join_meeting(
    meeting_id: int,
    passcode: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Join a meeting.
    Creates or updates participant record, returns meeting info and ICE servers for WebRTC.
    """
    meeting = await check_meeting_access(meeting_id, current_user, db)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or access denied"
        )

    # Check passcode if required
    if meeting.meeting_passcode and passcode != meeting.meeting_passcode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid meeting passcode"
        )

    # Check if meeting is in progress or waiting
    if meeting.status not in [MeetingStatus.IN_PROGRESS, MeetingStatus.WAITING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Meeting is {meeting.status.value}"
        )

    # Check max participants
    active_count_stmt = select(func.count(MeetingParticipant.id)).where(
        and_(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.status == ParticipantStatus.JOINED
        )
    )
    active_count_result = await db.execute(active_count_stmt)
    active_count = active_count_result.scalar() or 0

    if active_count >= meeting.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting is at maximum capacity"
        )

    # Get or create participant
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == current_user.id
        )
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        # Create new participant
        participant = MeetingParticipant(
            meeting_id=meeting_id,
            user_id=current_user.id,
            role=ParticipantRole.ATTENDEE,
            status=ParticipantStatus.WAITING if meeting.waiting_room_enabled and meeting.created_by_id != current_user.id else ParticipantStatus.JOINED,
            is_audio_enabled=not meeting.mute_on_join,
            is_video_enabled=meeting.video_on_join,
        )
        db.add(participant)
    else:
        # Update existing participant
        if meeting.waiting_room_enabled and participant.role != ParticipantRole.HOST and meeting.created_by_id != current_user.id:
            participant.status = ParticipantStatus.WAITING
        else:
            participant.status = ParticipantStatus.JOINED
            participant.joined_at = datetime.utcnow()

    # Update meeting participant counts
    if participant.status == ParticipantStatus.JOINED:
        meeting.total_participants += 1
        if active_count + 1 > meeting.peak_participants:
            meeting.peak_participants = active_count + 1

    await db.commit()
    await db.refresh(participant)

    # Get ICE servers (STUN/TURN configuration)
    ice_servers = [
        {"urls": "stun:stun.l.google.com:19302"},
        {"urls": "stun:stun1.l.google.com:19302"},
    ]

    return MeetingJoinResponse(
        meeting=await build_meeting_response(meeting, db),
        participant=await build_participant_response(participant, db),
        ice_servers=ice_servers
    )


@router.post("/{meeting_id}/leave", response_model=MeetingParticipantResponse)
async def leave_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave a meeting"""
    # Get participant
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == current_user.id
        )
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    participant.status = ParticipantStatus.LEFT
    participant.left_at = datetime.utcnow()
    participant.connection_id = None
    participant.peer_id = None

    # Calculate duration
    if participant.joined_at:
        duration = (participant.left_at - participant.joined_at).total_seconds()
        participant.total_duration_seconds = int(duration)

    await db.commit()
    await db.refresh(participant)

    return await build_participant_response(participant, db)


# ============================================
# Participant Management Endpoints
# ============================================
@router.get("/{meeting_id}/participants", response_model=MeetingParticipantListResponse)
async def list_participants(
    meeting_id: int,
    status: Optional[ParticipantStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all participants in a meeting"""
    meeting = await check_meeting_access(meeting_id, current_user, db)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or access denied"
        )

    conditions = [MeetingParticipant.meeting_id == meeting_id]
    if status:
        conditions.append(MeetingParticipant.status == status)

    stmt = select(MeetingParticipant).where(and_(*conditions)).order_by(
        MeetingParticipant.joined_at.desc()
    ).offset(skip).limit(limit)

    result = await db.execute(stmt)
    participants = result.scalars().all()

    count_stmt = select(func.count(MeetingParticipant.id)).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    participant_responses = []
    for participant in participants:
        participant_responses.append(await build_participant_response(participant, db))

    return MeetingParticipantListResponse(participants=participant_responses, total=total)


@router.post("/{meeting_id}/participants", response_model=MeetingParticipantResponse, status_code=status.HTTP_201_CREATED)
async def invite_participant(
    meeting_id: int,
    participant_data: MeetingParticipantInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a participant to meeting - requires host or co-host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.CO_HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    # Check if already participant
    if participant_data.user_id:
        existing_stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.user_id == participant_data.user_id
            )
        )
        existing_result = await db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a participant"
            )

    new_participant = MeetingParticipant(
        meeting_id=meeting_id,
        user_id=participant_data.user_id,
        guest_name=participant_data.guest_name,
        guest_email=participant_data.guest_email,
        role=participant_data.role,
        status=ParticipantStatus.INVITED,
        can_speak=participant_data.can_speak,
        can_share_screen=participant_data.can_share_screen,
        can_chat=participant_data.can_chat,
    )

    db.add(new_participant)
    await db.commit()
    await db.refresh(new_participant)

    return await build_participant_response(new_participant, db)


@router.put("/{meeting_id}/participants/{participant_id}", response_model=MeetingParticipantResponse)
async def update_participant(
    meeting_id: int,
    participant_id: int,
    participant_update: MeetingParticipantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update participant role and permissions - requires host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    # Get participant
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.id == participant_id,
            MeetingParticipant.meeting_id == meeting_id
        )
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    # Update fields
    update_data = participant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(participant, field, value)

    await db.commit()
    await db.refresh(participant)

    return await build_participant_response(participant, db)


@router.delete("/{meeting_id}/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_participant(
    meeting_id: int,
    participant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a participant from meeting - requires host or co-host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.CO_HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    # Get participant
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.id == participant_id,
            MeetingParticipant.meeting_id == meeting_id
        )
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    # Cannot remove host
    if participant.role == ParticipantRole.HOST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove meeting host"
        )

    participant.status = ParticipantStatus.REMOVED
    participant.left_at = datetime.utcnow()

    await db.commit()


@router.put("/{meeting_id}/participants/{participant_id}/state", response_model=MeetingParticipantResponse)
async def update_participant_state(
    meeting_id: int,
    participant_id: int,
    state_update: MeetingParticipantStateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update participant media state - participant can update their own state"""
    # Get participant
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.id == participant_id,
            MeetingParticipant.meeting_id == meeting_id
        )
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    # Participants can only update their own state
    if participant.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own state"
        )

    # Update state
    update_data = state_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(participant, field, value)

    await db.commit()
    await db.refresh(participant)

    return await build_participant_response(participant, db)


@router.post("/{meeting_id}/participants/{participant_id}/admit", response_model=MeetingParticipantResponse)
async def admit_participant(
    meeting_id: int,
    participant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admit participant from waiting room - requires host or co-host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.CO_HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    # Get participant
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.id == participant_id,
            MeetingParticipant.meeting_id == meeting_id
        )
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    if participant.status != ParticipantStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant is not in waiting room"
        )

    participant.status = ParticipantStatus.JOINED
    participant.joined_at = datetime.utcnow()

    await db.commit()
    await db.refresh(participant)

    return await build_participant_response(participant, db)


# ============================================
# Recording Endpoints
# ============================================
@router.get("/{meeting_id}/recordings", response_model=MeetingRecordingListResponse)
async def list_recordings(
    meeting_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List recordings for a meeting"""
    meeting = await check_meeting_access(meeting_id, current_user, db)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or access denied"
        )

    stmt = select(MeetingRecording).where(
        MeetingRecording.meeting_id == meeting_id
    ).order_by(desc(MeetingRecording.recording_started_at)).offset(skip).limit(limit)

    result = await db.execute(stmt)
    recordings = result.scalars().all()

    count_stmt = select(func.count(MeetingRecording.id)).where(
        MeetingRecording.meeting_id == meeting_id
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    recording_responses = []
    for recording in recordings:
        # Load relationships
        if not recording.started_by:
            await db.refresh(recording, ['started_by', 'meeting'])

        response = MeetingRecordingResponse.model_validate(recording)
        response.started_by_name = recording.started_by.full_name if recording.started_by else None
        response.meeting_title = recording.meeting.title if recording.meeting else None
        recording_responses.append(response)

    return MeetingRecordingListResponse(recordings=recording_responses, total=total)


@router.post("/{meeting_id}/recordings/start", response_model=MeetingRecordingResponse, status_code=status.HTTP_201_CREATED)
async def start_recording(
    meeting_id: int,
    recording_data: MeetingRecordingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start recording a meeting - requires host or co-host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.CO_HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    if not meeting.allow_recording:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recording is not allowed for this meeting"
        )

    if meeting.is_recording:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting is already being recorded"
        )

    # Create recording
    new_recording = MeetingRecording(
        meeting_id=meeting_id,
        started_by_id=current_user.id,
        name=recording_data.name,
        description=recording_data.description,
        status=RecordingStatus.RECORDING,
        is_public=recording_data.is_public,
        password_protected=recording_data.password_protected,
        access_password=recording_data.access_password,
        recording_started_at=datetime.utcnow(),
    )

    db.add(new_recording)
    meeting.is_recording = True

    await db.commit()
    await db.refresh(new_recording)

    # Load relationships
    await db.refresh(new_recording, ['started_by', 'meeting'])

    response = MeetingRecordingResponse.model_validate(new_recording)
    response.started_by_name = new_recording.started_by.full_name
    response.meeting_title = new_recording.meeting.title

    return response


@router.post("/{meeting_id}/recordings/{recording_id}/stop", response_model=MeetingRecordingResponse)
async def stop_recording(
    meeting_id: int,
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop an active recording - requires host or co-host role"""
    meeting = await check_meeting_access(meeting_id, current_user, db, required_role=ParticipantRole.CO_HOST)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or insufficient permissions"
        )

    # Get recording
    recording_stmt = select(MeetingRecording).where(
        and_(
            MeetingRecording.id == recording_id,
            MeetingRecording.meeting_id == meeting_id
        )
    )
    recording_result = await db.execute(recording_stmt)
    recording = recording_result.scalar_one_or_none()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )

    if recording.status != RecordingStatus.RECORDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording is not active"
        )

    recording.status = RecordingStatus.PROCESSING
    recording.recording_ended_at = datetime.utcnow()

    # Calculate duration
    if recording.recording_started_at:
        duration = (recording.recording_ended_at - recording.recording_started_at).total_seconds()
        recording.duration_seconds = int(duration)

    meeting.is_recording = False

    await db.commit()
    await db.refresh(recording)

    # Load relationships
    await db.refresh(recording, ['started_by', 'meeting'])

    response = MeetingRecordingResponse.model_validate(recording)
    response.started_by_name = recording.started_by.full_name
    response.meeting_title = recording.meeting.title

    return response


# ============================================
# Meeting Chat Endpoints
# ============================================
@router.get("/{meeting_id}/chat", response_model=MeetingChatMessageListResponse)
async def list_chat_messages(
    meeting_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List chat messages in a meeting"""
    meeting = await check_meeting_access(meeting_id, current_user, db)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or access denied"
        )

    # Get public messages and private messages to/from current user
    stmt = select(MeetingChatMessage).where(
        and_(
            MeetingChatMessage.meeting_id == meeting_id,
            MeetingChatMessage.is_deleted == False,
            or_(
                MeetingChatMessage.is_private == False,
                MeetingChatMessage.sender_id == current_user.id,
                MeetingChatMessage.recipient_id == current_user.id
            )
        )
    ).order_by(MeetingChatMessage.created_at).offset(skip).limit(limit)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    count_stmt = select(func.count(MeetingChatMessage.id)).where(
        and_(
            MeetingChatMessage.meeting_id == meeting_id,
            MeetingChatMessage.is_deleted == False,
            or_(
                MeetingChatMessage.is_private == False,
                MeetingChatMessage.sender_id == current_user.id,
                MeetingChatMessage.recipient_id == current_user.id
            )
        )
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    message_responses = []
    for message in messages:
        # Load relationships
        if message.sender_id and not message.sender:
            await db.refresh(message, ['sender'])
        if message.recipient_id and not message.recipient:
            await db.refresh(message, ['recipient'])

        response = MeetingChatMessageResponse.model_validate(message)
        if message.sender:
            response.sender_name = message.sender.full_name
            response.sender_avatar = message.sender.avatar_url
        if message.recipient:
            response.recipient_name = message.recipient.full_name

        message_responses.append(response)

    return MeetingChatMessageListResponse(messages=message_responses, total=total)


@router.post("/{meeting_id}/chat", response_model=MeetingChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    meeting_id: int,
    message_data: MeetingChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a chat message in meeting"""
    meeting = await check_meeting_access(meeting_id, current_user, db)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or access denied"
        )

    if not meeting.allow_chat:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chat is not allowed in this meeting"
        )

    # Check if user is participant with chat permission
    participant_stmt = select(MeetingParticipant).where(
        and_(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == current_user.id
        )
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalar_one_or_none()

    if not participant or not participant.can_chat:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to send chat messages"
        )

    # Validate private message
    if message_data.is_private and not message_data.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient ID required for private messages"
        )

    new_message = MeetingChatMessage(
        meeting_id=meeting_id,
        sender_id=current_user.id,
        message=message_data.message,
        is_private=message_data.is_private,
        recipient_id=message_data.recipient_id,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    # Load relationships
    await db.refresh(new_message, ['sender'])
    if new_message.recipient_id:
        await db.refresh(new_message, ['recipient'])

    response = MeetingChatMessageResponse.model_validate(new_message)
    response.sender_name = new_message.sender.full_name
    response.sender_avatar = new_message.sender.avatar_url
    if new_message.recipient:
        response.recipient_name = new_message.recipient.full_name

    return response


# ============================================
# Statistics Endpoint
# ============================================
@router.get("/workspace/{workspace_id}/stats", response_model=MeetingStats)
async def get_meeting_stats(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get meeting statistics for a workspace"""
    # Check workspace membership
    workspace_stmt = select(WorkspaceMember).where(
        and_(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
    )
    workspace_result = await db.execute(workspace_stmt)
    workspace_member = workspace_result.scalar_one_or_none()

    if not workspace_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    # Count total meetings
    total_stmt = select(func.count(Meeting.id)).where(Meeting.workspace_id == workspace_id)
    total_result = await db.execute(total_stmt)
    total_meetings = total_result.scalar() or 0

    # Count active meetings
    active_stmt = select(func.count(Meeting.id)).where(
        and_(
            Meeting.workspace_id == workspace_id,
            Meeting.status == MeetingStatus.IN_PROGRESS
        )
    )
    active_result = await db.execute(active_stmt)
    active_meetings = active_result.scalar() or 0

    # Count participants today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    participants_stmt = select(func.count(MeetingParticipant.id)).select_from(
        MeetingParticipant
    ).join(Meeting).where(
        and_(
            Meeting.workspace_id == workspace_id,
            MeetingParticipant.joined_at >= today_start
        )
    )
    participants_result = await db.execute(participants_stmt)
    total_participants_today = participants_result.scalar() or 0

    # Sum duration today
    duration_stmt = select(func.sum(Meeting.total_duration_seconds)).where(
        and_(
            Meeting.workspace_id == workspace_id,
            Meeting.actual_start_time >= today_start
        )
    )
    duration_result = await db.execute(duration_stmt)
    total_duration_today = duration_result.scalar() or 0

    # Get upcoming meetings
    upcoming_stmt = select(Meeting).where(
        and_(
            Meeting.workspace_id == workspace_id,
            Meeting.status == MeetingStatus.SCHEDULED,
            Meeting.scheduled_start_time > datetime.utcnow()
        )
    ).order_by(Meeting.scheduled_start_time).limit(5)

    upcoming_result = await db.execute(upcoming_stmt)
    upcoming_meetings = upcoming_result.scalars().all()

    upcoming_responses = []
    for meeting in upcoming_meetings:
        upcoming_responses.append(await build_meeting_response(meeting, db))

    return MeetingStats(
        total_meetings=total_meetings,
        active_meetings=active_meetings,
        total_participants_today=total_participants_today,
        total_duration_today_seconds=total_duration_today,
        upcoming_meetings=upcoming_responses
    )

