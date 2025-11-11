/**
 * Meetings API Service
 * Handle video meeting API calls
 */

import api from '../lib/api';
import type { Meeting } from '../types';

export const meetingsService = {
  /**
   * Get meetings for workspace
   */
  async getMeetings(params: {
    workspace_id: number;
    status?: 'scheduled' | 'live' | 'ended';
  }): Promise<Meeting[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    return api.get<Meeting[]>(`/meetings?${queryParams.toString()}`);
  },

  /**
   * Get single meeting
   */
  async getMeeting(meetingId: number): Promise<Meeting> {
    return api.get<Meeting>(`/meetings/${meetingId}`);
  },

  /**
   * Create meeting
   */
  async createMeeting(data: {
    workspace_id: number;
    title: string;
    description?: string;
    scheduled_start?: string;
    scheduled_end?: string;
    max_participants?: number;
    require_approval?: boolean;
    enable_recording?: boolean;
    enable_chat?: boolean;
    enable_screen_share?: boolean;
  }): Promise<Meeting> {
    return api.post<Meeting>('/meetings', data);
  },

  /**
   * Update meeting
   */
  async updateMeeting(
    meetingId: number,
    data: Partial<Meeting>
  ): Promise<Meeting> {
    return api.patch<Meeting>(`/meetings/${meetingId}`, data);
  },

  /**
   * Delete meeting
   */
  async deleteMeeting(meetingId: number): Promise<void> {
    return api.delete(`/meetings/${meetingId}`);
  },

  /**
   * Start meeting
   */
  async startMeeting(meetingId: number): Promise<Meeting> {
    return api.post<Meeting>(`/meetings/${meetingId}/start`);
  },

  /**
   * End meeting
   */
  async endMeeting(meetingId: number): Promise<Meeting> {
    return api.post<Meeting>(`/meetings/${meetingId}/end`);
  },

  /**
   * Join meeting
   */
  async joinMeeting(meetingId: number): Promise<{
    meeting: Meeting;
    token: string;
  }> {
    return api.post(`/meetings/${meetingId}/join`);
  },

  /**
   * Leave meeting
   */
  async leaveMeeting(meetingId: number): Promise<void> {
    return api.post(`/meetings/${meetingId}/leave`);
  },

  /**
   * Get meeting participants
   */
  async getParticipants(meetingId: number): Promise<any[]> {
    return api.get(`/meetings/${meetingId}/participants`);
  },

  /**
   * Invite participant
   */
  async inviteParticipant(
    meetingId: number,
    userId: number
  ): Promise<void> {
    return api.post(`/meetings/${meetingId}/invite`, { user_id: userId });
  },

  /**
   * Start recording
   */
  async startRecording(meetingId: number): Promise<void> {
    return api.post(`/meetings/${meetingId}/recording/start`);
  },

  /**
   * Stop recording
   */
  async stopRecording(meetingId: number): Promise<void> {
    return api.post(`/meetings/${meetingId}/recording/stop`);
  },

  /**
   * Get recordings
   */
  async getRecordings(meetingId: number): Promise<any[]> {
    return api.get(`/meetings/${meetingId}/recordings`);
  },
};

export default meetingsService;
