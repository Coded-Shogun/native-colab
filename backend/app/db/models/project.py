"""
Project Model
Represents projects within workspaces for task management and collaboration
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class ProjectStatus(str, Enum):
    """Project status options"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(Base):
    """
    Project model for organizing work within workspaces.

    Attributes:
        id: Primary key
        workspace_id: Foreign key to Workspace
        team_id: Optional foreign key to Team
        name: Project name
        description: Project description
        status: Current project status
        owner_id: User who created/owns the project
        start_date: Project start date
        due_date: Project due date
        is_archived: Whether project is archived
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "projects"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36), nullable=True, index=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=ProjectStatus.PLANNING.value, nullable=False)

    # Dates
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)

    # Status
    is_archived = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", backref="projects")
    team = relationship("Team", backref="projects")
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_projects")
    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Task.position"
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


class TaskStatus(str, Enum):
    """Task status options"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(Base):
    """
    Task model for individual work items within projects.

    Attributes:
        id: Primary key
        project_id: Foreign key to Project
        assignee_id: Optional foreign key to User (assigned to)
        created_by_id: Foreign key to User (creator)
        title: Task title
        description: Task description
        status: Current task status
        priority: Task priority level
        position: Order position for Kanban boards
        due_date: Task due date
        completed_at: When task was completed
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "tasks"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Basic Info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=TaskStatus.TODO.value, nullable=False)
    priority = Column(String(50), default=TaskPriority.MEDIUM.value, nullable=False)
    position = Column(Integer, default=0, nullable=False)

    # Dates
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], backref="assigned_tasks")
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_tasks")
    comments = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at"
    )

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


class TaskComment(Base):
    """
    Task comment model for discussions and updates on tasks.

    Attributes:
        id: Primary key
        task_id: Foreign key to Task
        author_id: Foreign key to User (comment author)
        content: Comment text content
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "task_comments"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Content
    content = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="comments")
    author = relationship("User", backref="task_comments")

    def __repr__(self):
        return f"<TaskComment(id={self.id}, task_id={self.task_id}, author_id={self.author_id})>"
