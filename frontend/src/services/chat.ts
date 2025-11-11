/**
 * Chat API Service
 * Handle chat and messaging API calls
 */

import api from '../lib/api';
import type { Channel, Message } from '../types';

export const chatService = {
  /**
   * Get all channels for workspace
   */
  async getChannels(workspaceId: number): Promise<Channel[]> {
    return api.get<Channel[]>(`/channels?workspace_id=${workspaceId}`);
  },

  /**
   * Get channel by ID
   */
  async getChannel(channelId: number): Promise<Channel> {
    return api.get<Channel>(`/channels/${channelId}`);
  },

  /**
   * Create a new channel
   */
  async createChannel(data: {
    workspace_id: number;
    name: string;
    description?: string;
    is_private?: boolean;
  }): Promise<Channel> {
    return api.post<Channel>('/channels', data);
  },

  /**
   * Update channel
   */
  async updateChannel(
    channelId: number,
    data: Partial<Channel>
  ): Promise<Channel> {
    return api.patch<Channel>(`/channels/${channelId}`, data);
  },

  /**
   * Delete channel
   */
  async deleteChannel(channelId: number): Promise<void> {
    return api.delete(`/channels/${channelId}`);
  },

  /**
   * Get messages for channel
   */
  async getMessages(
    channelId: number,
    limit: number = 50,
    offset: number = 0
  ): Promise<Message[]> {
    return api.get<Message[]>(
      `/channels/${channelId}/messages?limit=${limit}&offset=${offset}`
    );
  },

  /**
   * Send message to channel
   */
  async sendMessage(
    channelId: number,
    content: string
  ): Promise<Message> {
    return api.post<Message>(`/channels/${channelId}/messages`, {
      content,
      type: 'text',
    });
  },

  /**
   * Update message
   */
  async updateMessage(
    messageId: number,
    content: string
  ): Promise<Message> {
    return api.patch<Message>(`/messages/${messageId}`, { content });
  },

  /**
   * Delete message
   */
  async deleteMessage(messageId: number): Promise<void> {
    return api.delete(`/messages/${messageId}`);
  },

  /**
   * Join channel
   */
  async joinChannel(channelId: number): Promise<void> {
    return api.post(`/channels/${channelId}/join`);
  },

  /**
   * Leave channel
   */
  async leaveChannel(channelId: number): Promise<void> {
    return api.post(`/channels/${channelId}/leave`);
  },
};

export default chatService;
