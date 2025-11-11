"""
Search Models
Database models for comprehensive search functionality
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.db.base import Base


# ============================================
# Enums
# ============================================
class ContentType(str, enum.Enum):
    """Content types that can be searched"""
    MESSAGE = "message"
    DOCUMENT = "document"
    TASK = "task"
    EVENT = "event"
    WHITEBOARD = "whiteboard"
    MEETING = "meeting"
    PROJECT = "project"
    FOLDER = "folder"
    COMMENT = "comment"


# ============================================
# Search Index Model
# ============================================
class SearchIndex(Base):
    """
    Search index for all searchable content
    Uses PostgreSQL full-text search with tsvector
    """
    __tablename__ = "search_indexes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Content reference
    content_type: Mapped[ContentType] = mapped_column(
        SQLEnum(ContentType, name="contenttype"),
        nullable=False,
        index=True
    )
    content_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Workspace and user context
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Can be null for system-generated content
        index=True
    )

    # Project context (optional)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Searchable content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Full-text search vector (PostgreSQL specific)
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        nullable=True
    )

    # Additional metadata as JSON
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )

    # Tags for filtering
    tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )

    # Access control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    content_created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )
    content_updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
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

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="search_indexes")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="search_indexes")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="search_indexes")

    # Composite indexes for performance
    __table_args__ = (
        Index(
            "ix_search_indexes_composite",
            "workspace_id",
            "content_type",
            "is_deleted"
        ),
        Index(
            "ix_search_indexes_project_type",
            "project_id",
            "content_type"
        ),
        Index(
            "ix_search_indexes_user_type",
            "user_id",
            "content_type"
        ),
        # GIN index for full-text search (created in migration)
        Index(
            "ix_search_indexes_search_vector",
            "search_vector",
            postgresql_using="gin"
        ),
    )

    def __repr__(self):
        return f"<SearchIndex {self.content_type}:{self.content_id} - {self.title[:50]}>"


# ============================================
# Search History Model
# ============================================
class SearchHistory(Base):
    """
    User search history for analytics and suggestions
    """
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User and workspace
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Search query
    query: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    # Filters applied
    filters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )

    # Content types searched
    content_types: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )

    # Search results
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Result clicked (if any)
    clicked_content_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    clicked_content_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Performance metrics
    search_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # IP and device info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="search_history")
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="search_history")

    __table_args__ = (
        Index(
            "ix_search_history_user_workspace",
            "user_id",
            "workspace_id",
            "created_at"
        ),
    )

    def __repr__(self):
        return f"<SearchHistory user={self.user_id} query='{self.query[:30]}' results={self.results_count}>"


# ============================================
# Saved Search Model
# ============================================
class SavedSearch(Base):
    """
    User's saved search queries for quick access
    """
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User and workspace
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Search details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Search query
    query: Mapped[str] = mapped_column(String(500), nullable=False)

    # Filters
    filters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )

    # Content types
    content_types: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )

    # Settings
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Notifications
    notify_on_new_results: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Usage statistics
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

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

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_searches")
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="saved_searches")

    __table_args__ = (
        Index(
            "ix_saved_searches_user_workspace",
            "user_id",
            "workspace_id"
        ),
    )

    def __repr__(self):
        return f"<SavedSearch '{self.name}' by user={self.user_id}>"
