"""
Chat Schemas
Pydantic schemas for chat channels, messages, and real-time communication
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.db.models.chat import MessageType, ChannelMemberRole


# ============================================
# Channel Schemas
# ============================================
class ChannelBase(BaseModel):
    """Base channel schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_private: bool = Field(default=False)


class ChannelCreate(ChannelBase):
    """Schema for creating a channel"""
    workspace_id: int = Field(..., gt=0)


class ChannelUpdate(BaseModel):
    """Schema for updating a channel"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)


class ChannelMemberInfo(BaseModel):
    """Schema for channel member information"""
    id: int
    user_id: int
    role: ChannelMemberRole
    joined_at: datetime
    last_read_at: Optional[datetime] = None

    # Nested user info
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ChannelResponse(BaseModel):
    """Schema for channel response"""
    id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    is_private: bool
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    # Statistics
    member_count: Optional[int] = None
    unread_count: Optional[int] = None

    # Nested info
    creator_email: Optional[str] = None
    creator_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ChannelDetailResponse(ChannelResponse):
    """Detailed channel response with members"""
    members: List[ChannelMemberInfo] = []

    model_config = {"from_attributes": True}


class ChannelListResponse(BaseModel):
    """Schema for channel list response"""
    channels: List[ChannelResponse]
    total: int


# ============================================
# Channel Member Schemas
# ============================================
class ChannelMemberAdd(BaseModel):
    """Schema for adding a member to a channel"""
    user_id: int = Field(..., gt=0)
    role: ChannelMemberRole = Field(default=ChannelMemberRole.MEMBER)


class ChannelMemberRoleUpdate(BaseModel):
    """Schema for updating a member's role"""
    role: ChannelMemberRole


# ============================================
# Message Schemas
# ============================================
class MessageBase(BaseModel):
    """Base message schema"""
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = Field(default=MessageType.TEXT)


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    channel_id: int = Field(..., gt=0)
    parent_message_id: Optional[int] = Field(None, gt=0)


class MessageUpdate(BaseModel):
    """Schema for updating a message"""
    content: str = Field(..., min_length=1, max_length=10000)


class MessageReactionAdd(BaseModel):
    """Schema for adding a reaction to a message"""
    emoji: str = Field(..., min_length=1, max_length=50)

    @field_validator('emoji')
    @classmethod
    def validate_emoji(cls, v: str) -> str:
        """Validate emoji is not empty after stripping"""
        if not v.strip():
            raise ValueError('Emoji cannot be empty')
        return v.strip()


class MessageReactionResponse(BaseModel):
    """Schema for message reaction response"""
    id: int
    message_id: int
    user_id: int
    emoji: str
    created_at: datetime

    # Nested user info
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: int
    channel_id: int
    user_id: int
    content: str
    message_type: MessageType
    parent_message_id: Optional[int] = None
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    edited_at: Optional[datetime] = None

    # Nested user info
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

    # Reactions summary
    reactions: Optional[List[MessageReactionResponse]] = []
    reply_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    """Schema for message list response"""
    messages: List[MessageResponse]
    total: int
    has_more: bool = False


# ============================================
# Direct Message Schemas
# ============================================
class DirectMessageCreate(BaseModel):
    """Schema for creating a direct message"""
    recipient_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = Field(default=MessageType.TEXT)


class DirectMessageResponse(BaseModel):
    """Schema for direct message response"""
    id: int
    sender_id: int
    recipient_id: int
    content: str
    message_type: MessageType
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Nested sender info
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None

    # Nested recipient info
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class DirectMessageListResponse(BaseModel):
    """Schema for direct message list response"""
    messages: List[DirectMessageResponse]
    total: int
    has_more: bool = False


class DirectConversation(BaseModel):
    """Schema for direct conversation summary"""
    other_user_id: int
    other_user_email: str
    other_user_name: str
    other_user_avatar: Optional[str] = None
    last_message: Optional[DirectMessageResponse] = None
    unread_count: int = 0


class DirectConversationListResponse(BaseModel):
    """Schema for direct conversation list"""
    conversations: List[DirectConversation]
    total: int


# ============================================
# Real-time Event Schemas (for Socket.io)
# ============================================
class TypingEvent(BaseModel):
    """Schema for typing indicator event"""
    channel_id: int
    user_id: int
    is_typing: bool


class OnlineStatusEvent(BaseModel):
    """Schema for user online status event"""
    user_id: int
    is_online: bool
    last_seen: Optional[datetime] = None


class MessageReadEvent(BaseModel):
    """Schema for message read event"""
    channel_id: Optional[int] = None
    direct_message_id: Optional[int] = None
    user_id: int
    read_at: datetime


# ============================================
# Search and Filter Schemas
# ============================================
class MessageSearchFilters(BaseModel):
    """Schema for message search filters"""
    channel_id: Optional[int] = Field(None, gt=0)
    user_id: Optional[int] = Field(None, gt=0)
    search_query: Optional[str] = Field(None, max_length=500)
    message_type: Optional[MessageType] = None
    parent_message_id: Optional[int] = Field(None, gt=0)
    before_date: Optional[datetime] = None
    after_date: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)


class ChannelSearchFilters(BaseModel):
    """Schema for channel search filters"""
    workspace_id: int = Field(..., gt=0)
    search_query: Optional[str] = Field(None, max_length=100)
    is_private: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)
