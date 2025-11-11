"""
Analytics Schemas
Pydantic schemas for analytics, reporting, and data export
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.models.analytics import (
    AnalyticsEventType,
    ReportType,
    ReportStatus,
    ReportFormat,
    ExportStatus,
)


# ============================================
# Analytics Event Schemas
# ============================================
class AnalyticsEventCreate(BaseModel):
    """Schema for creating an analytics event"""
    event_type: AnalyticsEventType
    event_name: str = Field(..., max_length=255)
    properties: Optional[Dict[str, Any]] = Field(default=None)
    session_id: Optional[str] = Field(None, max_length=255)
    duration_ms: Optional[int] = Field(None, ge=0)


class AnalyticsEventResponse(BaseModel):
    """Schema for analytics event response"""
    id: int
    event_type: AnalyticsEventType
    event_name: str
    workspace_id: Optional[int] = None
    user_id: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# Analytics Query Schemas
# ============================================
class AnalyticsDateRange(BaseModel):
    """Date range for analytics queries"""
    start_date: datetime
    end_date: datetime


class UsageAnalyticsRequest(BaseModel):
    """Request for usage analytics"""
    workspace_id: int = Field(..., gt=0)
    date_range: AnalyticsDateRange
    group_by: Optional[str] = Field(default="day", description="day, week, month")


class UserActivityMetrics(BaseModel):
    """User activity metrics"""
    total_users: int
    active_users: int
    new_users: int
    daily_active_users: Optional[int] = None
    weekly_active_users: Optional[int] = None
    monthly_active_users: Optional[int] = None


class ContentMetrics(BaseModel):
    """Content creation metrics"""
    total_projects: int
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    total_documents: int
    total_messages: int
    messages_per_day: float


class TimeTrackingMetrics(BaseModel):
    """Time tracking metrics"""
    total_time_seconds: int
    total_time_hours: float
    billable_time_seconds: int
    billable_time_hours: float
    average_daily_hours: float
    top_projects: List[Dict[str, Any]]


class WorkspaceAnalyticsResponse(BaseModel):
    """Comprehensive workspace analytics"""
    workspace_id: int
    date_range: AnalyticsDateRange
    user_metrics: UserActivityMetrics
    content_metrics: ContentMetrics
    time_tracking_metrics: TimeTrackingMetrics
    engagement_score: Optional[float] = None
    storage_used_bytes: int
    storage_used_mb: float


# ============================================
# Project Analytics Schemas
# ============================================
class ProjectProgressMetrics(BaseModel):
    """Project progress metrics"""
    project_id: int
    project_name: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    todo_tasks: int
    completion_percentage: float
    overdue_tasks: int
    total_time_tracked_hours: float
    team_size: int


class BurndownData(BaseModel):
    """Burndown chart data point"""
    date: date
    remaining_tasks: int
    completed_tasks: int
    ideal_remaining: Optional[int] = None


class VelocityData(BaseModel):
    """Sprint velocity data"""
    period: str
    completed_tasks: int
    completed_story_points: Optional[int] = None


class ProjectAnalyticsResponse(BaseModel):
    """Project analytics response"""
    project_id: int
    metrics: ProjectProgressMetrics
    burndown_data: List[BurndownData]
    velocity_data: List[VelocityData]
    task_distribution: Dict[str, int]
    time_by_member: List[Dict[str, Any]]


# ============================================
# Time Tracking Report Schemas
# ============================================
class TimeTrackingReportRequest(BaseModel):
    """Request for time tracking report"""
    workspace_id: int = Field(..., gt=0)
    date_range: AnalyticsDateRange
    project_id: Optional[int] = Field(None, gt=0)
    user_id: Optional[int] = Field(None, gt=0)
    group_by: str = Field(default="user", description="user, project, date")


class TimeEntryDetail(BaseModel):
    """Detailed time entry"""
    id: int
    user_name: str
    project_name: Optional[str] = None
    task_title: Optional[str] = None
    description: Optional[str] = None
    duration_seconds: int
    duration_hours: float
    is_billable: bool
    date: date


class TimeTrackingReportResponse(BaseModel):
    """Time tracking report response"""
    workspace_id: int
    date_range: AnalyticsDateRange
    total_hours: float
    billable_hours: float
    entries: List[TimeEntryDetail]
    summary_by_user: Optional[Dict[str, float]] = None
    summary_by_project: Optional[Dict[str, float]] = None


# ============================================
# Report Management Schemas
# ============================================
class ReportCreate(BaseModel):
    """Schema for creating a report"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    type: ReportType
    config: Dict[str, Any] = Field(..., description="Report configuration")
    format: ReportFormat = Field(default=ReportFormat.PDF)
    is_scheduled: bool = Field(default=False)
    schedule_cron: Optional[str] = Field(None, max_length=100)
    recipients: Optional[List[str]] = Field(default=None)


