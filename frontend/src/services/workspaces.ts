/**
 * Workspace API Service
 * Handle workspace-related API calls
 */

import api from '../lib/api';
import type { Workspace, WorkspaceMember } from '../types';

export const workspaceService = {
  /**
   * Get all workspaces for current user
   */
  async getMyWorkspaces(): Promise<Workspace[]> {
    return api.get<Workspace[]>('/workspaces/me');
  },

  /**
   * Get workspace by ID
   */
  async getWorkspace(workspaceId: number): Promise<Workspace> {
    return api.get<Workspace>(`/workspaces/${workspaceId}`);
  },

  /**
   * Create a new workspace
   */
  async createWorkspace(data: {
    name: string;
    slug: string;
    description?: string;
  }): Promise<Workspace> {
    return api.post<Workspace>('/workspaces', data);
  },

  /**
   * Update workspace
   */
  async updateWorkspace(
    workspaceId: number,
    data: Partial<Workspace>
  ): Promise<Workspace> {
    return api.patch<Workspace>(`/workspaces/${workspaceId}`, data);
  },

  /**
   * Get workspace members
   */
  async getMembers(workspaceId: number): Promise<WorkspaceMember[]> {
    return api.get<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`);
  },

  /**
   * Invite user to workspace
   */
  async inviteMember(
    workspaceId: number,
    data: { email: string; role: string }
  ): Promise<WorkspaceMember> {
    return api.post<WorkspaceMember>(
      `/workspaces/${workspaceId}/members/invite`,
      data
    );
  },
};

export default workspaceService;
