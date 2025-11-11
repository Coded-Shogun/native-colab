"""
Socket.io Manager
Handles real-time WebSocket connections and events
"""

import socketio
from typing import Dict, Set, Optional
from datetime import datetime
import logging
from jose import JWTError, jwt

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create Socket.io server with AsyncServer for FastAPI
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.cors_origins_list,
    logger=True,
    engineio_logger=True
)

# Create ASGI app
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io'
)


class ConnectionManager:
    """
    Manages Socket.io connections, rooms, and user presence.

    Tracks:
    - Active connections (sid -> user_id mapping)
    - User presence (user_id -> set of sids)
    - Channel/Room memberships
    """

    def __init__(self):
        self.active_connections: Dict[str, int] = {}  # sid -> user_id
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> set of sids
        self.typing_users: Dict[int, Set[int]] = {}  # channel_id -> set of user_ids

    def connect_user(self, sid: str, user_id: int):
        """Register a new connection"""
        self.active_connections[sid] = user_id

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(sid)

        logger.info(f"User {user_id} connected with sid {sid}")

    def disconnect_user(self, sid: str):
        """Remove a connection"""
        if sid in self.active_connections:
            user_id = self.active_connections[sid]
            del self.active_connections[sid]

            if user_id in self.user_connections:
                self.user_connections[user_id].discard(sid)

                # If no more connections, remove user
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
                    logger.info(f"User {user_id} fully disconnected")

            logger.info(f"Connection {sid} disconnected")

    def get_user_id(self, sid: str) -> Optional[int]:
        """Get user ID for a connection"""
        return self.active_connections.get(sid)

    def is_user_online(self, user_id: int) -> bool:
        """Check if user has any active connections"""
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0

    def get_user_sids(self, user_id: int) -> Set[str]:
        """Get all connection IDs for a user"""
        return self.user_connections.get(user_id, set())

    def add_typing_user(self, channel_id: int, user_id: int):
        """Mark user as typing in a channel"""
        if channel_id not in self.typing_users:
            self.typing_users[channel_id] = set()
        self.typing_users[channel_id].add(user_id)

    def remove_typing_user(self, channel_id: int, user_id: int):
        """Remove user from typing in a channel"""
        if channel_id in self.typing_users:
            self.typing_users[channel_id].discard(user_id)
            if not self.typing_users[channel_id]:
                del self.typing_users[channel_id]

    def get_typing_users(self, channel_id: int) -> Set[int]:
        """Get users currently typing in a channel"""
        return self.typing_users.get(channel_id, set())


# Global connection manager instance
connection_manager = ConnectionManager()


async def authenticate_socket(token: str) -> Optional[int]:
    """
    Authenticate a Socket.io connection using JWT token.
    Returns user_id if valid, None otherwise.
    """
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id: int = int(payload.get("sub"))
        if user_id is None:
            return None

        return user_id

    except JWTError as e:
        logger.error(f"JWT authentication error: {e}")
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


# ============================================
# Socket.io Event Handlers
# ============================================

