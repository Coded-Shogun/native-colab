"""
User Model
Represents users in the system with authentication and profile information
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserRole(str, Enum):
    """User roles for system-wide permissions"""
    SUPER_ADMIN = "super_admin"
    USER = "user"


class User(Base):
    """
    User model for authentication and profile management.

    Attributes:
        id: Primary key
        email: Unique email address for login
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        avatar_url: URL to user's avatar image
        is_active: Whether the user account is active
        is_verified: Whether the user's email is verified
        role: System-wide role (super_admin or user)
        created_at: Timestamp of account creation
        updated_at: Timestamp of last update
        last_login: Timestamp of last login
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default=UserRole.USER.value, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    workspace_memberships = relationship(
        "WorkspaceMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    owned_workspaces = relationship(
        "Workspace",
        back_populates="owner",
        foreign_keys="Workspace.owner_id"
    )
    team_memberships = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    webhooks = relationship(
        "Webhook",
        back_populates="creator",
        cascade="all, delete-orphan",
        foreign_keys="Webhook.created_by"
    )
    integration_connections = relationship(
        "IntegrationConnection",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    search_indexes = relationship(
        "SearchIndex",
        back_populates="user"
    )
    search_history = relationship(
        "SearchHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    saved_searches = relationship(
        "SavedSearch",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    def is_super_admin(self) -> bool:
        """Check if user has super admin role"""
        return self.role == UserRole.SUPER_ADMIN.value
