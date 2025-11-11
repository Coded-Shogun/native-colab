"""
Channels API
Endpoints for managing workspace chat channels
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    User,
    Channel,
    ChannelMember,
    ChannelMemberRole,
    Message,
    Workspace,
    WorkspaceMember,
)
from app.schemas.chat import (
    ChannelCreate,
    ChannelUpdate,
    ChannelResponse,
    ChannelDetailResponse,
    ChannelListResponse,
    ChannelMemberAdd,
    ChannelMemberRoleUpdate,
    ChannelMemberInfo,
)
from app.core.deps import get_current_user

router = APIRouter()


# ============================================
# Helper Functions
# ============================================
async def check_workspace_access(
    workspace_id: int,
    user: User,
    db: AsyncSession
) -> WorkspaceMember:
    """Check if user has access to the workspace"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    return membership


async def get_channel_with_access_check(
    channel_id: int,
    user: User,
    db: AsyncSession
) -> Channel:
    """Get channel and verify user has access"""
    stmt = select(Channel).where(Channel.id == channel_id)
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    # Check if user has workspace access
    await check_workspace_access(channel.workspace_id, user, db)

    # For private channels, check membership
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
                detail="You don't have access to this private channel"
            )

    return channel


async def check_channel_admin(
    channel_id: int,
    user: User,
    db: AsyncSession
) -> ChannelMember:
    """Check if user is channel admin"""
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == user.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership or membership.role != ChannelMemberRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a channel admin to perform this action"
        )

    return membership


async def build_channel_response(
    channel: Channel,
    user: User,
    db: AsyncSession,
    include_members: bool = False
) -> ChannelResponse:
    """Build channel response with statistics"""
    # Load relationships
    stmt = select(Channel).options(
        selectinload(Channel.creator),
        selectinload(Channel.members).selectinload(ChannelMember.user)
    ).where(Channel.id == channel.id)
    result = await db.execute(stmt)
    channel = result.scalar_one()

    # Count members
    member_count = len(channel.members)

    # Count unread messages
    member_stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel.id,
        ChannelMember.user_id == user.id
    )
    member_result = await db.execute(member_stmt)
    membership = member_result.scalar_one_or_none()

    unread_count = 0
    if membership:
        # Count messages after last read
        unread_stmt = select(func.count(Message.id)).where(
            Message.channel_id == channel.id,
            Message.is_deleted == False
        )
        if membership.last_read_at:
            unread_stmt = unread_stmt.where(Message.created_at > membership.last_read_at)
        unread_result = await db.execute(unread_stmt)
        unread_count = unread_result.scalar()

    response_data = {
        "id": channel.id,
        "workspace_id": channel.workspace_id,
        "name": channel.name,
        "description": channel.description,
        "is_private": channel.is_private,
        "created_by_id": channel.created_by_id,
        "created_at": channel.created_at,
        "updated_at": channel.updated_at,
        "member_count": member_count,
        "unread_count": unread_count,
        "creator_email": channel.creator.email if channel.creator else None,
        "creator_name": channel.creator.full_name if channel.creator else None,
    }

    if include_members:
        members_data = []
        for member in channel.members:
            members_data.append(ChannelMemberInfo(
                id=member.id,
                user_id=member.user_id,
                role=member.role,
                joined_at=member.joined_at,
                last_read_at=member.last_read_at,
                user_email=member.user.email if member.user else None,
                user_name=member.user.full_name if member.user else None,
            ))
        response_data["members"] = members_data
        return ChannelDetailResponse(**response_data)

    return ChannelResponse(**response_data)


# ============================================
# Channel CRUD Endpoints
# ============================================
@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new channel in a workspace.
    Creator automatically becomes an admin member.
    """
    # Check workspace access
    await check_workspace_access(channel_data.workspace_id, current_user, db)

    # Check if channel name already exists in workspace
    stmt = select(Channel).where(
        Channel.workspace_id == channel_data.workspace_id,
        Channel.name == channel_data.name
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Channel '{channel_data.name}' already exists in this workspace"
        )

    # Create channel
    new_channel = Channel(
        workspace_id=channel_data.workspace_id,
        name=channel_data.name,
        description=channel_data.description,
        is_private=channel_data.is_private,
        created_by_id=current_user.id
    )

    db.add(new_channel)
    await db.flush()

    # Add creator as admin member
    creator_membership = ChannelMember(
        channel_id=new_channel.id,
        user_id=current_user.id,
        role=ChannelMemberRole.ADMIN
    )
    db.add(creator_membership)

    await db.commit()
    await db.refresh(new_channel)

    return await build_channel_response(new_channel, current_user, db)


@router.get("/workspace/{workspace_id}", response_model=ChannelListResponse)
async def list_channels(
    workspace_id: int,
    search_query: Optional[str] = Query(None, max_length=100),
    is_private: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List channels in a workspace.
    Shows all public channels and private channels where user is a member.
    """
    # Check workspace access
    await check_workspace_access(workspace_id, current_user, db)

    # Build query
    stmt = select(Channel).where(Channel.workspace_id == workspace_id)

    # Apply filters
    if search_query:
        stmt = stmt.where(
            or_(
                Channel.name.ilike(f"%{search_query}%"),
                Channel.description.ilike(f"%{search_query}%")
            )
        )

    if is_private is not None:
        stmt = stmt.where(Channel.is_private == is_private)

    # For private channels, only show channels where user is member
    # For public channels, show all
    subquery = select(ChannelMember.channel_id).where(
        ChannelMember.user_id == current_user.id
    )
    stmt = stmt.where(
        or_(
            Channel.is_private == False,
            Channel.id.in_(subquery)
        )
    )

    # Order by created_at
    stmt = stmt.order_by(Channel.created_at.desc())

    # Count total
    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    channels = result.scalars().all()

    # Build responses
    channel_responses = []
    for channel in channels:
        channel_responses.append(await build_channel_response(channel, current_user, db))

    return ChannelListResponse(
        channels=channel_responses,
        total=total
    )


