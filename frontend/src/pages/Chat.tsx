/**
 * Chat Page
 * Real-time messaging with channels
 */

import { useState, useEffect, useRef } from 'react';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { useAuth } from '../contexts/AuthContext';
import { chatService } from '../services/chat';
import type { Channel, Message } from '../types';

export default function Chat() {
  const { currentWorkspace } = useWorkspace();
  const { user } = useAuth();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageText, setMessageText] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load channels
  useEffect(() => {
    if (currentWorkspace) {
      loadChannels();
    }
  }, [currentWorkspace]);

  // Load messages when channel changes
  useEffect(() => {
    if (selectedChannel) {
      loadMessages();
    }
  }, [selectedChannel]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChannels = async () => {
    if (!currentWorkspace) return;
    try {
      setIsLoading(true);
      const data = await chatService.getChannels(currentWorkspace.id);
      setChannels(data);
      if (data.length > 0 && !selectedChannel) {
        setSelectedChannel(data[0]);
      }
    } catch (error) {
      console.error('Failed to load channels:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async () => {
    if (!selectedChannel) return;
    try {
      const data = await chatService.getMessages(selectedChannel.id, { limit: 100 });
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedChannel || !messageText.trim() || isSending) return;

    try {
      setIsSending(true);
      const newMessage = await chatService.sendMessage(selectedChannel.id, {
        content: messageText,
      });
      setMessages([...messages, newMessage]);
      setMessageText('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (!currentWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-slate-600 dark:text-slate-400">Please select a workspace</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading channels...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Channel Sidebar */}
      <div className="w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Channels</h2>
        </div>

        {/* Channel List */}
        <div className="flex-1 overflow-y-auto">
          {channels.length === 0 ? (
            <div className="p-4 text-center text-slate-500 dark:text-slate-400 text-sm">
              No channels yet
            </div>
          ) : (
            <div className="p-2">
              {channels.map((channel) => (
                <button
                  key={channel.id}
                  onClick={() => setSelectedChannel(channel)}
                  className={`w-full text-left px-3 py-2 rounded-lg mb-1 transition-colors ${
                    selectedChannel?.id === channel.id
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">
                      {channel.is_private ? '🔒' : '#'}
                    </span>
                    <span className="text-sm font-medium truncate">{channel.name}</span>
                  </div>
                  {channel.description && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-1 ml-7">
                      {channel.description}
                    </p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Create Channel Button */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-700">
          <button className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">
            + Create Channel
          </button>
        </div>
      </div>

      {/* Chat Area */}
      {selectedChannel ? (
        <div className="flex-1 flex flex-col bg-slate-50 dark:bg-slate-900">
          {/* Chat Header */}
          <div className="h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center">
                <span className="mr-2">{selectedChannel.is_private ? '🔒' : '#'}</span>
                {selectedChannel.name}
              </h3>
              {selectedChannel.description && (
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                  {selectedChannel.description}
                </p>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                <svg className="w-5 h-5 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </button>
              <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                <svg className="w-5 h-5 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-500 dark:text-slate-400">No messages yet. Start the conversation!</p>
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} className="flex space-x-3">
                  {/* Avatar */}
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {message.sender?.full_name?.[0] || 'U'}
                    </div>
                  </div>

                  {/* Message Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline space-x-2">
                      <span className="text-sm font-semibold text-slate-900 dark:text-white">
                        {message.sender?.full_name || 'Unknown User'}
                      </span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {formatTime(message.created_at)}
                      </span>
                    </div>
                    <div className="mt-1 text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap break-words">
                      {message.content}
                    </div>
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {message.attachments.map((attachment: any, idx: number) => (
                          <div key={idx} className="flex items-center space-x-2 p-2 bg-slate-100 dark:bg-slate-800 rounded-lg">
                            <svg className="w-5 h-5 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                            </svg>
                            <span className="text-sm text-slate-700 dark:text-slate-300">{attachment.filename}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <div className="bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 p-4">
            <form onSubmit={handleSendMessage} className="flex space-x-4">
              <input
                type="text"
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                placeholder={`Message #${selectedChannel.name}`}
                className="flex-1 px-4 py-3 bg-slate-100 dark:bg-slate-700 border-0 rounded-lg text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isSending}
              />
              <button
                type="submit"
                disabled={!messageText.trim() || isSending}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
              >
                {isSending ? 'Sending...' : 'Send'}
              </button>
            </form>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-slate-50 dark:bg-slate-900">
          <p className="text-slate-500 dark:text-slate-400">Select a channel to start chatting</p>
        </div>
      )}
    </div>
  );
}
