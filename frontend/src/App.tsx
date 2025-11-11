/**
 * Native Colab - Main Application
 * Unified Collaboration Platform
 */

import { RouterProvider } from '@tanstack/react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { WorkspaceProvider } from './contexts/WorkspaceContext';
import { router } from './routes';
import './App.css';

// Create a client for TanStack Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WorkspaceProvider>
          <RouterProvider router={router} />
        </WorkspaceProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
