/**
 * Projects API Service
 * Handle project-related API calls
 */

import api from '../lib/api';
import type { Project, Task, PaginatedResponse } from '../types';

export const projectService = {
  /**
   * Get all projects for workspace
   */
  async getProjects(workspaceId: number): Promise<Project[]> {
    return api.get<Project[]>(`/projects?workspace_id=${workspaceId}`);
  },

  /**
   * Get project by ID
   */
  async getProject(projectId: number): Promise<Project> {
    return api.get<Project>(`/projects/${projectId}`);
  },

  /**
   * Create a new project
   */
  async createProject(data: {
    workspace_id: number;
    name: string;
    description?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<Project> {
    return api.post<Project>('/projects', data);
  },

  /**
   * Update project
   */
  async updateProject(
    projectId: number,
    data: Partial<Project>
  ): Promise<Project> {
    return api.patch<Project>(`/projects/${projectId}`, data);
  },

  /**
   * Delete project
   */
  async deleteProject(projectId: number): Promise<void> {
    return api.delete(`/projects/${projectId}`);
  },

  /**
   * Get tasks for project
   */
  async getProjectTasks(projectId: number): Promise<Task[]> {
    return api.get<Task[]>(`/projects/${projectId}/tasks`);
  },
};

export const taskService = {
  /**
   * Get all tasks with filters
   */
  async getTasks(params: {
    workspace_id?: number;
    project_id?: number;
    assigned_to?: number;
    status?: string;
  }): Promise<Task[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    return api.get<Task[]>(`/tasks?${queryParams.toString()}`);
  },

  /**
   * Get task by ID
   */
  async getTask(taskId: number): Promise<Task> {
    return api.get<Task>(`/tasks/${taskId}`);
  },

  /**
   * Create a new task
   */
  async createTask(data: {
    project_id: number;
    title: string;
    description?: string;
    status?: string;
    priority?: string;
    assigned_to?: number;
    due_date?: string;
  }): Promise<Task> {
    return api.post<Task>('/tasks', data);
  },

  /**
   * Update task
   */
  async updateTask(taskId: number, data: Partial<Task>): Promise<Task> {
    return api.patch<Task>(`/tasks/${taskId}`, data);
  },

  /**
   * Delete task
   */
  async deleteTask(taskId: number): Promise<void> {
    return api.delete(`/tasks/${taskId}`);
  },

  /**
   * Complete task
   */
  async completeTask(taskId: number): Promise<Task> {
    return api.post<Task>(`/tasks/${taskId}/complete`);
  },
};

export default projectService;
