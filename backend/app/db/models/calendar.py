"""
Calendar Models
Represents calendars, events, attendees, and reminders for scheduling
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.session import Base


class EventType(str, Enum):
    """Event type enumeration"""
    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    DEADLINE = "deadline"
    OTHER = "other"


class EventVisibility(str, Enum):
    """Event visibility enumeration"""
    PUBLIC = "public"
    PRIVATE = "private"
    WORKSPACE = "workspace"


class RSVPStatus(str, Enum):
    """RSVP status enumeration"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    MAYBE = "maybe"


class ReminderType(str, Enum):
    """Reminder type enumeration"""
    EMAIL = "email"
    PUSH = "push"
    BOTH = "both"


class Calendar(Base):
    """
    Calendar model for organizing events.

    Can be personal (user-owned) or workspace-level (shared).

    Attributes:
        id: Primary key
        name: Calendar name
        description: Calendar description
        color: Display color (hex code)
        owner_id: Foreign key to User (for personal calendars)
        workspace_id: Foreign key to Workspace (for workspace calendars)
        is_default: Whether this is the user's default calendar
        is_public: Whether calendar is publicly visible
        timezone: Calendar timezone (IANA format, e.g., "America/New_York")
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "calendars"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)

    # Calendar Info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#3B82F6", nullable=False)  # Hex color
    timezone = Column(String(50), default="UTC", nullable=False)

    # Flags
    is_default = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", backref="calendars")
    workspace = relationship("Workspace", backref="calendars")
    events = relationship("Event", back_populates="calendar", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Calendar(id={self.id}, name={self.name})>"


class Event(Base):
    """
    Event model for calendar events.

    Supports meetings, tasks, reminders, and recurring events.

    Attributes:
        id: Primary key
        calendar_id: Foreign key to Calendar
        created_by_id: Foreign key to User who created the event
        project_id: Optional foreign key to Project
        task_id: Optional foreign key to Task
        title: Event title
        description: Event description
        location: Event location (physical or virtual)
        event_type: Type of event (meeting, task, etc.)
        visibility: Event visibility (public, private, workspace)
        start_time: Event start time
        end_time: Event end time
        is_all_day: Whether event is all-day
        timezone: Event timezone
        recurrence_rule: Recurrence pattern (iCalendar RRULE format or JSON)
        color: Display color override
        is_cancelled: Whether event is cancelled
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "events"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    # Event Info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    event_type = Column(SQLEnum(EventType), default=EventType.MEETING, nullable=False)
    visibility = Column(SQLEnum(EventVisibility), default=EventVisibility.WORKSPACE, nullable=False)

    # Time Info
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_all_day = Column(Boolean, default=False, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Recurrence (iCalendar RRULE format or simplified JSON)
    recurrence_rule = Column(Text, nullable=True)

    # Display
    color = Column(String(7), nullable=True)  # Hex color override

    # Flags
    is_cancelled = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    calendar = relationship("Calendar", back_populates="events")
    creator = relationship("User", foreign_keys=[created_by_id], backref="created_events")
    project = relationship("Project", backref="events")
    task = relationship("Task", backref="events")
    attendees = relationship("EventAttendee", back_populates="event", cascade="all, delete-orphan")
    reminders = relationship("EventReminder", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title})>"


class EventAttendee(Base):
    """
    Event attendee model for tracking invitations and RSVP status.

    Tracks who is invited to an event and their response.

    Attributes:
        id: Primary key
        event_id: Foreign key to Event
        user_id: Foreign key to User
        rsvp_status: RSVP response status
        is_organizer: Whether user is the event organizer
        is_optional: Whether attendance is optional
        comment: Attendee comment/note
        responded_at: When attendee responded
        created_at: Timestamp of invitation
        updated_at: Timestamp of last update
    """

    __tablename__ = "event_attendees"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # RSVP Info
    rsvp_status = Column(SQLEnum(RSVPStatus), default=RSVPStatus.PENDING, nullable=False)
    is_organizer = Column(Boolean, default=False, nullable=False)
    is_optional = Column(Boolean, default=False, nullable=False)
    comment = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="attendees")
    user = relationship("User", backref="event_attendees")

    def __repr__(self):
        return f"<EventAttendee(event_id={self.event_id}, user_id={self.user_id}, status={self.rsvp_status})>"


class EventReminder(Base):
    """
    Event reminder model for notifications.

    Tracks reminders for events (email, push, etc.).

    Attributes:
        id: Primary key
        event_id: Foreign key to Event
        user_id: Foreign key to User
        reminder_type: Type of reminder (email, push, both)
        minutes_before: Minutes before event to send reminder
        is_sent: Whether reminder has been sent
        sent_at: When reminder was sent
        created_at: Timestamp of creation
    """

    __tablename__ = "event_reminders"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Reminder Info
    reminder_type = Column(SQLEnum(ReminderType), default=ReminderType.EMAIL, nullable=False)
    minutes_before = Column(Integer, nullable=False)  # Minutes before event

    # Status
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="reminders")
    user = relationship("User", backref="event_reminders")

    def __repr__(self):
        return f"<EventReminder(event_id={self.event_id}, minutes_before={self.minutes_before})>"
