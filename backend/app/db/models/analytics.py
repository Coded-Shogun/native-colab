"""
Analytics Models
Database models for analytics tracking and reporting
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
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ============================================
# Enums
# ============================================
class AnalyticsEventType(str, enum.Enum):
    """Types of analytics events to track"""
    # User activity
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_ACTIVE = "user_active"

    # Feature usage
    FEATURE_USED = "feature_used"
    PAGE_VIEW = "page_view"

    # Content creation
    CONTENT_CREATED = "content_created"
    CONTENT_UPDATED = "content_updated"
    CONTENT_DELETED = "content_deleted"

    # Collaboration
    COLLABORATION_SESSION = "collaboration_session"
    MESSAGE_SENT = "message_sent"

    # File operations
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"

    # Search
    SEARCH_PERFORMED = "search_performed"

    # Integration
    WEBHOOK_DELIVERED = "webhook_delivered"
    INTEGRATION_SYNC = "integration_sync"


class ReportType(str, enum.Enum):
    """Types of reports"""
    USAGE_SUMMARY = "usage_summary"
    TIME_TRACKING = "time_tracking"
    PROJECT_PROGRESS = "project_progress"
    USER_ACTIVITY = "user_activity"
    WORKSPACE_ANALYTICS = "workspace_analytics"
    CUSTOM = "custom"


class ReportStatus(str, enum.Enum):
    """Report generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportFormat(str, enum.Enum):
    """Report output formats"""
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class ExportStatus(str, enum.Enum):
    """Export job status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================
# Analytics Event Model
# ============================================
class AnalyticsEvent(Base):
    """
    Track user actions and system events for analytics
    """
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Event details
    event_type: Mapped[AnalyticsEventType] = mapped_column(
        SQLEnum(AnalyticsEventType, name="analyticseventtype"),
        nullable=False,
        index=True
    )
    event_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    # Context
    workspace_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Event data
    properties: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Event-specific properties"
    )

    # Session tracking
    session_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    # Device/location
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    browser: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Performance metrics
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Event duration in milliseconds"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # Relationships
    workspace: Mapped[Optional["Workspace"]] = relationship("Workspace", back_populates="analytics_events")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="analytics_events")

    __table_args__ = (
        Index("ix_analytics_events_workspace_type", "workspace_id", "event_type"),
        Index("ix_analytics_events_user_type", "user_id", "event_type"),
        Index("ix_analytics_events_created_type", "created_at", "event_type"),
    )

    def __repr__(self):
        return f"<AnalyticsEvent {self.event_type} user={self.user_id}>"


# ============================================
# Report Model
# ============================================
class Report(Base):
    """
    Saved and scheduled reports
    """
    __tablename__ = "reports"

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

    # Report details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType, name="reporttype"),
        nullable=False,
        index=True
    )

    # Configuration
    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Report configuration (filters, date range, etc.)"
    )
    format: Mapped[ReportFormat] = mapped_column(
        SQLEnum(ReportFormat, name="reportformat"),
        nullable=False,
        default=ReportFormat.PDF
    )

    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    schedule_cron: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Cron expression for scheduled reports"
    )

    # Recipients
    recipients: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="Email addresses to send report to"
    )

    # Generation
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, name="reportstatus"),
        nullable=False,
        default=ReportStatus.PENDING,
        index=True
    )
    file_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="URL to generated report file"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes"
    )

    # Statistics
    generation_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last time scheduled report was run"
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="reports")
    creator: Mapped["User"] = relationship("User", back_populates="reports")

    __table_args__ = (
        Index("ix_reports_workspace_type", "workspace_id", "type"),
    )

    def __repr__(self):
        return f"<Report {self.id} '{self.name}' {self.type}>"


# ============================================
# Export Job Model
# ============================================
class ExportJob(Base):
    """
    Track data export operations
    """
    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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

    # Export details
    export_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of data being exported (tasks, time_entries, etc.)"
    )
    format: Mapped[ReportFormat] = mapped_column(
        SQLEnum(ReportFormat, name="reportformat"),
        nullable=False
    )

    # Filters
    filters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Export filters (date range, projects, etc.)"
    )

    # Status
    status: Mapped[ExportStatus] = mapped_column(
        SQLEnum(ExportStatus, name="exportstatus"),
        nullable=False,
        default=ExportStatus.QUEUED,
        index=True
    )

    # Results
    file_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="URL to exported file"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes"
    )
    rows_exported: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of rows exported"
    )

    # Performance
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When the export file expires and will be deleted"
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="export_jobs")
    user: Mapped["User"] = relationship("User", back_populates="export_jobs")

    __table_args__ = (
        Index("ix_export_jobs_workspace_status", "workspace_id", "status"),
    )

    def __repr__(self):
        return f"<ExportJob {self.id} {self.export_type} {self.status}>"


# ============================================
# Workspace Metrics Snapshot Model
# ============================================
class WorkspaceMetrics(Base):
    """
    Daily snapshots of workspace metrics for historical tracking
    """
    __tablename__ = "workspace_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Date of metrics
    date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        comment="Date these metrics represent"
    )

    # User metrics
    total_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_users: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Users active on this date"
    )
    new_users: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="New users added on this date"
    )

    # Content metrics
    total_projects: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_messages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Activity metrics
    messages_sent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Messages sent on this date"
    )
    tasks_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_uploaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meetings_held: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Time tracking
    total_time_tracked_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total time tracked on this date in seconds"
    )

    # Storage
    storage_used_bytes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total storage used in bytes"
    )

    # Engagement score (0-100)
    engagement_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Calculated engagement score for this date"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="metrics")

    __table_args__ = (
        Index("ix_workspace_metrics_workspace_date", "workspace_id", "date", unique=True),
    )

    def __repr__(self):
        return f"<WorkspaceMetrics workspace={self.workspace_id} date={self.date.date()}>"