class ReportUpdate(BaseModel):
    """Schema for updating a report"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    config: Optional[Dict[str, Any]] = None
    format: Optional[ReportFormat] = None
    is_scheduled: Optional[bool] = None
    schedule_cron: Optional[str] = Field(None, max_length=100)
    recipients: Optional[List[str]] = None


class ReportResponse(BaseModel):
    """Schema for report response"""
    id: int
    workspace_id: int
    created_by: int
    name: str
    description: Optional[str] = None
    type: ReportType
    config: Dict[str, Any]
    format: ReportFormat
    is_scheduled: bool
    schedule_cron: Optional[str] = None
    recipients: Optional[List[str]] = None
    status: ReportStatus
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    generation_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    generated_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """Schema for report list response"""
    reports: List[ReportResponse]
    total: int


class ReportGenerateRequest(BaseModel):
    """Request to generate a report"""
    report_id: int = Field(..., gt=0)
    override_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Override report config for this generation"
    )


# ============================================
# Export Job Schemas
# ============================================
class ExportRequest(BaseModel):
    """Request for data export"""
    export_type: str = Field(
        ...,
        max_length=100,
        description="Type of data to export (tasks, time_entries, etc.)"
    )
    format: ReportFormat = Field(default=ReportFormat.CSV)
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Export filters"
    )


class ExportJobResponse(BaseModel):
    """Schema for export job response"""
    id: int
    workspace_id: int
    user_id: int
    export_type: str
    format: ReportFormat
    filters: Optional[Dict[str, Any]] = None
    status: ExportStatus
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    rows_exported: Optional[int] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExportJobListResponse(BaseModel):
    """Schema for export job list response"""
    exports: List[ExportJobResponse]
    total: int


# ============================================
# Dashboard Widget Schemas
# ============================================
class DashboardWidgetRequest(BaseModel):
    """Request for dashboard widget data"""
    workspace_id: int = Field(..., gt=0)
    widget_type: str = Field(
        ...,
        description="Type of widget: active_users, task_completion, time_tracked, etc."
    )
    date_range: Optional[AnalyticsDateRange] = None


class DashboardWidgetData(BaseModel):
    """Dashboard widget data"""
    widget_type: str
    title: str
    value: Any
    trend: Optional[float] = Field(
        None,
        description="Percentage change from previous period"
    )
    chart_data: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================
# Workspace Metrics Schemas
# ============================================
class WorkspaceMetricsResponse(BaseModel):
    """Schema for workspace metrics response"""
    id: int
    workspace_id: int
    date: datetime
    total_users: int
    active_users: int
    new_users: int
    total_projects: int
    total_tasks: int
    completed_tasks: int
    total_documents: int
    total_messages: int
    messages_sent: int
    tasks_created: int
    tasks_completed: int
    documents_uploaded: int
    meetings_held: int
    total_time_tracked_seconds: int
    storage_used_bytes: int
    engagement_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceMetricsTrend(BaseModel):
    """Workspace metrics trend over time"""
    dates: List[date]
    active_users: List[int]
    tasks_completed: List[int]
    messages_sent: List[int]
    time_tracked_hours: List[float]


# ============================================
# Top Performers Schemas
# ============================================
class TopPerformer(BaseModel):
    """Top performer data"""
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    metric_value: float
    metric_label: str
    rank: int


class TopPerformersResponse(BaseModel):
    """Top performers response"""
    metric_type: str
    period: str
    performers: List[TopPerformer]


# ============================================
# Activity Feed Schemas
# ============================================
class ActivityItem(BaseModel):
    """Activity feed item"""
    id: int
    event_type: str
    description: str
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ActivityFeedResponse(BaseModel):
    """Activity feed response"""
    activities: List[ActivityItem]
    total: int
