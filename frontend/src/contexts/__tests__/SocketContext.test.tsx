/**
 * Socket Context Tests
 * Unit tests for Socket.io context and real-time features
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, waitFor, renderHook } from '@testing-library/react';
import { SocketProvider, useSocket } from '../SocketContext';
import { AuthProvider } from '../AuthContext';
import { WorkspaceProvider } from '../WorkspaceContext';

// Mock Socket.io client
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    off: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
    id: 'test-socket-id',
  })),
}));

// Mock AuthContext
vi.mock('../AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, full_name: 'Test User', email: 'test@example.com' },
    isAuthenticated: true,
    isLoading: false,
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock WorkspaceProvider
vi.mock('../WorkspaceContext', () => ({
  WorkspaceProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock logger
vi.mock('../../lib/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

describe('SocketContext', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('useSocket Hook', () => {
    it('should throw error when used outside SocketProvider', () => {
      expect(() => {
        renderHook(() => useSocket());
      }).toThrow('useSocket must be used within a SocketProvider');
    });

    it('should provide socket context when used within provider', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current).toBeDefined();
      expect(result.current).toHaveProperty('socket');
      expect(result.current).toHaveProperty('isConnected');
      expect(result.current).toHaveProperty('joinChannel');
      expect(result.current).toHaveProperty('sendMessage');
    });
  });

  describe('Socket Connection', () => {
    it('should initialize socket when authenticated', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      await waitFor(() => {
        expect(result.current.socket).toBeDefined();
      });
    });

    it('should provide connection status', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(typeof result.current.isConnected).toBe('boolean');
    });
  });

  describe('Channel Methods', () => {
    it('should provide joinChannel method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.joinChannel).toBeDefined();
      expect(typeof result.current.joinChannel).toBe('function');
    });

    it('should provide leaveChannel method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.leaveChannel).toBeDefined();
      expect(typeof result.current.leaveChannel).toBe('function');
    });

    it('should provide sendMessage method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.sendMessage).toBeDefined();
      expect(typeof result.current.sendMessage).toBe('function');
    });
  });

  describe('Event Listeners', () => {
    it('should provide onNewMessage listener', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.onNewMessage).toBeDefined();
      expect(typeof result.current.onNewMessage).toBe('function');
    });

    it('should provide onNotification listener', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.onNotification).toBeDefined();
      expect(typeof result.current.onNotification).toBe('function');
    });
  });

  describe('Typing Indicators', () => {
    it('should provide startTyping method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.startTyping).toBeDefined();
      expect(typeof result.current.startTyping).toBe('function');
    });

    it('should provide stopTyping method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.stopTyping).toBeDefined();
      expect(typeof result.current.stopTyping).toBe('function');
    });
  });

  describe('WebRTC Methods', () => {
    it('should provide joinMeeting method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.joinMeeting).toBeDefined();
      expect(typeof result.current.joinMeeting).toBe('function');
    });

    it('should provide leaveMeeting method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.leaveMeeting).toBeDefined();
      expect(typeof result.current.leaveMeeting).toBe('function');
    });

    it('should provide sendWebRTCOffer method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.sendWebRTCOffer).toBeDefined();
      expect(typeof result.current.sendWebRTCOffer).toBe('function');
    });

    it('should provide sendWebRTCAnswer method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.sendWebRTCAnswer).toBeDefined();
      expect(typeof result.current.sendWebRTCAnswer).toBe('function');
    });

    it('should provide sendICECandidate method', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>
          <WorkspaceProvider>
            <SocketProvider>{children}</SocketProvider>
          </WorkspaceProvider>
        </AuthProvider>
      );

      const { result } = renderHook(() => useSocket(), { wrapper });

      expect(result.current.sendICECandidate).toBeDefined();
      expect(typeof result.current.sendICECandidate).toBe('function');
    });
  });
});
