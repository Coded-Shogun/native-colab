"""
Meeting Schemas
Pydantic schemas for video/audio meetings with WebRTC support
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.models.meeting import (
    MeetingType,
    MeetingStatus,
    ParticipantRole,
    ParticipantStatus,
    RecordingStatus,
)


# ============================================
# Meeting Schemas
# ============================================
class MeetingBase(BaseModel):
    """Base meeting schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    meeting_type: MeetingType = Field(default=MeetingType.INSTANT)
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0, le=1440)  # Max 24 hours


class MeetingCreate(MeetingBase):
    """Schema for creating a meeting"""
    workspace_id: int = Field(..., gt=0)
    project_id: Optional[int] = Field(None, gt=0)
    event_id: Optional[int] = Field(None, gt=0)
    whiteboard_id: Optional[int] = Field(None, gt=0)

    # Meeting room settings
    meeting_passcode: Optional[str] = Field(None, max_length=50)
    waiting_room_enabled: bool = Field(default=True)
    mute_on_join: bool = Field(default=False)
    video_on_join: bool = Field(default=True)
    allow_screen_share: bool = Field(default=True)
    allow_chat: bool = Field(default=True)
    allow_recording: bool = Field(default=True)
    max_participants: int = Field(default=100, gt=0, le=1000)

    # Recording settings
    auto_record: bool = Field(default=False)
    record_audio: bool = Field(default=True)
    record_video: bool = Field(default=True)
    record_screen_share: bool = Field(default=True)

    # Access control
    is_public: bool = Field(default=False)
    require_authentication: bool = Field(default=True)

    # Participants to invite
    participant_user_ids: Optional[List[int]] = Field(default_factory=list)


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0, le=1440)

    # Settings
    meeting_passcode: Optional[str] = Field(None, max_length=50)
    waiting_room_enabled: Optional[bool] = None
    mute_on_join: Optional[bool] = None
    video_on_join: Optional[bool] = None
    allow_screen_share: Optional[bool] = None
    allow_chat: Optional[bool] = None
    allow_recording: Optional[bool] = None
    max_participants: Optional[int] = Field(None, gt=0, le=1000)

    # Access control
    is_public: Optional[bool] = None


class MeetingSettingsUpdate(BaseModel):
    """Schema for updating meeting settings during active meeting"""
    waiting_room_enabled: Optional[bool] = None
    allow_screen_share: Optional[bool] = None
    allow_chat: Optional[bool] = None
    allow_recording: Optional[bool] = None


class MeetingResponse(BaseModel):
    """Schema for meeting response"""
    id: int
    workspace_id: int
    created_by_id: int
    project_id: Optional[int] = None
    event_id: Optional[int] = None
    whiteboard_id: Optional[int] = None

    title: str
    description: Optional[str] = None
    meeting_type: MeetingType
    status: MeetingStatus

    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    meeting_url: Optional[str] = None
    meeting_passcode: Optional[str] = None
    waiting_room_enabled: bool
    mute_on_join: bool
    video_on_join: bool
    allow_screen_share: bool
    allow_chat: bool
    allow_recording: bool
    max_participants: int

    auto_record: bool
    is_recording: bool
    record_audio: bool
    record_video: bool
    record_screen_share: bool

    is_public: bool
    require_authentication: bool

    total_participants: int
    peak_participants: int
    total_duration_seconds: int

    created_at: datetime
    updated_at: datetime

    # Nested info
    creator_name: Optional[str] = None
    creator_email: Optional[str] = None
    active_participant_count: int = 0
    recording_count: int = 0

    model_config = {"from_attributes": True}


class MeetingListResponse(BaseModel):
    """Schema for meeting list response"""
    meetings: List[MeetingResponse]
    total: int


class MeetingJoinResponse(BaseModel):
    """Schema for meeting join response with connection info"""
    meeting: MeetingResponse
    participant: "MeetingParticipantResponse"
    ice_servers: List[Dict[str, Any]] = Field(default_factory=list)  # STUN/TURN servers


# ============================================
# Meeting Participant Schemas
# ============================================
class MeetingParticipantBase(BaseModel):
    """Base meeting participant schema"""
    role: ParticipantRole = Field(default=ParticipantRole.ATTENDEE)
    can_speak: bool = Field(default=True)
    can_share_screen: bool = Field(default=True)
    can_chat: bool = Field(default=True)


class MeetingParticipantInvite(MeetingParticipantBase):
    """Schema for inviting participant to meeting"""
    user_id: Optional[int] = Field(None, gt=0)  # Nullable for guest invites
    guest_name: Optional[str] = Field(None, max_length=255)
    guest_email: Optional[str] = Field(None, max_length=255)


