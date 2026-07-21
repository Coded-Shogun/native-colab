"""
Webhook Models
Database models for webhook functionality and integrations
"""

from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ============================================
# Enums
# ============================================
class WebhookEventType(str, enum.Enum):
    """Events that can trigger webhooks"""
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

    # Workspace events
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_MEMBER_ADDED = "workspace.member_added"
    WORKSPACE_MEMBER_REMOVED = "workspace.member_removed"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    PROJECT_COMPLETED = "project.completed"

    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_COMMENT_ADDED = "task.comment_added"

    # Document events
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_SHARED = "document.shared"
    DOCUMENT_COMMENT_ADDED = "document.comment_added"

    # Message events
    MESSAGE_CREATED = "message.created"
    MESSAGE_UPDATED = "message.updated"
    MESSAGE_DELETED = "message.deleted"
    DIRECT_MESSAGE_CREATED = "direct_message.created"

    # Calendar events
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"
    EVENT_RSVP_UPDATED = "event.rsvp_updated"

    # Meeting events
    MEETING_CREATED = "meeting.created"
    MEETING_STARTED = "meeting.started"
    MEETING_ENDED = "meeting.ended"
    MEETING_RECORDING_AVAILABLE = "meeting.recording_available"

    # Whiteboard events
    WHITEBOARD_CREATED = "whiteboard.created"
    WHITEBOARD_UPDATED = "whiteboard.updated"
    WHITEBOARD_SHARED = "whiteboard.shared"

    # Signature events
    SIGNATURE_REQUEST_CREATED = "signature_request.created"
    SIGNATURE_REQUEST_COMPLETED = "signature_request.completed"
    SIGNATURE_ADDED = "signature.added"

    # Time tracking events
    TIME_ENTRY_CREATED = "time_entry.created"
    TIME_ENTRY_UPDATED = "time_entry.updated"


class WebhookStatus(str, enum.Enum):
    """Webhook status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"  # Too many failures
    DISABLED = "disabled"  # Manually disabled


class DeliveryStatus(str, enum.Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class IntegrationType(str, enum.Enum):
    """Types of integrations"""
    SLACK = "slack"
    GITHUB = "github"
    GOOGLE_CALENDAR = "google_calendar"
    MICROSOFT_TEAMS = "microsoft_teams"
    JIRA = "jira"
    TRELLO = "trello"
    ZAPIER = "zapier"
    CUSTOM = "custom"


class IntegrationStatus(str, enum.Enum):
    """Integration connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EXPIRED = "expired"  # Token expired


# ============================================
# Webhook Model
# ============================================
class Webhook(Base):
    """
    Webhook configuration for sending events to external URLs
    """
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Ownership
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    organization_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )

    # Webhook details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # Authentication
    secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Secret for HMAC signature verification"
    )
    headers: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Custom headers to send with webhook"
    )

    # Event subscription
    events: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="List of event types this webhook subscribes to"
    )

    # Filters
    filters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Additional filters for events (e.g., project_id, user_id)"
    )

    # Status and settings
    status: Mapped[WebhookStatus] = mapped_column(
        SQLEnum(WebhookStatus, name="webhookstatus"),
        nullable=False,
        default=WebhookStatus.ACTIVE,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Retry configuration
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="Maximum delivery retry attempts"
    )
    retry_delay: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        comment="Delay between retries in seconds"
    )

    # Statistics
    total_deliveries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    successful_deliveries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    failed_deliveries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    last_delivery_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="webhooks")
    creator: Mapped["User"] = relationship("User", back_populates="webhooks")
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery",
        back_populates="webhook",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_webhooks_workspace_status", "workspace_id", "status"),
    )

    def __repr__(self):
        return f"<Webhook {self.id} '{self.name}' - {self.status}>"


# ============================================
# Webhook Delivery Model
# ============================================
class WebhookDelivery(Base):
    """
    Track webhook delivery attempts and responses
    """
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Webhook reference
    webhook_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Event details
    event_type: Mapped[WebhookEventType] = mapped_column(
        SQLEnum(WebhookEventType, name="webhookeventtype"),
        nullable=False,
        index=True
    )
    event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Unique identifier for this event"
    )

    # Payload
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Event payload sent to webhook"
    )

    # Request details
    request_url: Mapped[str] = mapped_column(Text, nullable=False)
    request_method: Mapped[str] = mapped_column(
        String(10),
        default="POST",
        nullable=False
    )
    request_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    request_signature: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="HMAC signature of payload"
    )

    # Response details
    response_status_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    response_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Response time in milliseconds"
    )

    # Delivery status
    status: Mapped[DeliveryStatus] = mapped_column(
        SQLEnum(DeliveryStatus, name="deliverystatus"),
        nullable=False,
        default=DeliveryStatus.PENDING,
        index=True
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of delivery attempts"
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False
    )

    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="When to retry if failed"
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When successfully delivered"
    )

    # Relationships
    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="deliveries")

    __table_args__ = (
        Index("ix_webhook_deliveries_webhook_status", "webhook_id", "status"),
        Index("ix_webhook_deliveries_event", "event_type", "event_id"),
    )

    def __repr__(self):
        return f"<WebhookDelivery {self.id} webhook={self.webhook_id} {self.status}>"


# ============================================
# Integration Model
# ============================================
class Integration(Base):
    """
    Third-party integration configuration
    """
    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Integration details
    type: Mapped[IntegrationType] = mapped_column(
        SQLEnum(IntegrationType, name="integrationtype"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # OAuth configuration
    client_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    client_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    authorization_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scopes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    # API configuration
    api_base_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Settings
    settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Integration-specific settings"
    )

    # Status
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_oauth: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this integration uses OAuth"
    )

    # System integration (not user-created)
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    connections: Mapped[list["IntegrationConnection"]] = relationship(
        "IntegrationConnection",
        back_populates="integration",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Integration {self.id} {self.type} '{self.name}'>"


# ============================================
# Integration Connection Model
# ============================================
class IntegrationConnection(Base):
    """
    User/Workspace connection to a third-party integration
    """
    __tablename__ = "integration_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Integration reference
    integration_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Ownership
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    organization_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )

    # Connection details
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User-provided name for this connection"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # OAuth tokens
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Additional credentials (for non-OAuth)
    credentials: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="API keys, tokens, etc."
    )

    # Connection settings
    settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Connection-specific settings"
    )

    # External identifiers
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="External user/team ID"
    )
    external_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="External user/team data"
    )

    # Status
    status: Mapped[IntegrationStatus] = mapped_column(
        SQLEnum(IntegrationStatus, name="integrationstatus"),
        nullable=False,
        default=IntegrationStatus.CONNECTED,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Statistics
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_syncs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_syncs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error tracking
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration",
        back_populates="connections"
    )
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="integration_connections"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="integration_connections"
    )

    __table_args__ = (
        Index(
            "ix_integration_connections_workspace_integration",
            "workspace_id",
            "integration_id"
        ),
        Index(
            "ix_integration_connections_user_integration",
            "user_id",
            "integration_id"
        ),
    )

    def __repr__(self):
        return f"<IntegrationConnection {self.id} user={self.user_id} {self.status}>"
