"""
Messages API
Endpoints for channel messages, direct messages, and reactions
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    Channel,
    ChannelMember,
    Message,
    DirectMessage,
    MessageReaction,
)
from app.schemas.chat import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageListResponse,
    MessageReactionAdd,
    MessageReactionResponse,
    DirectMessageCreate,
    DirectMessageResponse,
    DirectMessageListResponse,
    DirectConversation,
    DirectConversationListResponse,
)
from app.core.deps import get_current_user
from app.realtime import (
    broadcast_message,
    broadcast_message_update,
    broadcast_message_delete,
    broadcast_reaction,
    send_direct_message,
)

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_channel_membership(
    channel_id: int,
    user: User,
    db: AsyncSession
) -> ChannelMember:
    """Check if user is a member of the channel"""
    # Get channel
    stmt = select(Channel).where(Channel.id == channel_id)
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    # For public channels, everyone with workspace access can read
    # For private channels, must be a member
    if channel.is_private:
        stmt = select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == user.id
        )
        result = await db.execute(stmt)
        membership = result.scalar_one_or_none()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a channel member to access private channel messages"
            )
        return membership

    # For public channels, check if membership exists (optional)
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == user.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def build_message_response(message: Message, db: AsyncSession) -> MessageResponse:
    """Build message response with nested user and reaction info"""
    # Load relationships
    stmt = select(Message).options(
        selectinload(Message.user),
        selectinload(Message.reactions).selectinload(MessageReaction.user)
    ).where(Message.id == message.id)
    result = await db.execute(stmt)
    message = result.scalar_one()

    # Count replies
    reply_count_stmt = select(func.count(Message.id)).where(
        Message.parent_message_id == message.id,
        Message.is_deleted == False
    )
    reply_count_result = await db.execute(reply_count_stmt)
    reply_count = reply_count_result.scalar()

    # Build reactions
    reactions = []
    for reaction in message.reactions:
        reactions.append(MessageReactionResponse(
            id=reaction.id,
            message_id=reaction.message_id,
            user_id=reaction.user_id,
            emoji=reaction.emoji,
            created_at=reaction.created_at,
            user_email=reaction.user.email if reaction.user else None,
            user_name=reaction.user.full_name if reaction.user else None,
        ))

    return MessageResponse(
        id=message.id,
        channel_id=message.channel_id,
        user_id=message.user_id,
        content=message.content if not message.is_deleted else "[deleted]",
        message_type=message.message_type,
        parent_message_id=message.parent_message_id,
        is_edited=message.is_edited,
        is_deleted=message.is_deleted,
        created_at=message.created_at,
        updated_at=message.updated_at,
        edited_at=message.edited_at,
        user_email=message.user.email if message.user else None,
        user_name=message.user.full_name if message.user else None,
        user_avatar=message.user.avatar_url if message.user else None,
        reactions=reactions,
        reply_count=reply_count,
    )


# ============================================
# Channel Message Endpoints
# ============================================
@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to a channel.
    User must be a member of private channels.
    """
    # Check channel membership
    membership = await check_channel_membership(message_data.channel_id, current_user, db)

    # If replying to a message, verify parent exists
    if message_data.parent_message_id:
        stmt = select(Message).where(
            Message.id == message_data.parent_message_id,
            Message.channel_id == message_data.channel_id
        )
        result = await db.execute(stmt)
        parent = result.scalar_one_or_none()

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent message not found in this channel"
            )

    # Create message
    new_message = Message(
        channel_id=message_data.channel_id,
        user_id=current_user.id,
        content=message_data.content,
        message_type=message_data.message_type,
        parent_message_id=message_data.parent_message_id
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    # Build response
    message_response = await build_message_response(new_message, db)

    # Broadcast message to channel in real-time
    await broadcast_message(message_data.channel_id, message_response.model_dump())

    return message_response


@router.get("/channel/{channel_id}", response_model=MessageListResponse)
async def list_channel_messages(
    channel_id: int,
    parent_message_id: Optional[int] = Query(None, gt=0),
    before_id: Optional[int] = Query(None, gt=0, description="Get messages before this ID (pagination)"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List messages in a channel.
    Supports pagination using before_id cursor.
    Can filter by parent_message_id to get thread replies.
    """
    # Check channel membership
    membership = await check_channel_membership(channel_id, current_user, db)

    # Update last_read_at if user is a member
    if membership:
        membership.last_read_at = datetime.utcnow()
        await db.commit()

    # Build query
    stmt = select(Message).where(
        Message.channel_id == channel_id,
        Message.is_deleted == False
    )

    # Filter by parent (for threads) or root messages
    if parent_message_id is not None:
        stmt = stmt.where(Message.parent_message_id == parent_message_id)
    else:
        # Only show root messages (not replies) by default
        stmt = stmt.where(Message.parent_message_id.is_(None))

    # Cursor pagination
    if before_id:
        stmt = stmt.where(Message.id < before_id)

    # Order by created_at descending (newest first)
    stmt = stmt.order_by(desc(Message.created_at))

    # Apply limit
    stmt = stmt.limit(limit + 1)  # Fetch one extra to check if there are more

    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Check if there are more messages
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Build responses
    message_responses = []
    for message in messages:
        message_responses.append(await build_message_response(message, db))

    # Count total (expensive, consider caching)
    count_stmt = select(func.count(Message.id)).where(
        Message.channel_id == channel_id,
        Message.is_deleted == False
    )
    if parent_message_id is not None:
        count_stmt = count_stmt.where(Message.parent_message_id == parent_message_id)
    else:
        count_stmt = count_stmt.where(Message.parent_message_id.is_(None))

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    return MessageListResponse(
        messages=message_responses,
        total=total,
        has_more=has_more
    )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific message by ID"""
    stmt = select(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Check channel access
    await check_channel_membership(message.channel_id, current_user, db)

    return await build_message_response(message, db)


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: int,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a message.
    Only the author can update their messages.
    """
    stmt = select(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Check ownership
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages"
        )

    # Check channel access
    await check_channel_membership(message.channel_id, current_user, db)

    # Update message
    message.content = message_update.content
    message.is_edited = True
    message.edited_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)

    # Build response
    message_response = await build_message_response(message, db)

    # Broadcast update to channel in real-time
    await broadcast_message_update(message.channel_id, message_response.model_dump())

    return message_response


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a message.
    Only the author can delete their messages.
    """
    stmt = select(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Check ownership
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )

    # Store channel_id before deletion
    channel_id = message.channel_id

    # Soft delete
    message.is_deleted = True
    message.content = "[deleted]"

    await db.commit()

    # Broadcast deletion to channel in real-time
    await broadcast_message_delete(channel_id, message_id)


# ============================================
# Message Reaction Endpoints
# ============================================
@router.post("/{message_id}/reactions", response_model=MessageReactionResponse, status_code=status.HTTP_201_CREATED)
async def add_reaction(
    message_id: int,
    reaction_data: MessageReactionAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add an emoji reaction to a message"""
    # Get message
    stmt = select(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Check channel access
    await check_channel_membership(message.channel_id, current_user, db)

    # Check if reaction already exists
    stmt = select(MessageReaction).where(
        MessageReaction.message_id == message_id,
        MessageReaction.user_id == current_user.id,
        MessageReaction.emoji == reaction_data.emoji
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already reacted with this emoji"
        )

    # Add reaction
    new_reaction = MessageReaction(
        message_id=message_id,
        user_id=current_user.id,
        emoji=reaction_data.emoji
    )

    db.add(new_reaction)
    await db.commit()
    await db.refresh(new_reaction)

    # Load user info
    stmt = select(MessageReaction).options(
        selectinload(MessageReaction.user)
    ).where(MessageReaction.id == new_reaction.id)
    result = await db.execute(stmt)
    new_reaction = result.scalar_one()

    # Build response
    reaction_response = MessageReactionResponse(
        id=new_reaction.id,
        message_id=new_reaction.message_id,
        user_id=new_reaction.user_id,
        emoji=new_reaction.emoji,
        created_at=new_reaction.created_at,
        user_email=new_reaction.user.email if new_reaction.user else None,
        user_name=new_reaction.user.full_name if new_reaction.user else None,
    )

    # Broadcast reaction to channel in real-time
    await broadcast_reaction(message.channel_id, {
        'action': 'add',
        'reaction': reaction_response.model_dump()
    })

    return reaction_response


@router.delete("/{message_id}/reactions/{emoji}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    message_id: int,
    emoji: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove an emoji reaction from a message"""
    # Get message
    stmt = select(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Check channel access
    await check_channel_membership(message.channel_id, current_user, db)

    # Get reaction
    stmt = select(MessageReaction).where(
        MessageReaction.message_id == message_id,
        MessageReaction.user_id == current_user.id,
        MessageReaction.emoji == emoji
    )
    result = await db.execute(stmt)
    reaction = result.scalar_one_or_none()

    if not reaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction not found"
        )

    await db.delete(reaction)
    await db.commit()


# ============================================
# Direct Message Endpoints
# ============================================
@router.post("/direct", response_model=DirectMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_direct_message(
    dm_data: DirectMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a direct message to another user"""
    # Cannot send to self
    if dm_data.recipient_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send direct message to yourself"
        )

    # Verify recipient exists
    stmt = select(User).where(User.id == dm_data.recipient_id)
    result = await db.execute(stmt)
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    # Create direct message
    new_dm = DirectMessage(
        sender_id=current_user.id,
        recipient_id=dm_data.recipient_id,
        content=dm_data.content,
        message_type=dm_data.message_type
    )

    db.add(new_dm)
    await db.commit()
    await db.refresh(new_dm)

    # Load relationships
    stmt = select(DirectMessage).options(
        selectinload(DirectMessage.sender),
        selectinload(DirectMessage.recipient)
    ).where(DirectMessage.id == new_dm.id)
    result = await db.execute(stmt)
    new_dm = result.scalar_one()

    # Build response
    dm_response = DirectMessageResponse(
        id=new_dm.id,
        sender_id=new_dm.sender_id,
        recipient_id=new_dm.recipient_id,
        content=new_dm.content,
        message_type=new_dm.message_type,
        is_read=new_dm.is_read,
        read_at=new_dm.read_at,
        created_at=new_dm.created_at,
        updated_at=new_dm.updated_at,
        sender_email=new_dm.sender.email if new_dm.sender else None,
        sender_name=new_dm.sender.full_name if new_dm.sender else None,
        sender_avatar=new_dm.sender.avatar_url if new_dm.sender else None,
        recipient_email=new_dm.recipient.email if new_dm.recipient else None,
        recipient_name=new_dm.recipient.full_name if new_dm.recipient else None,
        recipient_avatar=new_dm.recipient.avatar_url if new_dm.recipient else None,
    )

    # Send direct message to recipient in real-time
    await send_direct_message(dm_data.recipient_id, dm_response.model_dump())

    return dm_response


@router.get("/direct/conversations", response_model=DirectConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all direct message conversations for the current user.
    Shows unique users with last message and unread count.
    """
    # Get all unique users the current user has conversed with
    # This is a complex query - we'll get all messages and process them
    stmt = select(DirectMessage).where(
        or_(
            DirectMessage.sender_id == current_user.id,
            DirectMessage.recipient_id == current_user.id
        )
    ).order_by(desc(DirectMessage.created_at))

    result = await db.execute(stmt)
    all_messages = result.scalars().all()

    # Build conversations map
    conversations_map = {}

    for msg in all_messages:
        # Determine the other user
        other_user_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id

        if other_user_id not in conversations_map:
            conversations_map[other_user_id] = {
                'last_message': msg,
                'unread_count': 0
            }

        # Count unread (messages from other user that are unread)
        if msg.recipient_id == current_user.id and not msg.is_read:
            conversations_map[other_user_id]['unread_count'] += 1

    # Build conversation responses
    conversations = []
    for other_user_id, conv_data in conversations_map.items():
        # Load other user
        user_stmt = select(User).where(User.id == other_user_id)
        user_result = await db.execute(user_stmt)
        other_user = user_result.scalar_one_or_none()

        if not other_user:
            continue

        # Load last message with full details
        msg_stmt = select(DirectMessage).options(
            selectinload(DirectMessage.sender),
            selectinload(DirectMessage.recipient)
        ).where(DirectMessage.id == conv_data['last_message'].id)
        msg_result = await db.execute(msg_stmt)
        last_msg = msg_result.scalar_one()

        last_message_response = DirectMessageResponse(
            id=last_msg.id,
            sender_id=last_msg.sender_id,
            recipient_id=last_msg.recipient_id,
            content=last_msg.content,
            message_type=last_msg.message_type,
            is_read=last_msg.is_read,
            read_at=last_msg.read_at,
            created_at=last_msg.created_at,
            updated_at=last_msg.updated_at,
            sender_email=last_msg.sender.email if last_msg.sender else None,
            sender_name=last_msg.sender.full_name if last_msg.sender else None,
            sender_avatar=last_msg.sender.avatar_url if last_msg.sender else None,
            recipient_email=last_msg.recipient.email if last_msg.recipient else None,
            recipient_name=last_msg.recipient.full_name if last_msg.recipient else None,
            recipient_avatar=last_msg.recipient.avatar_url if last_msg.recipient else None,
        )

        conversations.append(DirectConversation(
            other_user_id=other_user.id,
            other_user_email=other_user.email,
            other_user_name=other_user.full_name,
            other_user_avatar=other_user.avatar_url,
            last_message=last_message_response,
            unread_count=conv_data['unread_count']
        ))

    return DirectConversationListResponse(
        conversations=conversations,
        total=len(conversations)
    )


@router.get("/direct/{other_user_id}", response_model=DirectMessageListResponse)
async def list_direct_messages(
    other_user_id: int,
    before_id: Optional[int] = Query(None, gt=0, description="Get messages before this ID (pagination)"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List direct messages with a specific user.
    Marks messages as read when fetched.
    """
    # Build query for conversation between current_user and other_user
    stmt = select(DirectMessage).where(
        or_(
            and_(
                DirectMessage.sender_id == current_user.id,
                DirectMessage.recipient_id == other_user_id
            ),
            and_(
                DirectMessage.sender_id == other_user_id,
                DirectMessage.recipient_id == current_user.id
            )
        )
    )

    # Cursor pagination
    if before_id:
        stmt = stmt.where(DirectMessage.id < before_id)

    # Order by created_at descending
    stmt = stmt.order_by(desc(DirectMessage.created_at))

    # Apply limit
    stmt = stmt.limit(limit + 1)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Check if there are more messages
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Mark received messages as read
    for msg in messages:
        if msg.recipient_id == current_user.id and not msg.is_read:
            msg.is_read = True
            msg.read_at = datetime.utcnow()

    await db.commit()

    # Build responses
    message_responses = []
    for msg in messages:
        # Reload with relationships
        msg_stmt = select(DirectMessage).options(
            selectinload(DirectMessage.sender),
            selectinload(DirectMessage.recipient)
        ).where(DirectMessage.id == msg.id)
        msg_result = await db.execute(msg_stmt)
        msg = msg_result.scalar_one()

        message_responses.append(DirectMessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            recipient_id=msg.recipient_id,
            content=msg.content,
            message_type=msg.message_type,
            is_read=msg.is_read,
            read_at=msg.read_at,
            created_at=msg.created_at,
            updated_at=msg.updated_at,
            sender_email=msg.sender.email if msg.sender else None,
            sender_name=msg.sender.full_name if msg.sender else None,
            sender_avatar=msg.sender.avatar_url if msg.sender else None,
            recipient_email=msg.recipient.email if msg.recipient else None,
            recipient_name=msg.recipient.full_name if msg.recipient else None,
            recipient_avatar=msg.recipient.avatar_url if msg.recipient else None,
        ))

    # Count total
    count_stmt = select(func.count(DirectMessage.id)).where(
        or_(
            and_(
                DirectMessage.sender_id == current_user.id,
                DirectMessage.recipient_id == other_user_id
            ),
            and_(
                DirectMessage.sender_id == other_user_id,
                DirectMessage.recipient_id == current_user.id
            )
        )
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    return DirectMessageListResponse(
        messages=message_responses,
        total=total,
        has_more=has_more
    )
