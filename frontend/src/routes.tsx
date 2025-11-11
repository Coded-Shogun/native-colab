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
import Chat from './pages/Chat';
import Projects from './pages/Projects';
import Tasks from './pages/Tasks';
import TimeTracking from './pages/TimeTracking';
import Calendar from './pages/Calendar';
import Documents from './pages/Documents';
import Meetings from './pages/Meetings';
import Search from './pages/Search';
import Whiteboards from './pages/Whiteboards';

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

// Projects Route
const projectsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/projects',
  component: () => (
    <ProtectedRoute>
      <Projects />
    </ProtectedRoute>
  ),
});

const tasksRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/tasks',
  component: () => (
    <ProtectedRoute>
      <Tasks />
    </ProtectedRoute>
  ),
});

const chatRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/chat',
  component: () => (
    <ProtectedRoute>
      <Chat />
    </ProtectedRoute>
  ),
});

const calendarRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/calendar',
  component: () => (
    <ProtectedRoute>
      <Calendar />
    </ProtectedRoute>
  ),
});

const documentsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/documents',
  component: () => (
    <ProtectedRoute>
      <Documents />
    </ProtectedRoute>
  ),
});

const timeRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/time',
  component: () => (
    <ProtectedRoute>
      <TimeTracking />
    </ProtectedRoute>
  ),
});

const meetingsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/meetings',
  component: () => (
    <ProtectedRoute>
      <Meetings />
    </ProtectedRoute>
  ),
});

const whiteboardsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/whiteboards',
  component: () => (
    <ProtectedRoute>
      <Whiteboards />
    </ProtectedRoute>
  ),
});

const searchRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/search',
  component: () => (
    <ProtectedRoute>
      <Search />
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
