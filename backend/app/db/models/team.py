"""
Team Model
Represents teams within workspaces
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class TeamRole(str, Enum):
    """Team-level roles"""
    LEAD = "lead"
    MEMBER = "member"


class Team(Base):
    """
    Team model representing a team within a workspace.

    Attributes:
        id: Primary key
        workspace_id: Foreign key to Workspace
        name: Team name
        description: Team description
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "teams"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)

    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="teams")
    members = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', workspace_id={self.workspace_id})>"


class TeamMember(Base):
    """
    Team membership linking users to teams with roles.

    Attributes:
        id: Primary key
        team_id: Foreign key to Team
        user_id: Foreign key to User
        role: Member's role in the team
        joined_at: Timestamp of when user joined
    """

    __tablename__ = "team_members"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Role
    role = Column(String(50), default=TeamRole.MEMBER.value, nullable=False)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Unique constraint: user can only be a member once per team
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, role='{self.role}')>"

    def is_lead(self) -> bool:
        """Check if member is team lead"""
        return self.role == TeamRole.LEAD.value
