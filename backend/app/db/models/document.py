"""
Document Collaboration Models
Represents folders, documents, versions, shares, and comments for file management
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.session import Base


class DocumentSharePermission(str, Enum):
    """Document share permission enumeration"""
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class Folder(Base):
    """Folder model for organizing documents in hierarchical structure."""
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    parent_folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", backref="folders")
    parent_folder = relationship("Folder", remote_side=[id], backref="subfolders")
    created_by = relationship("User", backref="folders_created")
    documents = relationship("Document", back_populates="folder", cascade="all, delete-orphan")


class Document(Base):
    """Document model for file metadata and current version."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    # File metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_type = Column(String(50), nullable=False)  # e.g., "pdf", "docx", "xlsx"
    mime_type = Column(String(100), nullable=False)  # e.g., "application/pdf"
    file_size = Column(BigInteger, nullable=False)  # in bytes

    # Current version info
    current_version = Column(Integer, default=1, nullable=False)
    storage_path = Column(String(500), nullable=False)  # S3/MinIO path

    # Metadata
    tags = Column(Text, nullable=True)  # Comma-separated tags
    is_starred = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", backref="documents")
    folder = relationship("Folder", back_populates="documents")
    created_by = relationship("User", backref="documents_created")
    project = relationship("Project", backref="documents")
    task = relationship("Task", backref="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    shares = relationship("DocumentShare", back_populates="document", cascade="all, delete-orphan")
    comments = relationship("DocumentComment", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    """Document version model for version history."""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Version info
    version_number = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)  # S3/MinIO path
    file_size = Column(BigInteger, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=False)

    # Version metadata
    change_description = Column(Text, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="versions")
    created_by = relationship("User", backref="document_versions_created")


class DocumentShare(Base):
    """Document share model for sharing documents with users/teams."""
    __tablename__ = "document_shares"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    shared_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Share target (either user or team, not both)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    shared_with_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    # Permission level
    permission = Column(SQLEnum(DocumentSharePermission), default=DocumentSharePermission.VIEW, nullable=False)

    # Metadata
    message = Column(Text, nullable=True)  # Optional message when sharing
    expires_at = Column(DateTime, nullable=True)  # Optional expiration

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="shares")
    shared_by = relationship("User", foreign_keys=[shared_by_id], backref="document_shares_created")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id], backref="document_shares_received")
    shared_with_team = relationship("Team", backref="document_shares")


class DocumentComment(Base):
    """Document comment model for commenting on documents."""
    __tablename__ = "document_comments"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("document_comments.id"), nullable=True)

    # Comment content
    content = Column(Text, nullable=False)

    # Metadata
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id], backref="document_comments")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id], backref="document_comments_resolved")
    parent_comment = relationship("DocumentComment", remote_side=[id], backref="replies")
