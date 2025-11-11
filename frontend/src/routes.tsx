/**
 * Router Configuration
 * Using TanStack Router for type-safe routing with lazy loading
 */

import { Router, Route, RootRoute, Outlet } from '@tanstack/react-router';
import { lazy, Suspense } from 'react';
import { useAuth } from './contexts/AuthContext';
import DashboardLayout from './components/DashboardLayout';
import { PageLoader } from './components/LoadingSpinner';

// Eager load auth pages for faster initial access
import Login from './pages/Login';
import Register from './pages/Register';

// Lazy load feature pages for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Chat = lazy(() => import('./pages/Chat'));
const Projects = lazy(() => import('./pages/Projects'));
const Tasks = lazy(() => import('./pages/Tasks'));
const TimeTracking = lazy(() => import('./pages/TimeTracking'));
const Calendar = lazy(() => import('./pages/Calendar'));
const Documents = lazy(() => import('./pages/Documents'));
const Meetings = lazy(() => import('./pages/Meetings'));
const Search = lazy(() => import('./pages/Search'));
const Whiteboards = lazy(() => import('./pages/Whiteboards'));

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

// Protected Routes Wrapper with Lazy Loading Support
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <PageLoader message="Loading..." />;
  }

  if (!isAuthenticated) {
    window.location.href = '/login';
    return null;
  }

  return (
    <DashboardLayout>
      <Suspense fallback={<PageLoader message="Loading page..." />}>
        {children}
      </Suspense>
    </DashboardLayout>
  );
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
