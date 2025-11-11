"""
Meeting Models
Represents video/audio meetings with WebRTC support, participants, recordings, and chat
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, JSON, BigInteger
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.session import Base


class MeetingType(str, Enum):
    """Meeting type enumeration"""
    INSTANT = "instant"  # Ad-hoc meeting started immediately
    SCHEDULED = "scheduled"  # Scheduled for a specific time
    RECURRING = "recurring"  # Recurring meeting series


class MeetingStatus(str, Enum):
    """Meeting status enumeration"""
    SCHEDULED = "scheduled"  # Meeting is scheduled but not started
    WAITING = "waiting"  # Waiting room active, host not joined
    IN_PROGRESS = "in_progress"  # Meeting is currently active
    ENDED = "ended"  # Meeting has ended normally
    CANCELLED = "cancelled"  # Meeting was cancelled


class ParticipantRole(str, Enum):
    """Meeting participant role enumeration"""
    HOST = "host"  # Meeting host (creator or designated host)
    CO_HOST = "co_host"  # Co-host with elevated permissions
    ATTENDEE = "attendee"  # Regular participant


class ParticipantStatus(str, Enum):
    """Meeting participant status enumeration"""
    INVITED = "invited"  # Invited but not joined
    WAITING = "waiting"  # In waiting room
    JOINED = "joined"  # Currently in meeting
    LEFT = "left"  # Left the meeting
    REMOVED = "removed"  # Removed by host


class RecordingStatus(str, Enum):
    """Meeting recording status enumeration"""
    RECORDING = "recording"  # Currently recording
    PROCESSING = "processing"  # Recording ended, being processed
    READY = "ready"  # Recording ready for playback
    FAILED = "failed"  # Recording processing failed


class Meeting(Base):
    """Meeting model for video/audio conferencing sessions."""
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)  # Link to calendar event
    whiteboard_id = Column(Integer, ForeignKey("whiteboards.id"), nullable=True)  # Optional integrated whiteboard

    # Meeting details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    meeting_type = Column(SQLEnum(MeetingType), default=MeetingType.INSTANT, nullable=False)
    status = Column(SQLEnum(MeetingStatus), default=MeetingStatus.SCHEDULED, nullable=False)

    # Scheduling
    scheduled_start_time = Column(DateTime, nullable=True)
    scheduled_end_time = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Planned duration

    # Meeting room settings
    meeting_url = Column(String(500), nullable=True)  # Unique meeting room URL
    meeting_passcode = Column(String(50), nullable=True)  # Optional passcode
    waiting_room_enabled = Column(Boolean, default=True, nullable=False)
    mute_on_join = Column(Boolean, default=False, nullable=False)
    video_on_join = Column(Boolean, default=True, nullable=False)
    allow_screen_share = Column(Boolean, default=True, nullable=False)
    allow_chat = Column(Boolean, default=True, nullable=False)
    allow_recording = Column(Boolean, default=True, nullable=False)
    max_participants = Column(Integer, default=100, nullable=False)

    # Recording settings
    auto_record = Column(Boolean, default=False, nullable=False)
    is_recording = Column(Boolean, default=False, nullable=False)
    record_audio = Column(Boolean, default=True, nullable=False)
    record_video = Column(Boolean, default=True, nullable=False)
    record_screen_share = Column(Boolean, default=True, nullable=False)

    # Access control
    is_public = Column(Boolean, default=False, nullable=False)  # Public within workspace
    require_authentication = Column(Boolean, default=True, nullable=False)

    # Meeting metadata
    total_participants = Column(Integer, default=0, nullable=False)
    peak_participants = Column(Integer, default=0, nullable=False)
    total_duration_seconds = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", backref="meetings")
    created_by = relationship("User", backref="meetings_created")
    project = relationship("Project", backref="meetings")
    event = relationship("Event", backref="meeting")
    whiteboard = relationship("Whiteboard", backref="meeting")
    participants = relationship("MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan")
    recordings = relationship("MeetingRecording", back_populates="meeting", cascade="all, delete-orphan")
    chat_messages = relationship("MeetingChatMessage", back_populates="meeting", cascade="all, delete-orphan")


class MeetingParticipant(Base):
    """Meeting participant model tracking who joins meetings and their state."""
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for guest participants

    # Participant info (for guests)
    guest_name = Column(String(255), nullable=True)
    guest_email = Column(String(255), nullable=True)

    # Role and status
    role = Column(SQLEnum(ParticipantRole), default=ParticipantRole.ATTENDEE, nullable=False)
    status = Column(SQLEnum(ParticipantStatus), default=ParticipantStatus.INVITED, nullable=False)

    # Media state (current state in meeting)
    is_audio_enabled = Column(Boolean, default=True, nullable=False)
    is_video_enabled = Column(Boolean, default=True, nullable=False)
    is_screen_sharing = Column(Boolean, default=False, nullable=False)
    is_hand_raised = Column(Boolean, default=False, nullable=False)

    # Connection info for WebRTC
    connection_id = Column(String(100), nullable=True)  # Socket.io connection ID
    peer_id = Column(String(100), nullable=True)  # WebRTC peer ID
    connection_quality = Column(String(20), nullable=True)  # good, fair, poor

    # Permissions
    can_speak = Column(Boolean, default=True, nullable=False)
    can_share_screen = Column(Boolean, default=True, nullable=False)
    can_chat = Column(Boolean, default=True, nullable=False)

    # Timestamps
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    total_duration_seconds = Column(Integer, default=0, nullable=False)

    # IP and device info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet

    # Relationships
    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", backref="meeting_participations")


class MeetingRecording(Base):
    """Meeting recording model for storing meeting recordings."""
    __tablename__ = "meeting_recordings"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    started_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Recording details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Recording metadata
    file_size = Column(BigInteger, nullable=True)  # Size in bytes
    duration_seconds = Column(Integer, nullable=True)
    format = Column(String(50), default="webm", nullable=False)  # webm, mp4, etc.
    resolution = Column(String(20), nullable=True)  # 1920x1080, 1280x720, etc.

    # Storage
    storage_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)

    # Processing
    status = Column(SQLEnum(RecordingStatus), default=RecordingStatus.RECORDING, nullable=False)
    processing_error = Column(Text, nullable=True)

    # Access control
    is_public = Column(Boolean, default=False, nullable=False)  # Public within workspace
    is_downloadable = Column(Boolean, default=True, nullable=False)
    password_protected = Column(Boolean, default=False, nullable=False)
    access_password = Column(String(255), nullable=True)

    # Transcript
    has_transcript = Column(Boolean, default=False, nullable=False)
    transcript_path = Column(String(500), nullable=True)

    # Statistics
    view_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    recording_started_at = Column(DateTime, nullable=True)
    recording_ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="recordings")
    started_by = relationship("User", backref="meeting_recordings_started")


class MeetingChatMessage(Base):
    """Meeting chat message model for in-meeting chat."""
    __tablename__ = "meeting_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for guest senders

    # Message content
    message = Column(Text, nullable=False)
    message_type = Column(String(50), default="text", nullable=False)  # text, file, emoji_reaction

    # Message metadata
    is_private = Column(Boolean, default=False, nullable=False)  # Private message to specific participant
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # For private messages

    # Attachments
    attachment_url = Column(String(500), nullable=True)
    attachment_name = Column(String(255), nullable=True)
    attachment_size = Column(BigInteger, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    edited_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="chat_messages")
    sender = relationship("User", foreign_keys=[sender_id], backref="meeting_messages_sent")
    recipient = relationship("User", foreign_keys=[recipient_id], backref="meeting_messages_received")
