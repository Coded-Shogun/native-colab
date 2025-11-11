"""
Calendar Schemas
Pydantic schemas for calendars, events, attendees, and reminders
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.db.models.calendar import EventType, EventVisibility, RSVPStatus, ReminderType


# ============================================
# Calendar Schemas
# ============================================
class CalendarBase(BaseModel):
    """Base calendar schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")
    timezone: str = Field(default="UTC", max_length=50)
    is_public: bool = Field(default=False)


class CalendarCreate(CalendarBase):
    """Schema for creating a calendar"""
    workspace_id: Optional[int] = Field(None, gt=0)
    is_default: bool = Field(default=False)


class CalendarUpdate(BaseModel):
    """Schema for updating a calendar"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    timezone: Optional[str] = Field(None, max_length=50)
    is_public: Optional[bool] = None


class CalendarResponse(BaseModel):
    """Schema for calendar response"""
    id: int
    name: str
    description: Optional[str] = None
    color: str
    timezone: str
    owner_id: Optional[int] = None
    workspace_id: Optional[int] = None
    is_default: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime

    # Nested owner info
    owner_email: Optional[str] = None
    owner_name: Optional[str] = None

    # Statistics
    event_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class CalendarListResponse(BaseModel):
    """Schema for calendar list response"""
    calendars: List[CalendarResponse]
    total: int


# ============================================
# Event Schemas
# ============================================
class EventBase(BaseModel):
    """Base event schema"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    location: Optional[str] = Field(None, max_length=500)
    event_type: EventType = Field(default=EventType.MEETING)
    visibility: EventVisibility = Field(default=EventVisibility.WORKSPACE)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class EventCreate(EventBase):
    """Schema for creating an event"""
    calendar_id: int = Field(..., gt=0)
    project_id: Optional[int] = Field(None, gt=0)
    task_id: Optional[int] = Field(None, gt=0)
    start_time: datetime
    end_time: datetime
    is_all_day: bool = Field(default=False)
    timezone: str = Field(default="UTC", max_length=50)
    recurrence_rule: Optional[str] = Field(None, max_length=500)
    attendee_ids: Optional[List[int]] = Field(default_factory=list)

    @field_validator('end_time')
    @classmethod
    def validate_end_after_start(cls, v: datetime, info) -> datetime:
        """Validate that end_time is after start_time"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v


class EventUpdate(BaseModel):
    """Schema for updating an event"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    location: Optional[str] = Field(None, max_length=500)
    event_type: Optional[EventType] = None
    visibility: Optional[EventVisibility] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    timezone: Optional[str] = Field(None, max_length=50)
    recurrence_rule: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class EventAttendeeInfo(BaseModel):
    """Schema for event attendee information"""
    id: int
    user_id: int
    rsvp_status: RSVPStatus
    is_organizer: bool
    is_optional: bool
    comment: Optional[str] = None
    responded_at: Optional[datetime] = None

    # Nested user info
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class EventReminderInfo(BaseModel):
    """Schema for event reminder information"""
    id: int
    reminder_type: ReminderType
    minutes_before: int
    is_sent: bool
    sent_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    """Schema for event response"""
    id: int
    calendar_id: int
    created_by_id: int
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    event_type: EventType
    visibility: EventVisibility
    start_time: datetime
    end_time: datetime
    is_all_day: bool
    timezone: str
    recurrence_rule: Optional[str] = None
    color: Optional[str] = None
    is_cancelled: bool
    created_at: datetime
    updated_at: datetime

    # Nested creator info
    creator_email: Optional[str] = None
    creator_name: Optional[str] = None

    # Nested calendar info
    calendar_name: Optional[str] = None
    calendar_color: Optional[str] = None

    # Attendees and reminders
    attendees: Optional[List[EventAttendeeInfo]] = []
    attendee_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    """Schema for event list response"""
    events: List[EventResponse]
    total: int


# ============================================
# Event Attendee Schemas
# ============================================
class EventAttendeeAdd(BaseModel):
    """Schema for adding an attendee to an event"""
    user_id: int = Field(..., gt=0)
    is_optional: bool = Field(default=False)


class EventAttendeeUpdate(BaseModel):
    """Schema for updating an attendee"""
    is_optional: Optional[bool] = None


class RSVPUpdate(BaseModel):
    """Schema for updating RSVP status"""
    rsvp_status: RSVPStatus
    comment: Optional[str] = Field(None, max_length=1000)


# ============================================
# Event Reminder Schemas
# ============================================
class EventReminderCreate(BaseModel):
    """Schema for creating an event reminder"""
    event_id: int = Field(..., gt=0)
    reminder_type: ReminderType = Field(default=ReminderType.EMAIL)
    minutes_before: int = Field(..., ge=0, le=43200)  # Max 30 days


class EventReminderResponse(BaseModel):
    """Schema for event reminder response"""
    id: int
    event_id: int
    user_id: int
    reminder_type: ReminderType
    minutes_before: int
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# Search and Filter Schemas
# ============================================
class EventSearchFilters(BaseModel):
    """Schema for event search filters"""
    calendar_ids: Optional[List[int]] = Field(None, description="Filter by calendar IDs")
    event_type: Optional[EventType] = None
    visibility: Optional[EventVisibility] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_query: Optional[str] = Field(None, max_length=200)
    include_cancelled: bool = Field(default=False)
    project_id: Optional[int] = Field(None, gt=0)
    task_id: Optional[int] = Field(None, gt=0)
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)


class AvailabilityQuery(BaseModel):
    """Schema for checking user availability"""
    user_ids: List[int] = Field(..., min_length=1, max_length=20)
    start_time: datetime
    end_time: datetime
    timezone: str = Field(default="UTC", max_length=50)

    @field_validator('end_time')
    @classmethod
    def validate_end_after_start(cls, v: datetime, info) -> datetime:
        """Validate that end_time is after start_time"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v


class UserAvailability(BaseModel):
    """Schema for user availability response"""
    user_id: int
    user_email: str
    user_name: str
    is_available: bool
    busy_times: List[dict] = []  # List of {start_time, end_time, event_title}


class AvailabilityResponse(BaseModel):
    """Schema for availability check response"""
    query_start: datetime
    query_end: datetime
    timezone: str
    users: List[UserAvailability]


# ============================================
# Calendar Sharing Schemas
# ============================================
class CalendarShareCreate(BaseModel):
    """Schema for sharing a calendar"""
    user_id: int = Field(..., gt=0)
    can_edit: bool = Field(default=False)


class CalendarShareResponse(BaseModel):
    """Schema for calendar share response"""
    calendar_id: int
    user_id: int
    user_email: str
    user_name: str
    can_edit: bool
    shared_at: datetime
