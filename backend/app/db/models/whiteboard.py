"""
Whiteboard Models
Represents collaborative whiteboards, elements, participants, and snapshots
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.session import Base


class ElementType(str, Enum):
    """Whiteboard element type enumeration"""
    PATH = "path"  # Freehand drawing
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    LINE = "line"
    ARROW = "arrow"
    TEXT = "text"
    IMAGE = "image"
    STICKY_NOTE = "sticky_note"


class WhiteboardAccessLevel(str, Enum):
    """Whiteboard access level enumeration"""
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class Whiteboard(Base):
    """Whiteboard model for collaborative drawing sessions."""
    __tablename__ = "whiteboards"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    meeting_id = Column(Integer, nullable=True)  # For future meeting integration

    # Whiteboard details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Canvas settings
    canvas_width = Column(Integer, default=3000, nullable=False)
    canvas_height = Column(Integer, default=2000, nullable=False)
    background_color = Column(String(7), default="#FFFFFF", nullable=False)
    grid_enabled = Column(Boolean, default=True, nullable=False)

    # Access control
    is_public = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)  # Prevent editing

    # Metadata
    is_template = Column(Boolean, default=False, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", backref="whiteboards")
    created_by = relationship("User", backref="whiteboards_created")
    project = relationship("Project", backref="whiteboards")
    elements = relationship("WhiteboardElement", back_populates="whiteboard", cascade="all, delete-orphan")
    participants = relationship("WhiteboardParticipant", back_populates="whiteboard", cascade="all, delete-orphan")
    snapshots = relationship("WhiteboardSnapshot", back_populates="whiteboard", cascade="all, delete-orphan")


class WhiteboardElement(Base):
    """Whiteboard element model representing shapes, drawings, and text on the canvas."""
    __tablename__ = "whiteboard_elements"

    id = Column(Integer, primary_key=True, index=True)
    whiteboard_id = Column(Integer, ForeignKey("whiteboards.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Element identification
    element_id = Column(String(100), nullable=False, index=True)  # Client-side UUID
    element_type = Column(SQLEnum(ElementType), nullable=False)

    # Position and size
    x_position = Column(Float, nullable=False)
    y_position = Column(Float, nullable=False)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    # Style properties
    stroke_color = Column(String(7), default="#000000", nullable=False)
    fill_color = Column(String(7), nullable=True)
    stroke_width = Column(Float, default=2.0, nullable=False)
    opacity = Column(Float, default=1.0, nullable=False)

    # Element-specific data (JSON for flexibility)
    # For PATH: {points: [[x1,y1], [x2,y2], ...]}
    # For TEXT: {text: "...", fontSize: 16, fontFamily: "Arial"}
    # For IMAGE: {url: "...", originalWidth: 100, originalHeight: 100}
    element_data = Column(JSON, nullable=False, default=dict)

    # Layer management
    z_index = Column(Integer, default=0, nullable=False)

    # State
    is_locked = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    whiteboard = relationship("Whiteboard", back_populates="elements")
    created_by = relationship("User", backref="whiteboard_elements_created")


class WhiteboardParticipant(Base):
    """Whiteboard participant model for tracking who has access and is currently active."""
    __tablename__ = "whiteboard_participants"

    id = Column(Integer, primary_key=True, index=True)
    whiteboard_id = Column(Integer, ForeignKey("whiteboards.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Access level
    access_level = Column(SQLEnum(WhiteboardAccessLevel), default=WhiteboardAccessLevel.EDIT, nullable=False)

    # Activity tracking
    is_active = Column(Boolean, default=False, nullable=False)
    last_seen_at = Column(DateTime, nullable=True)

    # Cursor position (for real-time collaboration)
    cursor_x = Column(Float, nullable=True)
    cursor_y = Column(Float, nullable=True)

    # Selected element (what user is currently working on)
    selected_element_id = Column(String(100), nullable=True)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    whiteboard = relationship("Whiteboard", back_populates="participants")
    user = relationship("User", backref="whiteboard_participations")


class WhiteboardSnapshot(Base):
    """Whiteboard snapshot model for saving versions/history of the whiteboard."""
    __tablename__ = "whiteboard_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    whiteboard_id = Column(Integer, ForeignKey("whiteboards.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Snapshot details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Snapshot data (complete state)
    elements_data = Column(JSON, nullable=False)  # Array of all elements at this point
    canvas_settings = Column(JSON, nullable=False)  # Canvas width, height, background, etc.

    # Metadata
    thumbnail_url = Column(String(500), nullable=True)
    is_auto_save = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    whiteboard = relationship("Whiteboard", back_populates="snapshots")
    created_by = relationship("User", backref="whiteboard_snapshots_created")
