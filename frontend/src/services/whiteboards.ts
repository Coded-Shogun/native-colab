/**
 * Whiteboards API Service
 * Handle whiteboard and collaborative drawing API calls
 */

import api from '../lib/api';
import type { Whiteboard } from '../types';

export const whiteboardsService = {
  /**
   * Get whiteboards for workspace
   */
  async getWhiteboards(params: {
    workspace_id: number;
    project_id?: number;
  }): Promise<Whiteboard[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    return api.get<Whiteboard[]>(`/whiteboards?${queryParams.toString()}`);
  },

  /**
   * Get single whiteboard
   */
  async getWhiteboard(whiteboardId: number): Promise<Whiteboard> {
    return api.get<Whiteboard>(`/whiteboards/${whiteboardId}`);
  },

  /**
   * Create whiteboard
   */
  async createWhiteboard(data: {
    workspace_id: number;
    name: string;
    description?: string;
    project_id?: number;
    canvas_data?: any;
  }): Promise<Whiteboard> {
    return api.post<Whiteboard>('/whiteboards', data);
  },

  /**
   * Update whiteboard
   */
  async updateWhiteboard(
    whiteboardId: number,
    data: {
      name?: string;
      description?: string;
      canvas_data?: any;
    }
  ): Promise<Whiteboard> {
    return api.patch<Whiteboard>(`/whiteboards/${whiteboardId}`, data);
  },

  /**
   * Delete whiteboard
   */
  async deleteWhiteboard(whiteboardId: number): Promise<void> {
    return api.delete(`/whiteboards/${whiteboardId}`);
  },

  /**
   * Save canvas data
   */
  async saveCanvas(whiteboardId: number, canvasData: any): Promise<void> {
    return api.post(`/whiteboards/${whiteboardId}/save`, { canvas_data: canvasData });
  },

  /**
   * Get whiteboard collaborators
   */
  async getCollaborators(whiteboardId: number): Promise<any[]> {
    return api.get(`/whiteboards/${whiteboardId}/collaborators`);
  },

  /**
   * Share whiteboard
   */
  async shareWhiteboard(
    whiteboardId: number,
    data: {
      user_id: number;
      permission: 'view' | 'edit';
    }
  ): Promise<void> {
    return api.post(`/whiteboards/${whiteboardId}/share`, data);
  },

  /**
   * Export whiteboard as image
   */
  async exportWhiteboard(whiteboardId: number, format: 'png' | 'jpg' | 'svg'): Promise<Blob> {
    return api.download(`/whiteboards/${whiteboardId}/export?format=${format}`);
  },
};

export default whiteboardsService;
