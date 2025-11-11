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
