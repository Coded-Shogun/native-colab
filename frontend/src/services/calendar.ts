/**
 * Calendar/Events API Service
 * Handle calendar and event API calls
 */

import api from '../lib/api';
import type { Event } from '../types';

export const calendarService = {
  /**
   * Get events for workspace
   */
  async getEvents(params: {
    workspace_id: number;
    start_date?: string;
    end_date?: string;
    user_id?: number;
  }): Promise<Event[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    return api.get<Event[]>(`/events?${queryParams.toString()}`);
  },

  /**
   * Get single event
   */
  async getEvent(eventId: number): Promise<Event> {
    return api.get<Event>(`/events/${eventId}`);
  },

  /**
   * Create event
   */
  async createEvent(data: {
    workspace_id: number;
    title: string;
    description?: string;
    start_time: string;
    end_time: string;
    location?: string;
    event_type?: 'meeting' | 'deadline' | 'reminder' | 'other';
    is_all_day?: boolean;
    recurrence_rule?: string;
  }): Promise<Event> {
    return api.post<Event>('/events', data);
  },

  /**
   * Update event
   */
  async updateEvent(eventId: number, data: Partial<Event>): Promise<Event> {
    return api.patch<Event>(`/events/${eventId}`, data);
  },

  /**
   * Delete event
   */
  async deleteEvent(eventId: number): Promise<void> {
    return api.delete(`/events/${eventId}`);
  },

  /**
   * Add attendee to event
   */
  async addAttendee(eventId: number, userId: number): Promise<void> {
    return api.post(`/events/${eventId}/attendees`, { user_id: userId });
  },

  /**
   * Remove attendee from event
   */
  async removeAttendee(eventId: number, userId: number): Promise<void> {
    return api.delete(`/events/${eventId}/attendees/${userId}`);
  },

  /**
   * Update RSVP status
   */
  async updateRSVP(
    eventId: number,
    status: 'accepted' | 'declined' | 'tentative'
  ): Promise<void> {
    return api.post(`/events/${eventId}/rsvp`, { status });
  },
};

export default calendarService;
