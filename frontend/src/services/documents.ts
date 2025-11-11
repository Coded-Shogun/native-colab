/**
 * Documents API Service
 * Handle document management API calls
 */

import api from '../lib/api';
import type { Document } from '../types';

export const documentsService = {
  /**
   * Get documents for workspace
   */
  async getDocuments(params: {
    workspace_id: number;
    folder_id?: number;
    search?: string;
  }): Promise<Document[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    return api.get<Document[]>(`/documents?${queryParams.toString()}`);
  },

  /**
   * Get single document
   */
  async getDocument(documentId: number): Promise<Document> {
    return api.get<Document>(`/documents/${documentId}`);
  },

  /**
   * Upload document
   */
  async uploadDocument(
    workspaceId: number,
    file: File,
    folderId?: number
  ): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('workspace_id', String(workspaceId));
    if (folderId) {
      formData.append('folder_id', String(folderId));
    }

    return api.post<Document>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Update document
   */
  async updateDocument(
    documentId: number,
    data: { name?: string; folder_id?: number }
  ): Promise<Document> {
    return api.patch<Document>(`/documents/${documentId}`, data);
  },

  /**
   * Delete document
   */
  async deleteDocument(documentId: number): Promise<void> {
    return api.delete(`/documents/${documentId}`);
  },

  /**
   * Download document
   */
  async downloadDocument(documentId: number): Promise<Blob> {
    return api.download(`/documents/${documentId}/download`);
  },

  /**
   * Get document versions
   */
  async getVersions(documentId: number): Promise<any[]> {
    return api.get(`/documents/${documentId}/versions`);
  },

  /**
   * Share document
   */
  async shareDocument(
    documentId: number,
    data: {
      user_id?: number;
      permission: 'view' | 'edit';
    }
  ): Promise<void> {
    return api.post(`/documents/${documentId}/share`, data);
  },

  /**
   * Get folders
   */
  async getFolders(workspaceId: number): Promise<any[]> {
    return api.get(`/workspaces/${workspaceId}/folders`);
  },

  /**
   * Create folder
   */
  async createFolder(data: {
    workspace_id: number;
    name: string;
    parent_id?: number;
  }): Promise<any> {
    return api.post('/folders', data);
  },
};

export default documentsService;
