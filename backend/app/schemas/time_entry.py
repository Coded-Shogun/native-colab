"""
Time Entry Schemas
Pydantic schemas for time tracking validation and serialization
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


# ============================================
# Time Entry Schemas
# ============================================
class TimeEntryBase(BaseModel):
    """Base schema for time entry data"""
    description: Optional[str] = Field(None, max_length=5000)
    is_billable: bool = Field(default=False)


class TimeEntryManualCreate(TimeEntryBase):
    """Schema for creating a manual time entry"""
    workspace_id: int = Field(..., gt=0)
    project_id: Optional[int] = Field(None, gt=0)
    task_id: Optional[int] = Field(None, gt=0)
    start_time: datetime
    end_time: datetime
    duration_minutes: Optional[Decimal] = Field(None, gt=0)

    @field_validator('end_time')
    @classmethod
    def validate_end_after_start(cls, v: datetime, info) -> datetime:
        """Validate that end_time is after start_time"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v


class TimeEntryTimerStart(BaseModel):
    """Schema for starting a timer"""
    workspace_id: int = Field(..., gt=0)
    project_id: Optional[int] = Field(None, gt=0)
    task_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=5000)
    is_billable: bool = Field(default=False)


class TimeEntryTimerStop(BaseModel):
    """Schema for stopping a timer"""
    description: Optional[str] = Field(None, max_length=5000)


class TimeEntryUpdate(BaseModel):
    """Schema for updating a time entry"""
    description: Optional[str] = Field(None, max_length=5000)
    project_id: Optional[int] = Field(None, gt=0)
    task_id: Optional[int] = Field(None, gt=0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[Decimal] = Field(None, gt=0)
    is_billable: Optional[bool] = None


class TimeEntryResponse(BaseModel):
    """Schema for time entry response"""
    id: int
    user_id: int
    workspace_id: int
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[Decimal] = None
    is_billable: bool
    is_manual: bool
    is_running: bool
    created_at: datetime
    updated_at: datetime

    # Related entity names (nested)
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    project_name: Optional[str] = None
    task_title: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class TimeEntryListResponse(BaseModel):
    """Schema for list of time entries"""
    entries: List[TimeEntryResponse]
    total: int
    total_duration_minutes: Decimal


class TimeSummary(BaseModel):
    """Schema for time tracking summary/statistics"""
    user_id: Optional[int] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    task_id: Optional[int] = None

    total_entries: int
    total_duration_minutes: Decimal
    billable_duration_minutes: Decimal
    non_billable_duration_minutes: Decimal

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TimeEntryFilters(BaseModel):
    """Schema for time entry filtering"""
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    is_billable: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
