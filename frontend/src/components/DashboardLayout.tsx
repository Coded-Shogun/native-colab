/**
 * Dashboard Layout
 * Main layout with sidebar navigation
 */

import { useState, ReactNode, useRef, useEffect } from 'react';
import { Link } from '@tanstack/react-router';
import { useAuth } from '../contexts/AuthContext';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { useNotifications } from '../contexts/NotificationContext';

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, logout } = useAuth();
  const { currentWorkspace } = useWorkspace();
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const notificationRef = useRef<HTMLDivElement>(null);

  // Close notification dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-40 h-screen transition-transform ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } bg-card border-r border-border w-64`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-border">
          <h1 className="text-xl font-bold text-card-foreground">
            Native Colab
          </h1>
        </div>

        {/* Workspace Selector */}
        {currentWorkspace && (
          <div className="px-4 py-3 border-b border-border">
            <button className="w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-accent transition-colors">
              <div className="flex items-center space-x-3 min-w-0">
                <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center text-white font-semibold text-sm">
                  {currentWorkspace.name[0]}
                </div>
                <span className="text-sm font-medium text-card-foreground truncate">
                  {currentWorkspace.name}
                </span>
              </div>
              <svg
                className="w-4 h-4 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          <NavLink to="/dashboard" icon="🏠" label="Dashboard" />
          <NavLink to="/projects" icon="📋" label="Projects" />
          <NavLink to="/tasks" icon="✓" label="Tasks" />
          <NavLink to="/chat" icon="💬" label="Chat" />
          <NavLink to="/calendar" icon="📅" label="Calendar" />
          <NavLink to="/documents" icon="📄" label="Documents" />
          <NavLink to="/time" icon="⏱️" label="Time Tracking" />
          <NavLink to="/meetings" icon="📹" label="Meetings" />
          <NavLink to="/whiteboards" icon="🎨" label="Whiteboards" />
          <NavLink to="/search" icon="🔍" label="Search" />
        </nav>

        {/* User Menu */}
        <div className="border-t border-border p-4">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white font-semibold">
              {user?.full_name[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-card-foreground truncate">
                {user?.full_name}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.email}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full px-3 py-2 text-sm text-left text-critical hover:bg-critical/10 rounded-md transition-colors"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className={`${isSidebarOpen ? 'ml-64' : 'ml-0'} transition-all`}>
        {/* Top Bar */}
        <header className="h-16 bg-card border-b border-border flex items-center px-6">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-md hover:bg-accent transition-colors mr-4"
          >
            <svg
              className="w-6 h-6 text-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          <div className="flex-1" />

          {/* Top Bar Actions */}
          <div className="flex items-center space-x-4">
            {/* Search */}
            <button className="p-2 rounded-md hover:bg-accent transition-colors">
              <svg
                className="w-5 h-5 text-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>

            {/* Notifications */}
            <div className="relative" ref={notificationRef}>
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-2 rounded-md hover:bg-accent transition-colors relative"
              >
                <svg
                  className="w-5 h-5 text-foreground"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-5 h-5 bg-critical text-white text-xs rounded-full flex items-center justify-center">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-96 bg-card rounded-md shadow-lg border border-border z-50 max-h-[600px] overflow-hidden flex flex-col">
                  {/* Header */}
                  <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-card-foreground">
                      Notifications
                    </h3>
                    {unreadCount > 0 && (
                      <button
                        onClick={markAllAsRead}
                        className="text-xs text-primary hover:underline"
                      >
                        Mark all as read
                      </button>
                    )}
                  </div>

                  {/* Notification List */}
                  <div className="flex-1 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="px-4 py-8 text-center text-muted-foreground">
                        <svg
                          className="w-12 h-12 mx-auto mb-2 text-accent"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                          />
                        </svg>
                        <p className="text-sm">No notifications yet</p>
                      </div>
                    ) : (
                      notifications.slice(0, 10).map((notification) => (
                        <button
                          key={notification.id}
                          onClick={() => {
                            markAsRead(notification.id);
                            if (notification.link) {
                              window.location.href = notification.link;
                            }
                          }}
                          className={`w-full px-4 py-3 border-b border-border hover:bg-accent/50 transition-colors text-left ${
                            !notification.read ? 'bg-accent/50' : ''
                          }`}
                        >
                          <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0 text-2xl">
                              {notification.type === 'message' && '💬'}
                              {notification.type === 'mention' && '📣'}
                              {notification.type === 'task' && '✅'}
                              {notification.type === 'project' && '📁'}
                              {notification.type === 'meeting' && '📞'}
                              {notification.type === 'document' && '📄'}
                              {notification.type === 'system' && '⚙️'}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-card-foreground">
                                {notification.title}
                              </p>
                              <p className="text-sm text-foreground mt-0.5">
                                {notification.message}
                              </p>
                              <p className="text-xs text-muted-foreground mt-1">
                                {new Date(notification.created_at).toLocaleString()}
                              </p>
                            </div>
                            {!notification.read && (
                              <div className="flex-shrink-0">
                                <div className="w-2 h-2 bg-primary rounded-full" />
                              </div>
                            )}
                          </div>
                        </button>
                      ))
                    )}
                  </div>

                  {/* Footer */}
                  {notifications.length > 0 && (
                    <div className="px-4 py-3 border-t border-border">
                      <Link
                        to="/notifications"
                        className="text-sm text-primary hover:underline"
                      >
                        View all notifications
                      </Link>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
      </div>
    </div>
  );
}

interface NavLinkProps {
  to: string;
  icon: string;
  label: string;
}

function NavLink({ to, icon, label }: NavLinkProps) {
  // This is a simplified version - you'd use the router's Link component with active state
  return (
    <Link
      to={to}
      className="flex items-center space-x-3 px-3 py-2 rounded-md hover:bg-accent transition-colors group"
    >
      <span className="text-xl">{icon}</span>
      <span className="text-sm font-medium text-foreground group-hover:text-card-foreground">
        {label}
      </span>
    </Link>
  );
}
