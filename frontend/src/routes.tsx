/**
 * Router Configuration
 * Using TanStack Router for type-safe routing
 */

import { Router, Route, RootRoute, Outlet } from '@tanstack/react-router';
import { useAuth } from './contexts/AuthContext';
import DashboardLayout from './components/DashboardLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';

// Root Route
const rootRoute = new RootRoute({
  component: () => <Outlet />,
});

// Public Routes
const loginRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: Login,
});

const registerRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/register',
  component: Register,
});

// Protected Routes Wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    window.location.href = '/login';
    return null;
  }

  return <DashboardLayout>{children}</DashboardLayout>;
}

// Dashboard Route
const dashboardRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: () => (
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  ),
});

// Index Route (redirect to dashboard)
const indexRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => {
    const { isAuthenticated } = useAuth();

    React.useEffect(() => {
      if (isAuthenticated) {
        window.location.href = '/dashboard';
      } else {
        window.location.href = '/login';
      }
    }, [isAuthenticated]);

    return null;
  },
});

// Placeholder routes for other pages
const projectsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/projects',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Projects</h1>
        <p className="mt-2 text-slate-600">Projects page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

const tasksRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/tasks',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Tasks</h1>
        <p className="mt-2 text-slate-600">Tasks page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

const chatRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/chat',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Chat</h1>
        <p className="mt-2 text-slate-600">Chat page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

const calendarRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/calendar',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Calendar</h1>
        <p className="mt-2 text-slate-600">Calendar page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

const documentsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/documents',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Documents</h1>
        <p className="mt-2 text-slate-600">Documents page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

const timeRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/time',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Time Tracking</h1>
        <p className="mt-2 text-slate-600">Time tracking page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

const meetingsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/meetings',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Meetings</h1>
        <p className="mt-2 text-slate-600">Meetings page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

const whiteboardsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/whiteboards',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Whiteboards</h1>
        <p className="mt-2 text-slate-600">Whiteboards page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

const searchRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/search',
  component: () => (
    <ProtectedRoute>
      <div className="p-6">
        <h1 className="text-3xl font-bold">Search</h1>
        <p className="mt-2 text-slate-600">Search page coming soon...</p>
      </div>
    </ProtectedRoute>
  ),
});

// Route Tree
const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  registerRoute,
  dashboardRoute,
  projectsRoute,
  tasksRoute,
  chatRoute,
  calendarRoute,
  documentsRoute,
  timeRoute,
  meetingsRoute,
  whiteboardsRoute,
  searchRoute,
]);

// Create Router
export const router = new Router({ routeTree });

// Type declaration for TypeScript
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
