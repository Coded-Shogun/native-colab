/**
 * Socket.io Context
 * Real-time communication for chat, notifications, and presence
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './AuthContext';
import { logger } from '../lib/logger';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  joinWorkspace: (workspaceId: number) => void;
  leaveWorkspace: (workspaceId: number) => void;
  joinChannel: (channelId: number) => void;
  leaveChannel: (channelId: number) => void;
  sendMessage: (channelId: number, message: any) => void;
  onNewMessage: (callback: (message: any) => void) => () => void;
  onNotification: (callback: (notification: any) => void) => () => void;
  onUserTyping: (callback: (data: any) => void) => () => void;
  startTyping: (channelId: number, userId: number) => void;
  stopTyping: (channelId: number, userId: number) => void;
  // WebRTC methods
  joinMeeting: (meetingId: string, userId: number) => void;
  leaveMeeting: (meetingId: string, userId: number) => void;
  sendWebRTCOffer: (targetSid: string, offer: RTCSessionDescriptionInit, meetingId: string) => void;
  sendWebRTCAnswer: (targetSid: string, answer: RTCSessionDescriptionInit, meetingId: string) => void;
  sendICECandidate: (targetSid: string, candidate: RTCIceCandidateInit, meetingId: string) => void;
  onUserJoinedMeeting: (callback: (data: any) => void) => () => void;
  onUserLeftMeeting: (callback: (data: any) => void) => () => void;
  onWebRTCOffer: (callback: (data: any) => void) => () => void;
  onWebRTCAnswer: (callback: (data: any) => void) => () => void;
  onICECandidate: (callback: (data: any) => void) => () => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export function SocketProvider({ children }: { children: ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated || !user) {
      // Disconnect socket if user logs out
      if (socket) {
        socket.disconnect();
        setSocket(null);
        setIsConnected(false);
      }
      return;
    }

    // Get token from localStorage
    const token = localStorage.getItem('access_token');
    if (!token) return;

    // Initialize Socket.io connection
    const socketUrl = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000';

    const newSocket = io(socketUrl, {
      path: '/ws/socket.io',
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: Number(import.meta.env.VITE_SOCKET_RECONNECTION_ATTEMPTS) || 5,
    });

    // Connection event handlers
    newSocket.on('connect', () => {
      logger.info('Socket.io connected', { socketId: newSocket.id });
      setIsConnected(true);
    });

    newSocket.on('disconnect', (reason) => {
      logger.warn('Socket.io disconnected', { reason });
      setIsConnected(false);
    });

    newSocket.on('connect_error', (error) => {
      logger.error('Socket.io connection error', error);
      setIsConnected(false);
    });

    newSocket.on('connected', (data) => {
      logger.info('Socket.io authenticated', data);
    });

    newSocket.on('error', (error) => {
      logger.error('Socket.io error', error);
    });

    setSocket(newSocket);

    // Cleanup on unmount
    return () => {
      newSocket.disconnect();
    };
  }, [isAuthenticated, user]);

  // Join workspace room
  const joinWorkspace = (workspaceId: number) => {
    if (socket && isConnected) {
      socket.emit('join_workspace', { workspace_id: workspaceId }, (response: any) => {
        if (response?.success) {
          logger.info('Joined workspace', { workspaceId });
        }
      });
    }
  };

  // Leave workspace room
  const leaveWorkspace = (workspaceId: number) => {
    if (socket && isConnected) {
      socket.emit('leave_workspace', { workspace_id: workspaceId }, (response: any) => {
        if (response?.success) {
          logger.info('Left workspace', { workspaceId });
        }
      });
    }
  };

  // Join channel room
  const joinChannel = (channelId: number) => {
    if (socket && isConnected) {
      socket.emit('join_channel', { channel_id: channelId }, (response: any) => {
        if (response?.success) {
          logger.info('Joined channel', { channelId });
        }
      });
    }
  };

  // Leave channel room
  const leaveChannel = (channelId: number) => {
    if (socket && isConnected) {
      socket.emit('leave_channel', { channel_id: channelId }, (response: any) => {
        if (response?.success) {
          logger.info('Left channel', { channelId });
        }
      });
    }
  };

  // Send message to channel
  const sendMessage = (channelId: number, message: any) => {
    if (socket && isConnected) {
      socket.emit('send_message', {
        channel_id: channelId,
        message: message.content,
        sender_id: user?.id,
        timestamp: new Date().toISOString(),
      });
    }
  };

  // Listen for new messages
  const onNewMessage = (callback: (message: any) => void) => {
    if (!socket) return () => {};

    socket.on('new_message', callback);

    // Return cleanup function
    return () => {
      socket.off('new_message', callback);
    };
  };

  // Listen for notifications
  const onNotification = (callback: (notification: any) => void) => {
    if (!socket) return () => {};

    socket.on('notification', callback);

    return () => {
      socket.off('notification', callback);
    };
  };

  // Listen for typing indicators
  const onUserTyping = (callback: (data: any) => void) => {
    if (!socket) return () => {};

    socket.on('user_typing', callback);

    return () => {
      socket.off('user_typing', callback);
    };
  };

  // Emit typing start
  const startTyping = (channelId: number, userId: number) => {
    if (socket && isConnected) {
      socket.emit('typing_start', {
        channel_id: channelId,
        user_id: userId,
      });
    }
  };

  // Emit typing stop
  const stopTyping = (channelId: number, userId: number) => {
    if (socket && isConnected) {
      socket.emit('typing_stop', {
        channel_id: channelId,
        user_id: userId,
      });
    }
  };

  // WebRTC Methods

  // Join meeting room
  const joinMeeting = (meetingId: string, userId: number) => {
    if (socket && isConnected) {
      socket.emit('join_meeting', { meeting_id: meetingId, user_id: userId }, (response: any) => {
        if (response?.success) {
          logger.info('Joined meeting', { meetingId });
        }
      });
    }
  };

  // Leave meeting room
  const leaveMeeting = (meetingId: string, userId: number) => {
    if (socket && isConnected) {
      socket.emit('leave_meeting', { meeting_id: meetingId, user_id: userId }, (response: any) => {
        if (response?.success) {
          logger.info('Left meeting', { meetingId });
        }
      });
    }
  };

  // Send WebRTC offer
  const sendWebRTCOffer = (targetSid: string, offer: RTCSessionDescriptionInit, meetingId: string) => {
    if (socket && isConnected) {
      socket.emit('webrtc_offer', {
        target_sid: targetSid,
        offer,
        meeting_id: meetingId,
      });
    }
  };

  // Send WebRTC answer
  const sendWebRTCAnswer = (targetSid: string, answer: RTCSessionDescriptionInit, meetingId: string) => {
    if (socket && isConnected) {
      socket.emit('webrtc_answer', {
        target_sid: targetSid,
        answer,
        meeting_id: meetingId,
      });
    }
  };

  // Send ICE candidate
  const sendICECandidate = (targetSid: string, candidate: RTCIceCandidateInit, meetingId: string) => {
    if (socket && isConnected) {
      socket.emit('webrtc_ice_candidate', {
        target_sid: targetSid,
        candidate,
        meeting_id: meetingId,
      });
    }
  };

  // Listen for user joined meeting
  const onUserJoinedMeeting = (callback: (data: any) => void) => {
    if (!socket) return () => {};
    socket.on('user_joined_meeting', callback);
    return () => {
      socket.off('user_joined_meeting', callback);
    };
  };

  // Listen for user left meeting
  const onUserLeftMeeting = (callback: (data: any) => void) => {
    if (!socket) return () => {};
    socket.on('user_left_meeting', callback);
    return () => {
      socket.off('user_left_meeting', callback);
    };
  };

  // Listen for WebRTC offer
  const onWebRTCOffer = (callback: (data: any) => void) => {
    if (!socket) return () => {};
    socket.on('webrtc_offer', callback);
    return () => {
      socket.off('webrtc_offer', callback);
    };
  };

  // Listen for WebRTC answer
  const onWebRTCAnswer = (callback: (data: any) => void) => {
    if (!socket) return () => {};
    socket.on('webrtc_answer', callback);
    return () => {
      socket.off('webrtc_answer', callback);
    };
  };

  // Listen for ICE candidate
  const onICECandidate = (callback: (data: any) => void) => {
    if (!socket) return () => {};
    socket.on('webrtc_ice_candidate', callback);
    return () => {
      socket.off('webrtc_ice_candidate', callback);
    };
  };

  const value = {
    socket,
    isConnected,
    joinWorkspace,
    leaveWorkspace,
    joinChannel,
    leaveChannel,
    sendMessage,
    onNewMessage,
    onNotification,
    onUserTyping,
    startTyping,
    stopTyping,
    // WebRTC
    joinMeeting,
    leaveMeeting,
    sendWebRTCOffer,
    sendWebRTCAnswer,
    sendICECandidate,
    onUserJoinedMeeting,
    onUserLeftMeeting,
    onWebRTCOffer,
    onWebRTCAnswer,
    onICECandidate,
  };

  return <SocketContext.Provider value={value}>{children}</SocketContext.Provider>;
}

export function useSocket() {
  const context = useContext(SocketContext);
  if (context === undefined) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
}
