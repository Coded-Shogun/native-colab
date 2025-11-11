/**
 * Time Tracking API Service
 * Handle time entry API calls
 */

import api from '../lib/api';
import type { TimeEntry } from '../types';

export const timeTrackingService = {
  /**
   * Get time entries for workspace
   */
  async getTimeEntries(params: {
    workspace_id: number;
    user_id?: number;
    project_id?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<TimeEntry[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    return api.get<TimeEntry[]>(`/time-entries?${queryParams.toString()}`);
  },

  /**
   * Get active time entry for user
   */
  async getActiveEntry(userId: number): Promise<TimeEntry | null> {
    try {
      return await api.get<TimeEntry>(`/time-entries/active?user_id=${userId}`);
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  /**
   * Start time tracking
   */
  async startTimer(data: {
    workspace_id: number;
    project_id?: number;
    task_id?: number;
    description?: string;
    is_billable?: boolean;
  }): Promise<TimeEntry> {
    return api.post<TimeEntry>('/time-entries/start', data);
  },

  /**
   * Stop active timer
   */
  async stopTimer(entryId: number): Promise<TimeEntry> {
    return api.post<TimeEntry>(`/time-entries/${entryId}/stop`);
  },

  /**
   * Create manual time entry
   */
  async createEntry(data: {
    workspace_id: number;
    project_id?: number;
    task_id?: number;
    description?: string;
    start_time: string;
    end_time: string;
    is_billable?: boolean;
  }): Promise<TimeEntry> {
    return api.post<TimeEntry>('/time-entries', data);
  },

  /**
   * Update time entry
   */
  async updateEntry(
    entryId: number,
    data: Partial<TimeEntry>
  ): Promise<TimeEntry> {
    return api.patch<TimeEntry>(`/time-entries/${entryId}`, data);
  },

  /**
   * Delete time entry
   */
  async deleteEntry(entryId: number): Promise<void> {
    return api.delete(`/time-entries/${entryId}`);
  },

  /**
   * Get total time for period
   */
  async getTotalTime(params: {
    workspace_id: number;
    user_id?: number;
    project_id?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<{ total_seconds: number; billable_seconds: number }> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    return api.get(`/time-entries/total?${queryParams.toString()}`);
  },
};

export default timeTrackingService;
