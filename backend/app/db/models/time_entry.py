"""
Time Entry Model
Represents time tracking entries for projects and tasks
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Numeric
from sqlalchemy.orm import relationship

from app.db.session import Base


class TimeEntry(Base):
    """
    Time entry model for tracking time spent on projects and tasks.

    Supports both timer-based tracking and manual entry.

    Attributes:
        id: Primary key
        user_id: Foreign key to User (who tracked the time)
        workspace_id: Foreign key to Workspace (for reporting/filtering)
        project_id: Optional foreign key to Project
        task_id: Optional foreign key to Task
        description: Description of work done
        start_time: When work started
        end_time: When work ended (null for running timers)
        duration_minutes: Calculated or manually entered duration
        is_billable: Whether this time is billable
        is_manual: Whether this was manually entered (vs timer)
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "time_entries"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    # Time Tracking
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)  # Null for running timers
    duration_minutes = Column(Numeric(10, 2), nullable=True)  # Calculated or manual

    # Flags
    is_billable = Column(Boolean, default=False, nullable=False)
    is_manual = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="time_entries")
    workspace = relationship("Workspace", backref="time_entries")
    project = relationship("Project", backref="time_entries")
    task = relationship("Task", backref="time_entries")

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, user_id={self.user_id}, duration={self.duration_minutes})>"

    @property
    def is_running(self) -> bool:
        """Check if this timer is currently running"""
        return self.end_time is None

    def calculate_duration(self) -> float:
        """
        Calculate duration in minutes.
        Returns duration from start_time to end_time (or now if running).
        """
        if self.start_time is None:
            return 0.0

        end = self.end_time or datetime.utcnow()
        delta = end - self.start_time
        return round(delta.total_seconds() / 60, 2)
