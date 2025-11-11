"""
Notification Models
Represents notifications, user preferences, and notification delivery
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.session import Base


class NotificationType(str, Enum):
    """Notification type enumeration"""
    # Calendar notifications
    EVENT_REMINDER = "event_reminder"
    EVENT_INVITATION = "event_invitation"
    EVENT_UPDATE = "event_update"
    EVENT_CANCELLED = "event_cancelled"
    RSVP_UPDATE = "rsvp_update"

    # Chat notifications
    DIRECT_MESSAGE = "direct_message"
    CHANNEL_MESSAGE = "channel_message"
    CHANNEL_MENTION = "channel_mention"

    # Task notifications
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    TASK_COMMENT = "task_comment"
    TASK_DUE_SOON = "task_due_soon"
    TASK_OVERDUE = "task_overdue"

    # Project notifications
    PROJECT_INVITATION = "project_invitation"
    PROJECT_UPDATE = "project_update"

    # Workspace notifications
    WORKSPACE_INVITATION = "workspace_invitation"
    TEAM_INVITATION = "team_invitation"

    # System notifications
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    SYSTEM_ALERT = "system_alert"


class NotificationChannel(str, Enum):
    """Notification delivery channel enumeration"""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"


class NotificationPriority(str, Enum):
    """Notification priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """Notification model for user notifications."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False)

    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)

    # Related entities (nullable, depending on notification type)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional context data

    # Delivery tracking
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    # Delivery channels
    sent_in_app = Column(Boolean, default=False, nullable=False)
    sent_email = Column(Boolean, default=False, nullable=False)
    sent_push = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="notifications")
    event = relationship("Event", backref="notifications", foreign_keys=[event_id])
    message = relationship("Message", backref="notifications", foreign_keys=[message_id])
    task = relationship("Task", backref="notifications", foreign_keys=[task_id])
    project = relationship("Project", backref="notifications", foreign_keys=[project_id])
    workspace = relationship("Workspace", backref="notifications", foreign_keys=[workspace_id])


class NotificationPreference(Base):
    """User notification preferences for different notification types and channels."""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)

    # Channel preferences
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=False, nullable=False)

    # Delivery settings
    quiet_hours_start = Column(Integer, nullable=True)  # Hour 0-23
    quiet_hours_end = Column(Integer, nullable=True)    # Hour 0-23

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="notification_preferences")
