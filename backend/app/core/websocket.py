"""
WebSocket Manager
Real-time communication using Socket.io
"""

import socketio
from typing import Dict, Set, Optional
from fastapi import HTTPException
from app.core.config import settings
from app.core.security import verify_token

# Create Socket.io server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=True,
    engineio_logger=True
)

# Store connected clients
# Format: {user_id: {sid1, sid2, ...}}
connected_users: Dict[int, Set[str]] = {}

# Store user's current workspace
# Format: {sid: workspace_id}
user_workspaces: Dict[str, int] = {}


async def authenticate_socket(sid: str, data: dict) -> Optional[int]:
    """Authenticate socket connection with JWT token"""
    token = data.get('token')
    if not token:
        await sio.emit('error', {'message': 'Authentication required'}, room=sid)
        await sio.disconnect(sid)
        return None

    try:
        payload = verify_token(token)
        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        return int(user_id)
    except Exception as e:
        await sio.emit('error', {'message': 'Authentication failed'}, room=sid)
        await sio.disconnect(sid)
        return None


@sio.event
async def connect(sid: str, environ: dict, auth: dict):
    """Handle client connection"""
    print(f"Client connected: {sid}")

    # Authenticate user
    user_id = await authenticate_socket(sid, auth)
    if not user_id:
        return False

    # Track connected user
    if user_id not in connected_users:
        connected_users[user_id] = set()
    connected_users[user_id].add(sid)

    # Send connection success
    await sio.emit('connected', {'message': 'Connected successfully'}, room=sid)

    return True


@sio.event
async def disconnect(sid: str):
    """Handle client disconnection"""
    print(f"Client disconnected: {sid}")

    # Remove from connected users
    for user_id, sids in connected_users.items():
        if sid in sids:
            sids.remove(sid)
            if not sids:
                del connected_users[user_id]
            break

    # Remove from workspace tracking
    if sid in user_workspaces:
        del user_workspaces[sid]


@sio.event
async def join_workspace(sid: str, data: dict):
    """Join a workspace room"""
    workspace_id = data.get('workspace_id')
    if not workspace_id:
        return {'error': 'workspace_id required'}

    room_name = f"workspace_{workspace_id}"
    await sio.enter_room(sid, room_name)
    user_workspaces[sid] = workspace_id

    print(f"Client {sid} joined workspace {workspace_id}")
    return {'success': True, 'workspace_id': workspace_id}


@sio.event
async def leave_workspace(sid: str, data: dict):
    """Leave a workspace room"""
    workspace_id = data.get('workspace_id')
    if not workspace_id:
        return {'error': 'workspace_id required'}

    room_name = f"workspace_{workspace_id}"
    await sio.leave_room(sid, room_name)

    if sid in user_workspaces:
        del user_workspaces[sid]

    print(f"Client {sid} left workspace {workspace_id}")
    return {'success': True}


@sio.event
async def join_channel(sid: str, data: dict):
    """Join a chat channel"""
    channel_id = data.get('channel_id')
    if not channel_id:
        return {'error': 'channel_id required'}

    room_name = f"channel_{channel_id}"
    await sio.enter_room(sid, room_name)

    print(f"Client {sid} joined channel {channel_id}")
    return {'success': True, 'channel_id': channel_id}


@sio.event
async def leave_channel(sid: str, data: dict):
    """Leave a chat channel"""
    channel_id = data.get('channel_id')
    if not channel_id:
        return {'error': 'channel_id required'}

    room_name = f"channel_{channel_id}"
    await sio.leave_room(sid, room_name)

    print(f"Client {sid} left channel {channel_id}")
    return {'success': True}


@sio.event
async def send_message(sid: str, data: dict):
    """Send a chat message"""
    channel_id = data.get('channel_id')
    message = data.get('message')

    if not channel_id or not message:
        return {'error': 'channel_id and message required'}

    # Broadcast to channel
    room_name = f"channel_{channel_id}"
    await sio.emit('new_message', {
        'channel_id': channel_id,
        'message': message,
        'sender_id': data.get('sender_id'),
        'timestamp': data.get('timestamp')
    }, room=room_name, skip_sid=sid)

    return {'success': True}


@sio.event
async def typing_start(sid: str, data: dict):
    """User started typing"""
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')

    if not channel_id:
        return {'error': 'channel_id required'}

    room_name = f"channel_{channel_id}"
    await sio.emit('user_typing', {
        'channel_id': channel_id,
        'user_id': user_id,
        'typing': True
    }, room=room_name, skip_sid=sid)


@sio.event
async def typing_stop(sid: str, data: dict):
    """User stopped typing"""
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')

    if not channel_id:
        return {'error': 'channel_id required'}

    room_name = f"channel_{channel_id}"
    await sio.emit('user_typing', {
        'channel_id': channel_id,
        'user_id': user_id,
        'typing': False
    }, room=room_name, skip_sid=sid)


# Helper functions for emitting events from API routes

async def emit_notification(user_id: int, notification: dict):
    """Send notification to a specific user"""
    if user_id in connected_users:
        for sid in connected_users[user_id]:
            await sio.emit('notification', notification, room=sid)


async def emit_to_workspace(workspace_id: int, event: str, data: dict):
    """Emit event to all users in a workspace"""
    room_name = f"workspace_{workspace_id}"
    await sio.emit(event, data, room=room_name)


async def emit_to_channel(channel_id: int, event: str, data: dict):
    """Emit event to all users in a channel"""
    room_name = f"channel_{channel_id}"
    await sio.emit(event, data, room=room_name)


async def broadcast_user_status(user_id: int, status: str):
    """Broadcast user online/offline status"""
    await sio.emit('user_status', {
        'user_id': user_id,
        'status': status,
        'timestamp': None  # Add timestamp
    })


def get_online_users() -> Set[int]:
    """Get set of currently online user IDs"""
    return set(connected_users.keys())


def is_user_online(user_id: int) -> bool:
    """Check if a user is currently online"""
    return user_id in connected_users
