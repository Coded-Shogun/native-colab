"""
Real-time Communication Module
Socket.io integration for Native Colab
"""

import socketio
from app.core.websocket import sio

# Create ASGI application for Socket.io
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='socket.io'
)

# Export socket instance for use in other modules
__all__ = ['socket_app', 'sio']
