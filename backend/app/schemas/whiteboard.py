"""
Whiteboard Schemas
Pydantic schemas for collaborative whiteboards
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.models.whiteboard import ElementType, WhiteboardAccessLevel


# ============================================
# Whiteboard Schemas
# ============================================
class WhiteboardBase(BaseModel):
    """Base whiteboard schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    canvas_width: int = Field(default=3000, ge=500, le=10000)
    canvas_height: int = Field(default=2000, ge=500, le=10000)
    background_color: str = Field(default="#FFFFFF", pattern=r'^#[0-9A-Fa-f]{6}$')
    grid_enabled: bool = Field(default=True)
    is_public: bool = Field(default=False)


class WhiteboardCreate(WhiteboardBase):
    """Schema for creating a whiteboard"""
    workspace_id: int = Field(..., gt=0)
    project_id: Optional[int] = Field(None, gt=0)


class WhiteboardUpdate(BaseModel):
    """Schema for updating a whiteboard"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    background_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    grid_enabled: Optional[bool] = None
    is_public: Optional[bool] = None
    is_locked: Optional[bool] = None


class WhiteboardResponse(BaseModel):
    """Schema for whiteboard response"""
    id: int
    workspace_id: int
    created_by_id: int
    project_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    canvas_width: int
    canvas_height: int
    background_color: str
    grid_enabled: bool
    is_public: bool
    is_locked: bool
    is_template: bool
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime

    # Nested info
    creator_name: Optional[str] = None
    creator_email: Optional[str] = None
    element_count: int = 0
    participant_count: int = 0
    active_participant_count: int = 0

    model_config = {"from_attributes": True}


class WhiteboardListResponse(BaseModel):
    """Schema for whiteboard list response"""
    whiteboards: List[WhiteboardResponse]
    total: int


# ============================================
# Whiteboard Element Schemas
# ============================================
class WhiteboardElementBase(BaseModel):
    """Base whiteboard element schema"""
    element_id: str = Field(..., min_length=1, max_length=100)
    element_type: ElementType
    x_position: float
    y_position: float
    width: Optional[float] = None
    height: Optional[float] = None
    stroke_color: str = Field(default="#000000", pattern=r'^#[0-9A-Fa-f]{6}$')
    fill_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    stroke_width: float = Field(default=2.0, ge=0.1, le=50.0)
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    element_data: Dict[str, Any] = Field(default_factory=dict)
    z_index: int = Field(default=0)


class WhiteboardElementCreate(WhiteboardElementBase):
    """Schema for creating a whiteboard element"""
    pass


class WhiteboardElementUpdate(BaseModel):
    """Schema for updating a whiteboard element"""
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    stroke_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    fill_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    stroke_width: Optional[float] = Field(None, ge=0.1, le=50.0)
    opacity: Optional[float] = Field(None, ge=0.0, le=1.0)
    element_data: Optional[Dict[str, Any]] = None
    z_index: Optional[int] = None
    is_locked: Optional[bool] = None


class WhiteboardElementResponse(BaseModel):
    """Schema for whiteboard element response"""
    id: int
    whiteboard_id: int
    created_by_id: int
    element_id: str
    element_type: ElementType
    x_position: float
    y_position: float
    width: Optional[float] = None
    height: Optional[float] = None
    stroke_color: str
    fill_color: Optional[str] = None
    stroke_width: float
    opacity: float
    element_data: Dict[str, Any]
    z_index: int
    is_locked: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    # Nested info
    creator_name: Optional[str] = None

    model_config = {"from_attributes": True}


class WhiteboardElementListResponse(BaseModel):
    """Schema for whiteboard element list response"""
    elements: List[WhiteboardElementResponse]
    total: int


class BulkElementCreate(BaseModel):
    """Schema for creating multiple elements at once"""
    elements: List[WhiteboardElementCreate] = Field(..., min_length=1, max_length=1000)


class BulkElementDelete(BaseModel):
    """Schema for deleting multiple elements"""
    element_ids: List[str] = Field(..., min_length=1, max_length=1000)


# ============================================
# Whiteboard Participant Schemas
# ============================================
class WhiteboardParticipantAdd(BaseModel):
    """Schema for adding a participant to whiteboard"""
    user_id: int = Field(..., gt=0)
    access_level: WhiteboardAccessLevel = Field(default=WhiteboardAccessLevel.EDIT)


class WhiteboardParticipantUpdate(BaseModel):
    """Schema for updating participant access"""
    access_level: WhiteboardAccessLevel


class WhiteboardParticipantResponse(BaseModel):
    """Schema for whiteboard participant response"""
    id: int
    whiteboard_id: int
    user_id: int
    access_level: WhiteboardAccessLevel
    is_active: bool
    last_seen_at: Optional[datetime] = None
    cursor_x: Optional[float] = None
    cursor_y: Optional[float] = None
    selected_element_id: Optional[str] = None
    joined_at: datetime

    # Nested info
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class WhiteboardParticipantListResponse(BaseModel):
    """Schema for participant list response"""
    participants: List[WhiteboardParticipantResponse]
    total: int


# ============================================
# Whiteboard Snapshot Schemas
# ============================================
class WhiteboardSnapshotCreate(BaseModel):
    """Schema for creating a snapshot"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class WhiteboardSnapshotResponse(BaseModel):
    """Schema for snapshot response"""
    id: int
    whiteboard_id: int
    created_by_id: int
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_auto_save: bool
    created_at: datetime

    # Nested info
    creator_name: Optional[str] = None
    element_count: int = 0

    model_config = {"from_attributes": True}


class WhiteboardSnapshotDetailResponse(WhiteboardSnapshotResponse):
    """Schema for detailed snapshot response with full data"""
    elements_data: List[Dict[str, Any]]
    canvas_settings: Dict[str, Any]


class WhiteboardSnapshotListResponse(BaseModel):
    """Schema for snapshot list response"""
    snapshots: List[WhiteboardSnapshotResponse]
    total: int


# ============================================
# Real-time Event Schemas
# ============================================
class CursorPositionUpdate(BaseModel):
    """Schema for cursor position updates (Socket.io)"""
    x: float
    y: float


class ElementSelectionUpdate(BaseModel):
    """Schema for element selection updates (Socket.io)"""
    element_id: Optional[str] = None


class DrawingEvent(BaseModel):
    """Schema for drawing events (Socket.io)"""
    action: str  # "create", "update", "delete", "move"
    element: Optional[WhiteboardElementCreate] = None
    element_id: Optional[str] = None
    updates: Optional[Dict[str, Any]] = None


# ============================================
# Whiteboard Statistics
# ============================================
class WhiteboardStats(BaseModel):
    """Schema for whiteboard statistics"""
    total_whiteboards: int
    total_elements: int
    active_participants: int
    recent_activity: List[WhiteboardResponse]
