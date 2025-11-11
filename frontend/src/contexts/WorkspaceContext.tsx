/**
 * Workspace Context
 * Manages current workspace selection
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Workspace } from '../types';

interface WorkspaceContextType {
  currentWorkspace: Workspace | null;
  setCurrentWorkspace: (workspace: Workspace | null) => void;
  workspaces: Workspace[];
  setWorkspaces: (workspaces: Workspace[]) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

interface WorkspaceProviderProps {
  children: ReactNode;
}

export function WorkspaceProvider({ children }: WorkspaceProviderProps) {
  const [currentWorkspace, setCurrentWorkspaceState] = useState<Workspace | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);

  // Load workspace from localStorage on mount
  useEffect(() => {
    const savedWorkspaceId = localStorage.getItem('current_workspace_id');
    if (savedWorkspaceId && workspaces.length > 0) {
      const workspace = workspaces.find((w) => w.id === parseInt(savedWorkspaceId));
      if (workspace) {
        setCurrentWorkspaceState(workspace);
      }
    }
  }, [workspaces]);

  const setCurrentWorkspace = (workspace: Workspace | null) => {
    setCurrentWorkspaceState(workspace);
    if (workspace) {
      localStorage.setItem('current_workspace_id', workspace.id.toString());
    } else {
      localStorage.removeItem('current_workspace_id');
    }
  };

  const value: WorkspaceContextType = {
    currentWorkspace,
    setCurrentWorkspace,
    workspaces,
    setWorkspaces,
  };

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

/**
 * Hook to use workspace context
 */
export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}

export default WorkspaceContext;