class MeetingParticipantUpdate(BaseModel):
    """Schema for updating participant"""
    role: Optional[ParticipantRole] = None
    can_speak: Optional[bool] = None
    can_share_screen: Optional[bool] = None
    can_chat: Optional[bool] = None


class MeetingParticipantStateUpdate(BaseModel):
    """Schema for updating participant media state during meeting"""
    is_audio_enabled: Optional[bool] = None
    is_video_enabled: Optional[bool] = None
    is_screen_sharing: Optional[bool] = None
    is_hand_raised: Optional[bool] = None


class MeetingParticipantResponse(BaseModel):
    """Schema for meeting participant response"""
    id: int
    meeting_id: int
    user_id: Optional[int] = None
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None

    role: ParticipantRole
    status: ParticipantStatus

    is_audio_enabled: bool
    is_video_enabled: bool
    is_screen_sharing: bool
    is_hand_raised: bool

    connection_id: Optional[str] = None
    peer_id: Optional[str] = None
    connection_quality: Optional[str] = None

    can_speak: bool
    can_share_screen: bool
    can_chat: bool

    invited_at: datetime
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    total_duration_seconds: int

    device_type: Optional[str] = None

    # Nested info
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class MeetingParticipantListResponse(BaseModel):
    """Schema for participant list response"""
    participants: List[MeetingParticipantResponse]
    total: int


# ============================================
# Meeting Recording Schemas
# ============================================
class MeetingRecordingCreate(BaseModel):
    """Schema for starting a recording"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    is_public: bool = Field(default=False)
    password_protected: bool = Field(default=False)
    access_password: Optional[str] = Field(None, max_length=255)


class MeetingRecordingUpdate(BaseModel):
    """Schema for updating a recording"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    is_public: Optional[bool] = None
    is_downloadable: Optional[bool] = None
    password_protected: Optional[bool] = None
    access_password: Optional[str] = Field(None, max_length=255)


class MeetingRecordingResponse(BaseModel):
    """Schema for recording response"""
    id: int
    meeting_id: int
    started_by_id: int

    name: str
    description: Optional[str] = None

    file_size: Optional[int] = None
    duration_seconds: Optional[int] = None
    format: str
    resolution: Optional[str] = None

    storage_path: Optional[str] = None
    thumbnail_path: Optional[str] = None

    status: RecordingStatus
    processing_error: Optional[str] = None

    is_public: bool
    is_downloadable: bool
    password_protected: bool

    has_transcript: bool
    transcript_path: Optional[str] = None

    view_count: int

    recording_started_at: Optional[datetime] = None
    recording_ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Nested info
    started_by_name: Optional[str] = None
    meeting_title: Optional[str] = None

    model_config = {"from_attributes": True}


class MeetingRecordingListResponse(BaseModel):
    """Schema for recording list response"""
    recordings: List[MeetingRecordingResponse]
    total: int


# ============================================
# Meeting Chat Schemas
# ============================================
class MeetingChatMessageCreate(BaseModel):
    """Schema for creating chat message"""
    message: str = Field(..., min_length=1, max_length=5000)
    is_private: bool = Field(default=False)
    recipient_id: Optional[int] = Field(None, gt=0)  # Required if is_private=True


class MeetingChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: int
    meeting_id: int
    sender_id: Optional[int] = None

    message: str
    message_type: str

    is_private: bool
    recipient_id: Optional[int] = None

    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None

    created_at: datetime
    edited_at: Optional[datetime] = None
    is_deleted: bool

    # Nested info
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    recipient_name: Optional[str] = None

    model_config = {"from_attributes": True}


class MeetingChatMessageListResponse(BaseModel):
    """Schema for chat message list response"""
    messages: List[MeetingChatMessageResponse]
    total: int


# ============================================
# WebRTC Signaling Schemas
# ============================================
class WebRTCOffer(BaseModel):
    """Schema for WebRTC offer (SDP)"""
    peer_id: str = Field(..., min_length=1, max_length=100)
    sdp: str = Field(..., min_length=1)
    type: str = Field(default="offer")


class WebRTCAnswer(BaseModel):
    """Schema for WebRTC answer (SDP)"""
    peer_id: str = Field(..., min_length=1, max_length=100)
    sdp: str = Field(..., min_length=1)
    type: str = Field(default="answer")


class WebRTCICECandidate(BaseModel):
    """Schema for WebRTC ICE candidate"""
    peer_id: str = Field(..., min_length=1, max_length=100)
    candidate: str = Field(..., min_length=1)
    sdp_mid: Optional[str] = None
    sdp_m_line_index: Optional[int] = None


# ============================================
# Meeting Statistics
# ============================================
class MeetingStats(BaseModel):
    """Schema for meeting statistics"""
    total_meetings: int
    active_meetings: int
    total_participants_today: int
    total_duration_today_seconds: int
    upcoming_meetings: List[MeetingResponse]
