/**
 * Meetings Page
 * Video meeting management and interface
 */

import { useState, useEffect } from 'react';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { useAuth } from '../contexts/AuthContext';
import { meetingsService } from '../services/meetings';
import type { Meeting } from '../types';

export default function Meetings() {
  const { currentWorkspace } = useWorkspace();
  const { user } = useAuth();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<'all' | 'scheduled' | 'live' | 'ended'>('all');
  const [activeMeeting, setActiveMeeting] = useState<Meeting | null>(null);

  useEffect(() => {
    if (currentWorkspace) {
      loadMeetings();
    }
  }, [currentWorkspace, filterStatus]);

  const loadMeetings = async () => {
    if (!currentWorkspace) return;
    try {
      setIsLoading(true);
      const data = await meetingsService.getMeetings({
        workspace_id: currentWorkspace.id,
        status: filterStatus !== 'all' ? filterStatus : undefined,
      });
      setMeetings(data);
    } catch (error) {
      console.error('Failed to load meetings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartMeeting = async (meetingId: number) => {
    try {
      const meeting = await meetingsService.startMeeting(meetingId);
      setActiveMeeting(meeting);
      setMeetings(meetings.map(m => m.id === meetingId ? meeting : m));
    } catch (error) {
      console.error('Failed to start meeting:', error);
    }
  };

  const handleJoinMeeting = async (meetingId: number) => {
    try {
      const { meeting } = await meetingsService.joinMeeting(meetingId);
      setActiveMeeting(meeting);
    } catch (error) {
      console.error('Failed to join meeting:', error);
    }
  };

  const handleEndMeeting = async (meetingId: number) => {
    if (!confirm('Are you sure you want to end this meeting?')) return;
    try {
      await meetingsService.endMeeting(meetingId);
      setActiveMeeting(null);
      loadMeetings();
    } catch (error) {
      console.error('Failed to end meeting:', error);
    }
  };

  const handleLeaveMeeting = async (meetingId: number) => {
    try {
      await meetingsService.leaveMeeting(meetingId);
      setActiveMeeting(null);
    } catch (error) {
      console.error('Failed to leave meeting:', error);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      scheduled: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      live: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
      ended: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
    };
    return colors[status] || colors.scheduled;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const liveMeetings = meetings.filter(m => m.status === 'live');
  const scheduledMeetings = meetings.filter(m => m.status === 'scheduled');
  const endedMeetings = meetings.filter(m => m.status === 'ended');

  if (!currentWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-slate-600 dark:text-slate-400">Please select a workspace</p>
      </div>
    );
  }

  if (activeMeeting) {
    return <MeetingRoom meeting={activeMeeting} onLeave={handleLeaveMeeting} onEnd={handleEndMeeting} user={user} />;
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading meetings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Meetings</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              {meetings.length} meeting{meetings.length !== 1 ? 's' : ''} in {currentWorkspace.name}
            </p>
          </div>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            + Schedule Meeting
          </button>
        </div>

        {/* Filter Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFilterStatus('all')}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              filterStatus === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilterStatus('live')}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              filterStatus === 'live'
                ? 'bg-green-600 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            Live ({liveMeetings.length})
          </button>
          <button
            onClick={() => setFilterStatus('scheduled')}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              filterStatus === 'scheduled'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            Scheduled ({scheduledMeetings.length})
          </button>
          <button
            onClick={() => setFilterStatus('ended')}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              filterStatus === 'ended'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            Past ({endedMeetings.length})
          </button>
        </div>
      </div>

      {/* Live Meetings Banner */}
      {liveMeetings.length > 0 && filterStatus !== 'ended' && (
        <div className="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-700 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <div>
                <p className="text-sm font-semibold text-green-900 dark:text-green-100">
                  {liveMeetings.length} meeting{liveMeetings.length !== 1 ? 's' : ''} happening now
                </p>
                <p className="text-xs text-green-700 dark:text-green-300 mt-0.5">
                  Join an active meeting or start a new one
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Meetings List */}
      {meetings.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
          <div className="text-6xl mb-4">📹</div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">No meetings yet</h3>
          <p className="text-slate-600 dark:text-slate-400 mb-6">Schedule your first meeting to get started</p>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            + Schedule Meeting
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {meetings.map((meeting) => (
            <MeetingCard
              key={meeting.id}
              meeting={meeting}
              onStart={handleStartMeeting}
              onJoin={handleJoinMeeting}
              onEnd={handleEndMeeting}
              getStatusColor={getStatusColor}
              formatDateTime={formatDateTime}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface MeetingCardProps {
  meeting: Meeting;
  onStart: (meetingId: number) => void;
  onJoin: (meetingId: number) => void;
  onEnd: (meetingId: number) => void;
  getStatusColor: (status: string) => string;
  formatDateTime: (dateString: string) => string;
}

function MeetingCard({ meeting, onStart, onJoin, onEnd, getStatusColor, formatDateTime }: MeetingCardProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{meeting.title}</h3>
        <span className={`px-2 py-0.5 text-xs font-medium rounded ${getStatusColor(meeting.status)}`}>
          {meeting.status.toUpperCase()}
        </span>
      </div>

      {meeting.description && (
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-2">{meeting.description}</p>
      )}

      <div className="space-y-2 mb-4">
        {meeting.scheduled_start && (
          <div className="flex items-center text-sm text-slate-600 dark:text-slate-400">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {formatDateTime(meeting.scheduled_start)}
          </div>
        )}

        {meeting.actual_start && (
          <div className="flex items-center text-sm text-slate-600 dark:text-slate-400">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Started {formatDateTime(meeting.actual_start)}
          </div>
        )}

        <div className="flex items-center text-sm text-slate-600 dark:text-slate-400">
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          {meeting.participants?.length || 0} participant{meeting.participants?.length !== 1 ? 's' : ''}
        </div>
      </div>

      {meeting.status === 'scheduled' && (
        <button
          onClick={() => onStart(meeting.id)}
          className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors"
        >
          Start Meeting
        </button>
      )}

      {meeting.status === 'live' && (
        <div className="space-y-2">
          <button
            onClick={() => onJoin(meeting.id)}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            Join Meeting
          </button>
          <button
            onClick={() => onEnd(meeting.id)}
            className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            End Meeting
          </button>
        </div>
      )}

      {meeting.status === 'ended' && meeting.recording_url && (
        <button className="w-full px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
          View Recording
        </button>
      )}
    </div>
  );
}

interface MeetingRoomProps {
  meeting: Meeting;
  onLeave: (meetingId: number) => void;
  onEnd: (meetingId: number) => void;
  user: any;
}

function MeetingRoom({ meeting, onLeave, onEnd, user }: MeetingRoomProps) {
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);

  return (
    <div className="fixed inset-0 bg-slate-900 z-50">
      {/* Meeting Header */}
      <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-slate-900/90 to-transparent z-10">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">{meeting.title}</h2>
            <p className="text-sm text-slate-300">
              {meeting.participants?.length || 0} participant{meeting.participants?.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 bg-red-500 text-white text-xs font-medium rounded flex items-center">
              <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse" />
              LIVE
            </span>
          </div>
        </div>
      </div>

      {/* Video Grid */}
      <div className="h-full flex items-center justify-center p-4 pt-20 pb-32">
        <div className="grid grid-cols-2 gap-4 w-full max-w-6xl">
          {/* Main Video (Placeholder) */}
          <div className="col-span-2 bg-slate-800 rounded-lg aspect-video flex items-center justify-center">
            <div className="text-center">
              <div className="w-24 h-24 bg-blue-600 rounded-full flex items-center justify-center text-white text-3xl font-semibold mx-auto mb-4">
                {user?.full_name?.[0] || 'Y'}
              </div>
              <p className="text-white text-lg font-medium">{user?.full_name || 'You'}</p>
              {isVideoOff && <p className="text-slate-400 text-sm mt-2">Camera is off</p>}
            </div>
          </div>

          {/* Participant Thumbnails (Placeholders) */}
          {meeting.participants?.slice(0, 4).map((participant: any, index: number) => (
            <div
              key={index}
              className="bg-slate-800 rounded-lg aspect-video flex items-center justify-center"
            >
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center text-white text-xl font-semibold mx-auto mb-2">
                  {participant.user?.full_name?.[0] || 'P'}
                </div>
                <p className="text-white text-sm">{participant.user?.full_name || `Participant ${index + 1}`}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Meeting Controls */}
      <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-slate-900/90 to-transparent">
        <div className="flex items-center justify-center space-x-4">
          <button
            onClick={() => setIsMuted(!isMuted)}
            className={`p-4 rounded-full transition-colors ${
              isMuted ? 'bg-red-600 hover:bg-red-700' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMuted ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 016 0v6a3 3 0 01-3 3z" />
              )}
            </svg>
          </button>

          <button
            onClick={() => setIsVideoOff(!isVideoOff)}
            className={`p-4 rounded-full transition-colors ${
              isVideoOff ? 'bg-red-600 hover:bg-red-700' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>

          <button
            onClick={() => setIsScreenSharing(!isScreenSharing)}
            className={`p-4 rounded-full transition-colors ${
              isScreenSharing ? 'bg-blue-600 hover:bg-blue-700' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </button>

          <button
            onClick={() => onLeave(meeting.id)}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-full transition-colors"
          >
            Leave Meeting
          </button>

          <button
            onClick={() => onEnd(meeting.id)}
            className="p-4 bg-slate-700 hover:bg-slate-600 rounded-full transition-colors"
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
