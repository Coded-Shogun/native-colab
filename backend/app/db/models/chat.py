"""
Chat Models
Represents channels, messages, direct messages, and reactions for real-time chat
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.session import Base


class MessageType(str, Enum):
    """Message type enumeration"""
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    SYSTEM = "system"


class ChannelMemberRole(str, Enum):
    """Channel member role enumeration"""
    MEMBER = "member"
    ADMIN = "admin"


class Channel(Base):
    """
    Channel model for workspace chat channels.

    Channels are workspace-scoped and can be public or private.
    Similar to Slack channels or Discord channels.

    Attributes:
        id: Primary key
        workspace_id: Foreign key to Workspace
        name: Channel name (unique within workspace)
        description: Channel description
        is_private: Whether channel is private (invite-only)
        created_by_id: Foreign key to User who created the channel
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "channels"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Channel Info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_private = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", backref="channels")
    creator = relationship("User", foreign_keys=[created_by_id], backref="created_channels")
    members = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")

    # Unique constraint: channel name unique within workspace
    __table_args__ = (
        UniqueConstraint('workspace_id', 'name', name='uix_workspace_channel_name'),
    )

    def __repr__(self):
        return f"<Channel(id={self.id}, name={self.name}, workspace_id={self.workspace_id})>"


class ChannelMember(Base):
    """
    Channel membership model (many-to-many between Channel and User).

    Tracks which users are members of which channels and their roles.

    Attributes:
        id: Primary key
        channel_id: Foreign key to Channel
        user_id: Foreign key to User
        role: Member role (member or admin)
        joined_at: When user joined the channel
        last_read_at: Last time user read messages (for unread count)
    """

    __tablename__ = "channel_members"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Membership Info
    role = Column(SQLEnum(ChannelMemberRole), default=ChannelMemberRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_read_at = Column(DateTime, nullable=True)

    # Relationships
    channel = relationship("Channel", back_populates="members")
    user = relationship("User", backref="channel_memberships")

    # Unique constraint: user can only be member of channel once
    __table_args__ = (
        UniqueConstraint('channel_id', 'user_id', name='uix_channel_user'),
    )

    def __repr__(self):
        return f"<ChannelMember(channel_id={self.channel_id}, user_id={self.user_id}, role={self.role})>"


class Message(Base):
    """
    Message model for channel messages.

    Represents individual messages sent in channels.
    Supports threading, editing, and deletion.

    Attributes:
        id: Primary key
        channel_id: Foreign key to Channel
        user_id: Foreign key to User (sender)
        content: Message content
        message_type: Type of message (text, file, image, system)
        parent_message_id: Optional parent message for threading
        is_edited: Whether message has been edited
        is_deleted: Soft delete flag
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        edited_at: Timestamp of last edit
    """

    __tablename__ = "messages"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)

    # Message Info
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT, nullable=False)

    # Flags
    is_edited = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    edited_at = Column(DateTime, nullable=True)

    # Relationships
    channel = relationship("Channel", back_populates="messages")
    user = relationship("User", foreign_keys=[user_id], backref="messages")
    parent_message = relationship("Message", remote_side=[id], backref="replies")
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Message(id={self.id}, channel_id={self.channel_id}, user_id={self.user_id})>"


class DirectMessage(Base):
    """
    Direct message model for 1-on-1 conversations.

    Represents private messages between two users.

    Attributes:
        id: Primary key
        sender_id: Foreign key to User (sender)
        recipient_id: Foreign key to User (recipient)
        content: Message content
        message_type: Type of message (text, file, image)
        is_read: Whether recipient has read the message
        read_at: When message was read
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "direct_messages"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Message Info
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT, nullable=False)

    # Read Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_direct_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], backref="received_direct_messages")

    def __repr__(self):
        return f"<DirectMessage(id={self.id}, sender_id={self.sender_id}, recipient_id={self.recipient_id})>"


class MessageReaction(Base):
    """
    Message reaction model for emoji reactions.

    Tracks emoji reactions to messages (like Slack reactions).

    Attributes:
        id: Primary key
        message_id: Foreign key to Message
        user_id: Foreign key to User
        emoji: Emoji character or code
        created_at: Timestamp of creation
    """

    __tablename__ = "message_reactions"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Reaction Info
    emoji = Column(String(50), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="reactions")
    user = relationship("User", backref="message_reactions")

    # Unique constraint: user can only react with same emoji once per message
    __table_args__ = (
        UniqueConstraint('message_id', 'user_id', 'emoji', name='uix_message_user_emoji'),
    )

    def __repr__(self):
        return f"<MessageReaction(message_id={self.message_id}, user_id={self.user_id}, emoji={self.emoji})>"