@router.get("/{channel_id}", response_model=ChannelDetailResponse)
async def get_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get channel details including members"""
    channel = await get_channel_with_access_check(channel_id, current_user, db)
    return await build_channel_response(channel, current_user, db, include_members=True)


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    channel_update: ChannelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update channel details.
    Only channel admins can update.
    """
    channel = await get_channel_with_access_check(channel_id, current_user, db)
    await check_channel_admin(channel_id, current_user, db)

    # Update fields
    update_data = channel_update.model_dump(exclude_unset=True)

    # Check name uniqueness if name is being changed
    if 'name' in update_data and update_data['name'] != channel.name:
        stmt = select(Channel).where(
            Channel.workspace_id == channel.workspace_id,
            Channel.name == update_data['name']
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Channel '{update_data['name']}' already exists in this workspace"
            )

    for field, value in update_data.items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)

    return await build_channel_response(channel, current_user, db)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a channel.
    Only channel admins can delete.
    """
    channel = await get_channel_with_access_check(channel_id, current_user, db)
    await check_channel_admin(channel_id, current_user, db)

    await db.delete(channel)
    await db.commit()


# ============================================
# Channel Member Management Endpoints
# ============================================
@router.post("/{channel_id}/members", response_model=ChannelMemberInfo, status_code=status.HTTP_201_CREATED)
async def add_channel_member(
    channel_id: int,
    member_data: ChannelMemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a member to a channel.
    Only channel admins can add members.
    """
    channel = await get_channel_with_access_check(channel_id, current_user, db)
    await check_channel_admin(channel_id, current_user, db)

    # Verify user has workspace access
    await check_workspace_access(channel.workspace_id, User(id=member_data.user_id), db)

    # Check if already a member
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == member_data.user_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this channel"
        )

    # Add member
    new_member = ChannelMember(
        channel_id=channel_id,
        user_id=member_data.user_id,
        role=member_data.role
    )

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    # Load user info
    stmt = select(ChannelMember).options(
        selectinload(ChannelMember.user)
    ).where(ChannelMember.id == new_member.id)
    result = await db.execute(stmt)
    new_member = result.scalar_one()

    return ChannelMemberInfo(
        id=new_member.id,
        user_id=new_member.user_id,
        role=new_member.role,
        joined_at=new_member.joined_at,
        last_read_at=new_member.last_read_at,
        user_email=new_member.user.email if new_member.user else None,
        user_name=new_member.user.full_name if new_member.user else None,
    )


@router.put("/{channel_id}/members/{user_id}/role", response_model=ChannelMemberInfo)
async def update_member_role(
    channel_id: int,
    user_id: int,
    role_update: ChannelMemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a member's role in a channel.
    Only channel admins can update roles.
    """
    await get_channel_with_access_check(channel_id, current_user, db)
    await check_channel_admin(channel_id, current_user, db)

    # Get member
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this channel"
        )

    member.role = role_update.role
    await db.commit()
    await db.refresh(member)

    # Load user info
    stmt = select(ChannelMember).options(
        selectinload(ChannelMember.user)
    ).where(ChannelMember.id == member.id)
    result = await db.execute(stmt)
    member = result.scalar_one()

    return ChannelMemberInfo(
        id=member.id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
        last_read_at=member.last_read_at,
        user_email=member.user.email if member.user else None,
        user_name=member.user.full_name if member.user else None,
    )


@router.delete("/{channel_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_channel_member(
    channel_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a member from a channel.
    Channel admins can remove others, users can remove themselves.
    """
    await get_channel_with_access_check(channel_id, current_user, db)

    # Check if user is removing themselves or if they're admin
    is_self_remove = (user_id == current_user.id)
    if not is_self_remove:
        await check_channel_admin(channel_id, current_user, db)

    # Get member
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this channel"
        )

    await db.delete(member)
    await db.commit()


@router.post("/{channel_id}/join", response_model=ChannelMemberInfo, status_code=status.HTTP_201_CREATED)
async def join_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Join a public channel.
    Private channels require invitation.
    """
    # Get channel
    stmt = select(Channel).where(Channel.id == channel_id)
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    # Check workspace access
    await check_workspace_access(channel.workspace_id, current_user, db)

    # Can only join public channels
    if channel.is_private:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot join private channel. You need an invitation."
        )

    # Check if already a member
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user.id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this channel"
        )

    # Join channel
    new_member = ChannelMember(
        channel_id=channel_id,
        user_id=current_user.id,
        role=ChannelMemberRole.MEMBER
    )

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    # Load user info
    stmt = select(ChannelMember).options(
        selectinload(ChannelMember.user)
    ).where(ChannelMember.id == new_member.id)
    result = await db.execute(stmt)
    new_member = result.scalar_one()

    return ChannelMemberInfo(
        id=new_member.id,
        user_id=new_member.user_id,
        role=new_member.role,
        joined_at=new_member.joined_at,
        last_read_at=new_member.last_read_at,
        user_email=new_member.user.email if new_member.user else None,
        user_name=new_member.user.full_name if new_member.user else None,
    )


@router.post("/{channel_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave a channel (remove self from channel)"""
    return await remove_channel_member(channel_id, current_user.id, current_user, db)
