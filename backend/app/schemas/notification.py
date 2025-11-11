"""
Notification Schemas
Pydantic schemas for notifications and user preferences
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.models.notification import (
    NotificationType,
    NotificationChannel,
    NotificationPriority,
)


# ============================================
# Notification Schemas
# ============================================
class NotificationBase(BaseModel):
    """Base notification schema"""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    notification_type: NotificationType
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    action_url: Optional[str] = Field(None, max_length=500)


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    user_id: int = Field(..., gt=0)
    event_id: Optional[int] = Field(None, gt=0)
    message_id: Optional[int] = Field(None, gt=0)
    task_id: Optional[int] = Field(None, gt=0)
    project_id: Optional[int] = Field(None, gt=0)
    workspace_id: Optional[int] = Field(None, gt=0)
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: int
    user_id: int
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    action_url: Optional[str] = None

    # Related entity IDs
    event_id: Optional[int] = None
    message_id: Optional[int] = None
    task_id: Optional[int] = None
    project_id: Optional[int] = None
    workspace_id: Optional[int] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None

    # Delivery tracking
    is_read: bool
    read_at: Optional[datetime] = None
    sent_in_app: bool
    sent_email: bool
    sent_push: bool

    # Timestamps
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Schema for notification list response"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationMarkRead(BaseModel):
    """Schema for marking notifications as read"""
    notification_ids: List[int] = Field(..., min_length=1, max_length=100)


# ============================================
# Notification Preference Schemas
# ============================================
class NotificationPreferenceBase(BaseModel):
    """Base notification preference schema"""
    notification_type: NotificationType
    in_app_enabled: bool = Field(default=True)
    email_enabled: bool = Field(default=True)
    push_enabled: bool = Field(default=False)
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating a notification preference"""
    pass


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating a notification preference"""
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)


class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preference response"""
    id: int
    user_id: int
    notification_type: NotificationType
    in_app_enabled: bool
    email_enabled: bool
    push_enabled: bool
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationPreferenceListResponse(BaseModel):
    """Schema for notification preference list response"""
    preferences: List[NotificationPreferenceResponse]
    total: int


class BulkPreferenceUpdate(BaseModel):
    """Schema for bulk updating notification preferences"""
    notification_types: List[NotificationType] = Field(..., min_length=1)
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None


# ============================================
# Notification Statistics
# ============================================
class NotificationStats(BaseModel):
    """Schema for notification statistics"""
    total_notifications: int
    unread_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_priority: Dict[str, int]


# ============================================
# Email Template Data
# ============================================
class EmailNotificationData(BaseModel):
    """Schema for email notification template data"""
    recipient_email: str
    recipient_name: str
    subject: str
    template_name: str
    template_data: Dict[str, Any]
