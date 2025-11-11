/**
 * Notification Context
 * Real-time notification management with Socket.io
 */

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { useSocket } from './SocketContext';
import { useAuth } from './AuthContext';
import { logger } from '../lib/logger';

export interface Notification {
  id: number;
  type: 'message' | 'mention' | 'task' | 'project' | 'meeting' | 'document' | 'system';
  title: string;
  message: string;
  link?: string;
  read: boolean;
  created_at: string;
  sender?: {
    id: number;
    full_name: string;
    email: string;
  };
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  showToast: (notification: Notification) => void;
  markAsRead: (notificationId: number) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// Toast notification component
function ToastNotification({
  notification,
  onClose
}: {
  notification: Notification;
  onClose: () => void;
}) {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000); // Auto-close after 5 seconds
    return () => clearTimeout(timer);
  }, [onClose]);

  const getIcon = () => {
    switch (notification.type) {
      case 'message':
        return '💬';
      case 'mention':
        return '📣';
      case 'task':
        return '✅';
      case 'project':
        return '📁';
      case 'meeting':
        return '📞';
      case 'document':
        return '📄';
      case 'system':
        return '⚙️';
      default:
        return '🔔';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm w-full bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 p-4 animate-slide-in">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 text-2xl">{getIcon()}</div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-900 dark:text-white">
            {notification.title}
          </p>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            {notification.message}
          </p>
          {notification.sender && (
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
              From {notification.sender.full_name}
            </p>
          )}
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [toastNotification, setToastNotification] = useState<Notification | null>(null);
  const { socket, isConnected, onNotification } = useSocket();
  const { isAuthenticated, user } = useAuth();

  // Listen for real-time notifications
  useEffect(() => {
    if (!isAuthenticated || !isConnected) return;

    logger.info('Setting up notification listener');

    const unsubscribe = onNotification((notification: Notification) => {
      logger.info('Received notification', notification);

      // Add to notifications list
      setNotifications((prev) => [notification, ...prev]);

      // Show toast
      setToastNotification(notification);

      // Play notification sound (optional)
      if ('Notification' in window && Notification.permission === 'granted') {
        try {
          new Notification(notification.title, {
            body: notification.message,
            icon: '/logo.png',
            tag: `notification-${notification.id}`,
          });
        } catch (error) {
          logger.error('Failed to show browser notification', error);
        }
      }
    });

    return () => {
      unsubscribe();
    };
  }, [isAuthenticated, isConnected, onNotification]);

  // Request browser notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then((permission) => {
        logger.info('Notification permission:', permission);
      });
    }
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const showToast = useCallback((notification: Notification) => {
    setToastNotification(notification);
  }, []);

  const markAsRead = useCallback((notificationId: number) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const value = {
    notifications,
    unreadCount,
    showToast,
    markAsRead,
    markAllAsRead,
    clearAll,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      {toastNotification && (
        <ToastNotification
          notification={toastNotification}
          onClose={() => setToastNotification(null)}
        />
      )}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}