@sio.event
async def connect(sid, environ, auth):
    """
    Handle new Socket.io connection.
    Requires authentication via token in auth dict.
    """
    logger.info(f"New connection attempt: {sid}")

    # Get token from auth
    if not auth or 'token' not in auth:
        logger.warning(f"Connection {sid} rejected: No token provided")
        return False

    token = auth['token']

    # Authenticate user
    user_id = await authenticate_socket(token)

    if user_id is None:
        logger.warning(f"Connection {sid} rejected: Invalid token")
        return False

    # Register connection
    connection_manager.connect_user(sid, user_id)

    # Send connection confirmation
    await sio.emit('connected', {
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)

    # Broadcast user online status to all their connections
    await broadcast_user_status(user_id, is_online=True)

    logger.info(f"User {user_id} connected successfully with sid {sid}")
    return True


@sio.event
async def disconnect(sid):
    """Handle Socket.io disconnection"""
    user_id = connection_manager.get_user_id(sid)

    if user_id:
        # Remove from all typing indicators
        for channel_id in list(connection_manager.typing_users.keys()):
            if user_id in connection_manager.typing_users[channel_id]:
                connection_manager.remove_typing_user(channel_id, user_id)
                await broadcast_typing_indicator(channel_id, user_id, False)

        # Check if user still has other connections
        was_last_connection = len(connection_manager.get_user_sids(user_id)) == 1

        connection_manager.disconnect_user(sid)

        # If this was the last connection, broadcast offline status
        if was_last_connection:
            await broadcast_user_status(user_id, is_online=False)

    logger.info(f"Connection {sid} disconnected")


@sio.event
async def join_channel(sid, data):
    """
    Join a channel room for real-time updates.
    Data: { channel_id: int }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    channel_id = data.get('channel_id')
    if not channel_id:
        await sio.emit('error', {'message': 'channel_id required'}, room=sid)
        return

    # TODO: Verify user has access to this channel (check DB)
    # For now, we'll allow joining

    room_name = f"channel_{channel_id}"
    await sio.enter_room(sid, room_name)

    logger.info(f"User {user_id} joined channel {channel_id}")

    await sio.emit('channel_joined', {
        'channel_id': channel_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)


@sio.event
async def leave_channel(sid, data):
    """
    Leave a channel room.
    Data: { channel_id: int }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    channel_id = data.get('channel_id')
    if not channel_id:
        return

    room_name = f"channel_{channel_id}"
    await sio.leave_room(sid, room_name)

    # Remove from typing indicators
    connection_manager.remove_typing_user(channel_id, user_id)
    await broadcast_typing_indicator(channel_id, user_id, False)

    logger.info(f"User {user_id} left channel {channel_id}")


@sio.event
async def typing_start(sid, data):
    """
    User started typing in a channel.
    Data: { channel_id: int }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    channel_id = data.get('channel_id')
    if not channel_id:
        return

    connection_manager.add_typing_user(channel_id, user_id)
    await broadcast_typing_indicator(channel_id, user_id, True)


@sio.event
async def typing_stop(sid, data):
    """
    User stopped typing in a channel.
    Data: { channel_id: int }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    channel_id = data.get('channel_id')
    if not channel_id:
        return

    connection_manager.remove_typing_user(channel_id, user_id)
    await broadcast_typing_indicator(channel_id, user_id, False)


@sio.event
async def mark_read(sid, data):
    """
    Mark messages as read in a channel.
    Data: { channel_id: int, message_id: int (optional) }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    channel_id = data.get('channel_id')
    if not channel_id:
        return

    # Broadcast read receipt
    await broadcast_read_receipt(channel_id, user_id)


@sio.event
async def get_online_users(sid, data):
    """
    Get list of online users.
    Data: { user_ids: [int] }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    user_ids = data.get('user_ids', [])

    online_users = []
    for uid in user_ids:
        if connection_manager.is_user_online(uid):
            online_users.append(uid)

    await sio.emit('online_users', {
        'user_ids': online_users,
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)


# ============================================
# Whiteboard Event Handlers
# ============================================

@sio.event
async def join_whiteboard(sid, data):
    """
    Join a whiteboard room for real-time collaboration.
    Data: { whiteboard_id: int }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    whiteboard_id = data.get('whiteboard_id')
    if not whiteboard_id:
        await sio.emit('error', {'message': 'whiteboard_id required'}, room=sid)
        return

    # TODO: Verify user has access to this whiteboard (check DB)
    # For now, we'll allow joining

    room_name = f"whiteboard_{whiteboard_id}"
    await sio.enter_room(sid, room_name)

    # Update participant status in database
    from app.db.session import async_session_maker
    from app.db.models.whiteboard import WhiteboardParticipant
    from sqlalchemy import select, and_

    async with async_session_maker() as db:
        stmt = select(WhiteboardParticipant).where(
            and_(
                WhiteboardParticipant.whiteboard_id == whiteboard_id,
                WhiteboardParticipant.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        participant = result.scalar_one_or_none()

        if participant:
            participant.is_active = True
            participant.last_seen_at = datetime.utcnow()
            await db.commit()

            # Notify other participants
            await broadcast_participant_joined(whiteboard_id, user_id, skip_sid=sid)

    logger.info(f"User {user_id} joined whiteboard {whiteboard_id}")

    await sio.emit('whiteboard_joined', {
        'whiteboard_id': whiteboard_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)


@sio.event
async def leave_whiteboard(sid, data):
    """
    Leave a whiteboard room.
    Data: { whiteboard_id: int }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    whiteboard_id = data.get('whiteboard_id')
    if not whiteboard_id:
        return

    room_name = f"whiteboard_{whiteboard_id}"
    await sio.leave_room(sid, room_name)

    # Update participant status in database
    from app.db.session import async_session_maker
    from app.db.models.whiteboard import WhiteboardParticipant
    from sqlalchemy import select, and_

    async with async_session_maker() as db:
        stmt = select(WhiteboardParticipant).where(
            and_(
                WhiteboardParticipant.whiteboard_id == whiteboard_id,
                WhiteboardParticipant.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        participant = result.scalar_one_or_none()

        if participant:
            participant.is_active = False
            participant.last_seen_at = datetime.utcnow()
            participant.cursor_x = None
            participant.cursor_y = None
            participant.selected_element_id = None
            await db.commit()

            # Notify other participants
            await broadcast_participant_left(whiteboard_id, user_id)

    logger.info(f"User {user_id} left whiteboard {whiteboard_id}")


@sio.event
async def drawing_event(sid, data):
    """
    Handle drawing events (create/update/delete/move elements).
    Data: {
        whiteboard_id: int,
        action: str,  # "create", "update", "delete", "move"
        element: dict (optional),
        element_id: str (optional),
        updates: dict (optional)
    }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    whiteboard_id = data.get('whiteboard_id')
    if not whiteboard_id:
        return

    action = data.get('action')
    if not action:
        return

    # Update whiteboard last_activity_at
    from app.db.session import async_session_maker
    from app.db.models.whiteboard import Whiteboard

    async with async_session_maker() as db:
        stmt = select(Whiteboard).where(Whiteboard.id == whiteboard_id)
        result = await db.execute(stmt)
        whiteboard = result.scalar_one_or_none()

        if whiteboard:
            whiteboard.last_activity_at = datetime.utcnow()
            await db.commit()

    # Broadcast drawing event to all participants except sender
    await broadcast_drawing_event(whiteboard_id, {
        'action': action,
        'element': data.get('element'),
        'element_id': data.get('element_id'),
        'updates': data.get('updates'),
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, skip_sid=sid)

    logger.info(f"User {user_id} performed {action} on whiteboard {whiteboard_id}")


@sio.event
async def cursor_move(sid, data):
    """
    Broadcast cursor position to other participants.
    Data: {
        whiteboard_id: int,
        x: float,
        y: float
    }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    whiteboard_id = data.get('whiteboard_id')
    cursor_x = data.get('x')
    cursor_y = data.get('y')

    if whiteboard_id is None or cursor_x is None or cursor_y is None:
        return

    # Update participant cursor position in database (async, no await to avoid blocking)
    from app.db.session import async_session_maker
    from app.db.models.whiteboard import WhiteboardParticipant
    from sqlalchemy import select, and_

    async def update_cursor():
        async with async_session_maker() as db:
            stmt = select(WhiteboardParticipant).where(
                and_(
                    WhiteboardParticipant.whiteboard_id == whiteboard_id,
                    WhiteboardParticipant.user_id == user_id
                )
            )
            result = await db.execute(stmt)
            participant = result.scalar_one_or_none()

            if participant:
                participant.cursor_x = cursor_x
                participant.cursor_y = cursor_y
                participant.last_seen_at = datetime.utcnow()
                await db.commit()

    # Fire and forget
    import asyncio
    asyncio.create_task(update_cursor())

    # Broadcast cursor position to other participants
    await broadcast_cursor_position(whiteboard_id, user_id, cursor_x, cursor_y, skip_sid=sid)


@sio.event
async def element_select(sid, data):
    """
    Broadcast element selection to other participants.
    Data: {
        whiteboard_id: int,
        element_id: str (optional - null to deselect)
    }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    whiteboard_id = data.get('whiteboard_id')
    element_id = data.get('element_id')

    if whiteboard_id is None:
        return

    # Update participant selected element in database
    from app.db.session import async_session_maker
    from app.db.models.whiteboard import WhiteboardParticipant
    from sqlalchemy import select, and_

    async with async_session_maker() as db:
        stmt = select(WhiteboardParticipant).where(
            and_(
                WhiteboardParticipant.whiteboard_id == whiteboard_id,
                WhiteboardParticipant.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        participant = result.scalar_one_or_none()

        if participant:
            participant.selected_element_id = element_id
            participant.last_seen_at = datetime.utcnow()
            await db.commit()

    # Broadcast element selection to other participants
    await broadcast_element_selection(whiteboard_id, user_id, element_id, skip_sid=sid)

    logger.info(f"User {user_id} selected element {element_id} on whiteboard {whiteboard_id}")


# ============================================
# Broadcast Helper Functions
# ============================================

async def broadcast_message(channel_id: int, message_data: dict):
    """
    Broadcast a new message to all users in a channel.
    """
    room_name = f"channel_{channel_id}"
    await sio.emit('new_message', message_data, room=room_name)
    logger.info(f"Broadcasted message to channel {channel_id}")


async def broadcast_message_update(channel_id: int, message_data: dict):
    """
    Broadcast message edit/update to all users in a channel.
    """
    room_name = f"channel_{channel_id}"
    await sio.emit('message_updated', message_data, room=room_name)


async def broadcast_message_delete(channel_id: int, message_id: int):
    """
    Broadcast message deletion to all users in a channel.
    """
    room_name = f"channel_{channel_id}"
    await sio.emit('message_deleted', {
        'message_id': message_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name)


async def broadcast_reaction(channel_id: int, reaction_data: dict):
    """
    Broadcast reaction add/remove to all users in a channel.
    """
    room_name = f"channel_{channel_id}"
    await sio.emit('reaction_updated', reaction_data, room=room_name)


async def broadcast_typing_indicator(channel_id: int, user_id: int, is_typing: bool):
    """
    Broadcast typing indicator to all users in a channel (except the typer).
    """
    room_name = f"channel_{channel_id}"
    await sio.emit('user_typing', {
        'channel_id': channel_id,
        'user_id': user_id,
        'is_typing': is_typing,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name, skip_sid=connection_manager.get_user_sids(user_id))


async def broadcast_user_status(user_id: int, is_online: bool):
    """
    Broadcast user online/offline status to all connected users.
    """
    await sio.emit('user_status', {
        'user_id': user_id,
        'is_online': is_online,
        'timestamp': datetime.utcnow().isoformat()
    })


async def broadcast_read_receipt(channel_id: int, user_id: int):
    """
    Broadcast read receipt to channel.
    """
    room_name = f"channel_{channel_id}"
    await sio.emit('message_read', {
        'channel_id': channel_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name)


async def send_direct_message(recipient_id: int, message_data: dict):
    """
    Send a direct message to a specific user (all their connections).
    """
    sids = connection_manager.get_user_sids(recipient_id)
    for sid in sids:
        await sio.emit('new_direct_message', message_data, room=sid)


async def broadcast_to_user(user_id: int, event: str, data: dict):
    """
    Broadcast an event to all connections of a specific user.
    """
    sids = connection_manager.get_user_sids(user_id)
    for sid in sids:
        await sio.emit(event, data, room=sid)


# ============================================
# Whiteboard Broadcast Helper Functions
# ============================================

async def broadcast_participant_joined(whiteboard_id: int, user_id: int, skip_sid: str = None):
    """
    Broadcast participant joined event to all participants in whiteboard.
    """
    room_name = f"whiteboard_{whiteboard_id}"
    await sio.emit('participant_joined', {
        'whiteboard_id': whiteboard_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name, skip_sid=skip_sid)
    logger.info(f"Broadcasted participant_joined for user {user_id} in whiteboard {whiteboard_id}")


async def broadcast_participant_left(whiteboard_id: int, user_id: int):
    """
    Broadcast participant left event to all participants in whiteboard.
    """
    room_name = f"whiteboard_{whiteboard_id}"
    await sio.emit('participant_left', {
        'whiteboard_id': whiteboard_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name)
    logger.info(f"Broadcasted participant_left for user {user_id} in whiteboard {whiteboard_id}")


async def broadcast_drawing_event(whiteboard_id: int, event_data: dict, skip_sid: str = None):
    """
    Broadcast drawing event (create/update/delete/move) to all participants.
    """
    room_name = f"whiteboard_{whiteboard_id}"
    await sio.emit('drawing_update', event_data, room=room_name, skip_sid=skip_sid)
    logger.info(f"Broadcasted drawing_update to whiteboard {whiteboard_id}")


async def broadcast_cursor_position(whiteboard_id: int, user_id: int, cursor_x: float, cursor_y: float, skip_sid: str = None):
    """
    Broadcast cursor position to all participants except sender.
    """
    room_name = f"whiteboard_{whiteboard_id}"
    await sio.emit('cursor_update', {
        'whiteboard_id': whiteboard_id,
        'user_id': user_id,
        'x': cursor_x,
        'y': cursor_y,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name, skip_sid=skip_sid)


async def broadcast_element_selection(whiteboard_id: int, user_id: int, element_id: str, skip_sid: str = None):
    """
    Broadcast element selection to all participants except sender.
    """
    room_name = f"whiteboard_{whiteboard_id}"
    await sio.emit('element_selected', {
        'whiteboard_id': whiteboard_id,
        'user_id': user_id,
        'element_id': element_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name, skip_sid=skip_sid)


# ============================================
# Meeting / WebRTC Event Handlers
# ============================================

@sio.event
async def join_meeting(sid, data):
    """
    Join a meeting room for video/audio communication.
    Data: { meeting_id: int, participant_id: int, peer_id: str }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    meeting_id = data.get('meeting_id')
    participant_id = data.get('participant_id')
    peer_id = data.get('peer_id')

    if not meeting_id or not participant_id or not peer_id:
        await sio.emit('error', {'message': 'meeting_id, participant_id, and peer_id required'}, room=sid)
        return

    # TODO: Verify user has access to this meeting (check DB)

    room_name = f"meeting_{meeting_id}"
    await sio.enter_room(sid, room_name)

    # Update participant in database
    from app.db.session import async_session_maker
    from app.db.models.meeting import MeetingParticipant, ParticipantStatus

    async with async_session_maker() as db:
        from sqlalchemy import select
        stmt = select(MeetingParticipant).where(MeetingParticipant.id == participant_id)
        result = await db.execute(stmt)
        participant = result.scalar_one_or_none()

        if participant:
            participant.connection_id = sid
            participant.peer_id = peer_id
            participant.status = ParticipantStatus.JOINED
            participant.joined_at = datetime.utcnow()
            await db.commit()

            # Broadcast participant joined to others
            await broadcast_meeting_participant_joined(meeting_id, user_id, peer_id, skip_sid=sid)

    logger.info(f"User {user_id} joined meeting {meeting_id} with peer_id {peer_id}")

    await sio.emit('meeting_joined', {
        'meeting_id': meeting_id,
        'peer_id': peer_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)


@sio.event
async def leave_meeting(sid, data):
    """
    Leave a meeting room.
    Data: { meeting_id: int }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    meeting_id = data.get('meeting_id')
    if not meeting_id:
        return

    room_name = f"meeting_{meeting_id}"
    await sio.leave_room(sid, room_name)

    # Update participant status in database
    from app.db.session import async_session_maker
    from app.db.models.meeting import MeetingParticipant, ParticipantStatus
    from sqlalchemy import select, and_

    async with async_session_maker() as db:
        stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        participant = result.scalar_one_or_none()

        if participant:
            participant.status = ParticipantStatus.LEFT
            participant.left_at = datetime.utcnow()
            participant.connection_id = None
            participant.peer_id = None
            await db.commit()

            # Broadcast participant left
            await broadcast_meeting_participant_left(meeting_id, user_id)

    logger.info(f"User {user_id} left meeting {meeting_id}")


@sio.event
async def webrtc_offer(sid, data):
    """
    Handle WebRTC offer (SDP) and forward to target peer.
    Data: { meeting_id: int, target_peer_id: str, sdp: str }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    meeting_id = data.get('meeting_id')
    target_peer_id = data.get('target_peer_id')
    sdp = data.get('sdp')

    if not meeting_id or not target_peer_id or not sdp:
        return

    # Get sender's peer_id and forward offer
    from app.db.session import async_session_maker
    from app.db.models.meeting import MeetingParticipant
    from sqlalchemy import select, and_

    async with async_session_maker() as db:
        stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        sender = result.scalar_one_or_none()

        if not sender or not sender.peer_id:
            return

        # Find target participant
        target_stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.peer_id == target_peer_id
            )
        )
        target_result = await db.execute(target_stmt)
        target = target_result.scalar_one_or_none()

        if target and target.connection_id:
            # Forward offer to target peer
            await sio.emit('webrtc_offer', {
                'meeting_id': meeting_id,
                'from_peer_id': sender.peer_id,
                'sdp': sdp
            }, room=target.connection_id)

            logger.info(f"Forwarded WebRTC offer from {sender.peer_id} to {target_peer_id}")


@sio.event
async def webrtc_answer(sid, data):
    """
    Handle WebRTC answer (SDP) and forward to target peer.
    Data: { meeting_id: int, target_peer_id: str, sdp: str }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    meeting_id = data.get('meeting_id')
    target_peer_id = data.get('target_peer_id')
    sdp = data.get('sdp')

    if not meeting_id or not target_peer_id or not sdp:
        return

    # Get sender's peer_id and forward answer
    from app.db.session import async_session_maker
    from app.db.models.meeting import MeetingParticipant
    from sqlalchemy import select, and_

    async with async_session_maker() as db:
        stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        sender = result.scalar_one_or_none()

        if not sender or not sender.peer_id:
            return

        # Find target participant
        target_stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.peer_id == target_peer_id
            )
        )
        target_result = await db.execute(target_stmt)
        target = target_result.scalar_one_or_none()

        if target and target.connection_id:
            # Forward answer to target peer
            await sio.emit('webrtc_answer', {
                'meeting_id': meeting_id,
                'from_peer_id': sender.peer_id,
                'sdp': sdp
            }, room=target.connection_id)

            logger.info(f"Forwarded WebRTC answer from {sender.peer_id} to {target_peer_id}")


@sio.event
async def ice_candidate(sid, data):
    """
    Handle ICE candidate and forward to target peer.
    Data: { meeting_id: int, target_peer_id: str, candidate: str, sdpMid: str, sdpMLineIndex: int }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    meeting_id = data.get('meeting_id')
    target_peer_id = data.get('target_peer_id')
    candidate = data.get('candidate')

    if not meeting_id or not target_peer_id or not candidate:
        return

    # Get sender's peer_id and forward ICE candidate
    from app.db.session import async_session_maker
    from app.db.models.meeting import MeetingParticipant
    from sqlalchemy import select, and_

    async with async_session_maker() as db:
        stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        sender = result.scalar_one_or_none()

        if not sender or not sender.peer_id:
            return

        # Find target participant
        target_stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.peer_id == target_peer_id
            )
        )
        target_result = await db.execute(target_stmt)
        target = target_result.scalar_one_or_none()

        if target and target.connection_id:
            # Forward ICE candidate to target peer
            await sio.emit('ice_candidate', {
                'meeting_id': meeting_id,
                'from_peer_id': sender.peer_id,
                'candidate': candidate,
                'sdpMid': data.get('sdpMid'),
                'sdpMLineIndex': data.get('sdpMLineIndex')
            }, room=target.connection_id)

            logger.info(f"Forwarded ICE candidate from {sender.peer_id} to {target_peer_id}")


@sio.event
async def participant_state_changed(sid, data):
    """
    Broadcast participant media state changes (mute/unmute, video on/off, screen share, hand raised).
    Data: {
        meeting_id: int,
        is_audio_enabled: bool (optional),
        is_video_enabled: bool (optional),
        is_screen_sharing: bool (optional),
        is_hand_raised: bool (optional)
    }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    meeting_id = data.get('meeting_id')
    if not meeting_id:
        return

    # Update participant state in database
    from app.db.session import async_session_maker
    from app.db.models.meeting import MeetingParticipant
    from sqlalchemy import select, and_

    async with async_session_maker() as db:
        stmt = select(MeetingParticipant).where(
            and_(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        participant = result.scalar_one_or_none()

        if participant:
            # Update fields if provided
            if 'is_audio_enabled' in data:
                participant.is_audio_enabled = data['is_audio_enabled']
            if 'is_video_enabled' in data:
                participant.is_video_enabled = data['is_video_enabled']
            if 'is_screen_sharing' in data:
                participant.is_screen_sharing = data['is_screen_sharing']
            if 'is_hand_raised' in data:
                participant.is_hand_raised = data['is_hand_raised']

            await db.commit()

            # Broadcast state change to all participants
            await broadcast_participant_state_changed(meeting_id, user_id, {
                'peer_id': participant.peer_id,
                'is_audio_enabled': participant.is_audio_enabled,
                'is_video_enabled': participant.is_video_enabled,
                'is_screen_sharing': participant.is_screen_sharing,
                'is_hand_raised': participant.is_hand_raised,
            }, skip_sid=sid)


@sio.event
async def meeting_chat_message(sid, data):
    """
    Broadcast meeting chat message to all participants.
    Data: { meeting_id: int, message: str, is_private: bool, recipient_id: int (optional) }
    """
    user_id = connection_manager.get_user_id(sid)
    if not user_id:
        return

    meeting_id = data.get('meeting_id')
    message = data.get('message')
    is_private = data.get('is_private', False)
    recipient_id = data.get('recipient_id')

    if not meeting_id or not message:
        return

    if is_private and recipient_id:
        # Send to specific recipient
        recipient_sids = connection_manager.get_user_sids(recipient_id)
        for recipient_sid in recipient_sids:
            await sio.emit('meeting_chat_message', {
                'meeting_id': meeting_id,
                'from_user_id': user_id,
                'message': message,
                'is_private': True,
                'timestamp': datetime.utcnow().isoformat()
            }, room=recipient_sid)
    else:
        # Broadcast to all participants
        await broadcast_meeting_chat_message(meeting_id, {
            'from_user_id': user_id,
            'message': message,
            'is_private': False,
            'timestamp': datetime.utcnow().isoformat()
        }, skip_sid=sid)


# ============================================
# Meeting Broadcast Helper Functions
# ============================================

async def broadcast_meeting_participant_joined(meeting_id: int, user_id: int, peer_id: str, skip_sid: str = None):
    """
    Broadcast participant joined event to all participants in meeting.
    """
    room_name = f"meeting_{meeting_id}"
    await sio.emit('participant_joined', {
        'meeting_id': meeting_id,
        'user_id': user_id,
        'peer_id': peer_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name, skip_sid=skip_sid)
    logger.info(f"Broadcasted participant_joined for user {user_id} in meeting {meeting_id}")


async def broadcast_meeting_participant_left(meeting_id: int, user_id: int):
    """
    Broadcast participant left event to all participants in meeting.
    """
    room_name = f"meeting_{meeting_id}"
    await sio.emit('participant_left', {
        'meeting_id': meeting_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name)
    logger.info(f"Broadcasted participant_left for user {user_id} in meeting {meeting_id}")


async def broadcast_participant_state_changed(meeting_id: int, user_id: int, state: dict, skip_sid: str = None):
    """
    Broadcast participant state changes to all participants.
    """
    room_name = f"meeting_{meeting_id}"
    await sio.emit('participant_state_changed', {
        'meeting_id': meeting_id,
        'user_id': user_id,
        **state,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_name, skip_sid=skip_sid)
    logger.info(f"Broadcasted state change for user {user_id} in meeting {meeting_id}")


async def broadcast_meeting_chat_message(meeting_id: int, message_data: dict, skip_sid: str = None):
    """
    Broadcast meeting chat message to all participants.
    """
    room_name = f"meeting_{meeting_id}"
    await sio.emit('meeting_chat_message', message_data, room=room_name, skip_sid=skip_sid)
    logger.info(f"Broadcasted chat message in meeting {meeting_id}")
