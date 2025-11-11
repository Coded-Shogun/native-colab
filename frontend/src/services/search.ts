/**
 * Search API Service
 * Handle universal search API calls
 */

import api from '../lib/api';

export interface SearchResult {
  id: number;
  type: 'project' | 'task' | 'message' | 'document' | 'event' | 'user';
  title: string;
  description?: string;
  snippet?: string;
  url?: string;
  metadata?: Record<string, any>;
  score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  page_size: number;
  facets?: Record<string, any>;
}

export const searchService = {
  /**
   * Universal search across all content
   */
  async search(params: {
    workspace_id: number;
    query: string;
    types?: string[];
    filters?: Record<string, any>;
    page?: number;
    page_size?: number;
  }): Promise<SearchResponse> {
    const queryParams = new URLSearchParams();
    queryParams.append('workspace_id', String(params.workspace_id));
    queryParams.append('query', params.query);

    if (params.types && params.types.length > 0) {
      params.types.forEach(type => queryParams.append('types', type));
    }

    if (params.filters) {
      queryParams.append('filters', JSON.stringify(params.filters));
    }

    if (params.page !== undefined) {
      queryParams.append('page', String(params.page));
    }

    if (params.page_size !== undefined) {
      queryParams.append('page_size', String(params.page_size));
    }

    return api.get<SearchResponse>(`/search?${queryParams.toString()}`);
  },

  /**
   * Search suggestions (autocomplete)
   */
  async getSuggestions(params: {
    workspace_id: number;
    query: string;
    limit?: number;
  }): Promise<string[]> {
    const queryParams = new URLSearchParams();
    queryParams.append('workspace_id', String(params.workspace_id));
    queryParams.append('query', params.query);
    if (params.limit) {
      queryParams.append('limit', String(params.limit));
    }

    return api.get<string[]>(`/search/suggestions?${queryParams.toString()}`);
  },

  /**
   * Get recent searches
   */
  async getRecentSearches(workspaceId: number): Promise<string[]> {
    return api.get<string[]>(`/search/recent?workspace_id=${workspaceId}`);
  },

  /**
   * Clear recent searches
   */
  async clearRecentSearches(workspaceId: number): Promise<void> {
    return api.delete(`/search/recent?workspace_id=${workspaceId}`);
  },

  /**
   * Save search
   */
  async saveSearch(data: {
    workspace_id: number;
    name: string;
    query: string;
    filters?: Record<string, any>;
  }): Promise<any> {
    return api.post('/search/saved', data);
  },

  /**
   * Get saved searches
   */
  async getSavedSearches(workspaceId: number): Promise<any[]> {
    return api.get(`/search/saved?workspace_id=${workspaceId}`);
  },

  /**
   * Delete saved search
   */
  async deleteSavedSearch(searchId: number): Promise<void> {
    return api.delete(`/search/saved/${searchId}`);
  },
};

export default searchService;
