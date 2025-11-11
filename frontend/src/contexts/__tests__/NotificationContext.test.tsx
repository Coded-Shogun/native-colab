/**
 * Notification Context Tests
 * Unit tests for notification management and real-time notifications
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { NotificationProvider, useNotifications } from '../NotificationContext';
import type { Notification } from '../NotificationContext';

// Mock SocketContext
vi.mock('../SocketContext', () => ({
  useSocket: () => ({
    socket: { id: 'test-socket-id' },
    isConnected: true,
    onNotification: (callback: (notification: Notification) => void) => {
      // Store callback for testing
      (window as any).testNotificationCallback = callback;
      return () => {
        delete (window as any).testNotificationCallback;
      };
    },
  }),
}));

// Mock AuthContext
vi.mock('../AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, full_name: 'Test User', email: 'test@example.com' },
    isAuthenticated: true,
    isLoading: false,
  }),
}));

// Mock logger
vi.mock('../../lib/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock browser Notification API
beforeEach(() => {
  (global as any).Notification = {
    permission: 'granted',
    requestPermission: vi.fn().mockResolvedValue('granted'),
  };
});

describe('NotificationContext', () => {
  describe('useNotifications Hook', () => {
    it('should throw error when used outside NotificationProvider', () => {
      expect(() => {
        renderHook(() => useNotifications());
      }).toThrow('useNotifications must be used within a NotificationProvider');
    });

    it('should provide notification context when used within provider', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      expect(result.current).toBeDefined();
      expect(result.current).toHaveProperty('notifications');
      expect(result.current).toHaveProperty('unreadCount');
      expect(result.current).toHaveProperty('markAsRead');
      expect(result.current).toHaveProperty('markAllAsRead');
      expect(result.current).toHaveProperty('clearAll');
    });
  });

  describe('Notification State', () => {
    it('should initialize with empty notifications', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      expect(result.current.notifications).toEqual([]);
      expect(result.current.unreadCount).toBe(0);
    });

    it('should track unread count correctly', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      // Simulate receiving a notification
      act(() => {
        const testNotification: Notification = {
          id: 1,
          type: 'message',
          title: 'New Message',
          message: 'You have a new message',
          read: false,
          created_at: new Date().toISOString(),
        };

        (window as any).testNotificationCallback?.(testNotification);
      });

      await waitFor(() => {
        expect(result.current.notifications.length).toBe(1);
        expect(result.current.unreadCount).toBe(1);
      });
    });
  });

  describe('Mark as Read', () => {
    it('should mark single notification as read', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      // Add a notification
      act(() => {
        const testNotification: Notification = {
          id: 1,
          type: 'message',
          title: 'Test',
          message: 'Test message',
          read: false,
          created_at: new Date().toISOString(),
        };
        (window as any).testNotificationCallback?.(testNotification);
      });

      await waitFor(() => {
        expect(result.current.unreadCount).toBe(1);
      });

      // Mark as read
      act(() => {
        result.current.markAsRead(1);
      });

      await waitFor(() => {
        expect(result.current.unreadCount).toBe(0);
        expect(result.current.notifications[0].read).toBe(true);
      });
    });

    it('should mark all notifications as read', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      // Add multiple notifications
      act(() => {
        [1, 2, 3].forEach((id) => {
          const testNotification: Notification = {
            id,
            type: 'message',
            title: `Test ${id}`,
            message: `Test message ${id}`,
            read: false,
            created_at: new Date().toISOString(),
          };
          (window as any).testNotificationCallback?.(testNotification);
        });
      });

      await waitFor(() => {
        expect(result.current.unreadCount).toBe(3);
      });

      // Mark all as read
      act(() => {
        result.current.markAllAsRead();
      });

      await waitFor(() => {
        expect(result.current.unreadCount).toBe(0);
        expect(result.current.notifications.every((n) => n.read)).toBe(true);
      });
    });
  });

  describe('Clear Notifications', () => {
    it('should clear all notifications', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      // Add notifications
      act(() => {
        [1, 2, 3].forEach((id) => {
          const testNotification: Notification = {
            id,
            type: 'message',
            title: `Test ${id}`,
            message: `Test message ${id}`,
            read: false,
            created_at: new Date().toISOString(),
          };
          (window as any).testNotificationCallback?.(testNotification);
        });
      });

      await waitFor(() => {
        expect(result.current.notifications.length).toBe(3);
      });

      // Clear all
      act(() => {
        result.current.clearAll();
      });

      await waitFor(() => {
        expect(result.current.notifications.length).toBe(0);
        expect(result.current.unreadCount).toBe(0);
      });
    });
  });

  describe('Notification Types', () => {
    it('should handle message notifications', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      act(() => {
        const testNotification: Notification = {
          id: 1,
          type: 'message',
          title: 'New Message',
          message: 'You have a new message',
          read: false,
          created_at: new Date().toISOString(),
        };
        (window as any).testNotificationCallback?.(testNotification);
      });

      await waitFor(() => {
        expect(result.current.notifications[0].type).toBe('message');
      });
    });

    it('should handle task notifications', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      act(() => {
        const testNotification: Notification = {
          id: 1,
          type: 'task',
          title: 'Task Assigned',
          message: 'You have been assigned a new task',
          read: false,
          created_at: new Date().toISOString(),
        };
        (window as any).testNotificationCallback?.(testNotification);
      });

      await waitFor(() => {
        expect(result.current.notifications[0].type).toBe('task');
      });
    });

    it('should handle meeting notifications', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      act(() => {
        const testNotification: Notification = {
          id: 1,
          type: 'meeting',
          title: 'Meeting Starting',
          message: 'Your meeting is starting in 5 minutes',
          read: false,
          created_at: new Date().toISOString(),
        };
        (window as any).testNotificationCallback?.(testNotification);
      });

      await waitFor(() => {
        expect(result.current.notifications[0].type).toBe('meeting');
      });
    });
  });

  describe('Notification with Sender', () => {
    it('should store sender information', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <NotificationProvider>{children}</NotificationProvider>
      );

      const { result } = renderHook(() => useNotifications(), { wrapper });

      act(() => {
        const testNotification: Notification = {
          id: 1,
          type: 'mention',
          title: 'You were mentioned',
          message: 'John mentioned you in a comment',
          read: false,
          created_at: new Date().toISOString(),
          sender: {
            id: 2,
            full_name: 'John Doe',
            email: 'john@example.com',
          },
        };
        (window as any).testNotificationCallback?.(testNotification);
      });

      await waitFor(() => {
        expect(result.current.notifications[0].sender).toBeDefined();
        expect(result.current.notifications[0].sender?.full_name).toBe('John Doe');
      });
    });
  });
});
