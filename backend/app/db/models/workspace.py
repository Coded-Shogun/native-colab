"""
Workspace Model
Represents workspaces/organizations that contain teams and projects
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class WorkspaceRole(str, Enum):
    """Workspace-level roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"


class Workspace(Base):
    """
    Workspace model representing an organization or team workspace.

    Attributes:
        id: Primary key
        name: Workspace name
        slug: URL-friendly identifier
        description: Workspace description
        owner_id: Foreign key to User who owns this workspace
        is_active: Whether the workspace is active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "workspaces"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)

    # Owner
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="owned_workspaces", foreign_keys=[owner_id])
    members = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    teams = relationship(
        "Team",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    webhooks = relationship(
        "Webhook",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    integration_connections = relationship(
        "IntegrationConnection",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    search_indexes = relationship(
        "SearchIndex",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    search_history = relationship(
        "SearchHistory",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    saved_searches = relationship(
        "SavedSearch",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    analytics_events = relationship(
        "AnalyticsEvent",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    export_jobs = relationship(
        "ExportJob",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    metrics = relationship(
        "WorkspaceMetrics",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class WorkspaceMember(Base):
    """
    Workspace membership linking users to workspaces with roles.

    Attributes:
        id: Primary key
        workspace_id: Foreign key to Workspace
        user_id: Foreign key to User
        role: Member's role in the workspace
        joined_at: Timestamp of when user joined
    """

    __tablename__ = "workspace_members"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Role
    role = Column(String(50), default=WorkspaceRole.MEMBER.value, nullable=False)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Unique constraint: user can only be a member once per workspace
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspace_memberships")

    def __repr__(self):
        return f"<WorkspaceMember(workspace_id={self.workspace_id}, user_id={self.user_id}, role='{self.role}')>"

    def is_admin(self) -> bool:
        """Check if member has admin or owner role"""
        return self.role in [WorkspaceRole.ADMIN.value, WorkspaceRole.OWNER.value]
