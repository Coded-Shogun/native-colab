"""
Project Management Schemas
Pydantic schemas for project, task, and comment validation and serialization
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.db.models.project import ProjectStatus, TaskStatus, TaskPriority


# ============================================
# Project Schemas
# ============================================
class ProjectBase(BaseModel):
    """Base schema for project data"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: ProjectStatus = Field(default=ProjectStatus.PLANNING)
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""
    workspace_id: int = Field(..., gt=0)
    team_id: Optional[int] = Field(None, gt=0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name"""
        if not v or not v.strip():
            raise ValueError('Project name cannot be empty')
        return v.strip()


class ProjectUpdate(BaseModel):
    """Schema for updating project information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[ProjectStatus] = None
    team_id: Optional[int] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    is_archived: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name if provided"""
        if v is not None:
            if not v.strip():
                raise ValueError('Project name cannot be empty')
            return v.strip()
        return v


class ProjectResponse(BaseModel):
    """Schema for project response"""
    id: int
    workspace_id: int
    team_id: Optional[int] = None
    owner_id: int
    name: str
    description: Optional[str] = None
    status: str
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    # Stats
    task_count: Optional[int] = None
    completed_task_count: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class ProjectListResponse(BaseModel):
    """Schema for list of projects"""
    projects: List[ProjectResponse]
    total: int


# ============================================
# Task Schemas
# ============================================
class TaskBase(BaseModel):
    """Base schema for task data"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Schema for creating a new task"""
    project_id: int = Field(..., gt=0)
    assignee_id: Optional[int] = Field(None, gt=0)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate task title"""
        if not v or not v.strip():
            raise ValueError('Task title cannot be empty')
        return v.strip()


class TaskUpdate(BaseModel):
    """Schema for updating task information"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = Field(None, gt=0)
    due_date: Optional[datetime] = None
    position: Optional[int] = Field(None, ge=0)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate task title if provided"""
        if v is not None:
            if not v.strip():
                raise ValueError('Task title cannot be empty')
            return v.strip()
        return v


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: int
    project_id: int
    assignee_id: Optional[int] = None
    created_by_id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    position: int
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # User information (nested)
    assignee_email: Optional[str] = None
    assignee_name: Optional[str] = None
    created_by_email: Optional[str] = None
    created_by_name: Optional[str] = None

    # Comment count
    comment_count: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class TaskListResponse(BaseModel):
    """Schema for list of tasks"""
    tasks: List[TaskResponse]
    total: int


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status"""
    status: TaskStatus = Field(...)


class TaskAssigneeUpdate(BaseModel):
    """Schema for updating task assignee"""
    assignee_id: Optional[int] = Field(None, gt=0)


# ============================================
# Task Comment Schemas
# ============================================
class TaskCommentBase(BaseModel):
    """Base schema for task comment data"""
    content: str = Field(..., min_length=1, max_length=5000)


class TaskCommentCreate(TaskCommentBase):
    """Schema for creating a new task comment"""
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate comment content"""
        if not v or not v.strip():
            raise ValueError('Comment content cannot be empty')
        return v.strip()


class TaskCommentUpdate(BaseModel):
    """Schema for updating task comment"""
    content: str = Field(..., min_length=1, max_length=5000)

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate comment content"""
        if not v or not v.strip():
            raise ValueError('Comment content cannot be empty')
        return v.strip()


class TaskCommentResponse(BaseModel):
    """Schema for task comment response"""
    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    # Author information (nested)
    author_email: Optional[str] = None
    author_name: Optional[str] = None
    author_avatar_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class TaskWithCommentsResponse(TaskResponse):
    """Schema for task response with comments"""
    comments: List[TaskCommentResponse] = []

    model_config = {
        "from_attributes": True
    }
