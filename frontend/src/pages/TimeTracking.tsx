/**
 * Time Tracking Page
 * Track time with timer and view time entries
 */

import { useState, useEffect, useRef } from 'react';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { useAuth } from '../contexts/AuthContext';
import { timeTrackingService } from '../services/timeTracking';
import type { TimeEntry } from '../types';

export default function TimeTracking() {
  const { currentWorkspace } = useWorkspace();
  const { user } = useAuth();
  const [timeEntries, setTimeEntries] = useState<TimeEntry[]>([]);
  const [activeEntry, setActiveEntry] = useState<TimeEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [description, setDescription] = useState('');
  const [isBillable, setIsBillable] = useState(true);
  const [selectedProject, setSelectedProject] = useState<number | undefined>();
  const [totalStats, setTotalStats] = useState({ total_seconds: 0, billable_seconds: 0 });
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (currentWorkspace && user) {
      loadData();
    }
  }, [currentWorkspace, user]);

  useEffect(() => {
    if (activeEntry) {
      const startTime = new Date(activeEntry.start_time).getTime();
      const updateTimer = () => {
        const now = Date.now();
        const elapsed = Math.floor((now - startTime) / 1000);
        setTimerSeconds(elapsed);
      };
      updateTimer();
      timerRef.current = setInterval(updateTimer, 1000);
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    } else {
      setTimerSeconds(0);
    }
  }, [activeEntry]);

  const loadData = async () => {
    if (!currentWorkspace || !user) return;
    try {
      setIsLoading(true);
      const [entries, active, stats] = await Promise.all([
        timeTrackingService.getTimeEntries({
          workspace_id: currentWorkspace.id,
          user_id: user.id,
        }),
        timeTrackingService.getActiveEntry(user.id),
        timeTrackingService.getTotalTime({
          workspace_id: currentWorkspace.id,
          user_id: user.id,
        }),
      ]);
      setTimeEntries(entries);
      setActiveEntry(active);
      setTotalStats(stats);
    } catch (error) {
      console.error('Failed to load time tracking data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartTimer = async () => {
    if (!currentWorkspace || activeEntry) return;
    try {
      const newEntry = await timeTrackingService.startTimer({
        workspace_id: currentWorkspace.id,
        description: description || undefined,
        is_billable: isBillable,
        project_id: selectedProject,
      });
      setActiveEntry(newEntry);
      setDescription('');
    } catch (error) {
      console.error('Failed to start timer:', error);
    }
  };

  const handleStopTimer = async () => {
    if (!activeEntry) return;
    try {
      const stoppedEntry = await timeTrackingService.stopTimer(activeEntry.id);
      setActiveEntry(null);
      setTimeEntries([stoppedEntry, ...timeEntries]);
      loadData(); // Reload to update stats
    } catch (error) {
      console.error('Failed to stop timer:', error);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (startTime: string, endTime: string | null) => {
    const start = new Date(startTime).getTime();
    const end = endTime ? new Date(endTime).getTime() : Date.now();
    const seconds = Math.floor((end - start) / 1000);
    return formatTime(seconds);
  };

  const formatHours = (seconds: number) => {
    const hours = seconds / 3600;
    return hours.toFixed(2);
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
          <p className="text-slate-600 dark:text-slate-400">Loading time tracking...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Time Tracking</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">Track your time and view entries</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timer Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Timer */}
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Timer</h2>

            {/* Timer Display */}
            <div className="text-center mb-6">
              <div className="text-6xl font-bold text-slate-900 dark:text-white mb-2 font-mono">
                {formatTime(timerSeconds)}
              </div>
              {activeEntry && activeEntry.description && (
                <p className="text-slate-600 dark:text-slate-400">{activeEntry.description}</p>
              )}
            </div>

            {activeEntry ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center space-x-3">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Started at {new Date(activeEntry.start_time).toLocaleTimeString()}
                  </span>
                  {activeEntry.is_billable && (
                    <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-medium rounded">
                      Billable
                    </span>
                  )}
                </div>
                <button
                  onClick={handleStopTimer}
                  className="w-full px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors"
                >
                  ⏹ Stop Timer
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What are you working on?"
                  className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isBillable}
                      onChange={(e) => setIsBillable(e.target.checked)}
                      className="w-4 h-4 text-blue-600 bg-slate-100 border-slate-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-slate-700 dark:text-slate-300">Billable</span>
                  </label>
                </div>
                <button
                  onClick={handleStartTimer}
                  className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
                >
                  ▶ Start Timer
                </button>
              </div>
            )}
          </div>

          {/* Recent Entries */}
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Recent Entries</h2>

            {timeEntries.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                <p>No time entries yet. Start the timer to track your time!</p>
              </div>
            ) : (
              <div className="space-y-2">
                {timeEntries.slice(0, 10).map((entry) => (
                  <div
                    key={entry.id}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {entry.description || 'No description'}
                        </p>
                        {entry.is_billable && (
                          <span className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-medium rounded">
                            $
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400">
                        <span>
                          {new Date(entry.start_time).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                        <span>
                          {new Date(entry.start_time).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                          {entry.end_time && (
                            <>
                              {' - '}
                              {new Date(entry.end_time).toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </>
                          )}
                        </span>
                        {entry.project && <span>📋 {entry.project.name}</span>}
                      </div>
                    </div>
                    <div className="ml-4 text-right">
                      <div className="text-sm font-semibold text-slate-900 dark:text-white">
                        {formatDuration(entry.start_time, entry.end_time)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Stats Sidebar */}
        <div className="space-y-6">
          {/* Today's Stats */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg border border-blue-200 dark:border-blue-700 p-6">
            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-4">Today</h3>
            <div className="space-y-3">
              <div>
                <div className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                  {formatHours(totalStats.total_seconds)}h
                </div>
                <div className="text-xs text-blue-700 dark:text-blue-400 mt-1">Total Hours</div>
              </div>
              <div>
                <div className="text-2xl font-semibold text-blue-900 dark:text-blue-100">
                  {formatHours(totalStats.billable_seconds)}h
                </div>
                <div className="text-xs text-blue-700 dark:text-blue-400 mt-1">Billable Hours</div>
              </div>
            </div>
          </div>

          {/* This Week */}
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-sm font-medium text-slate-900 dark:text-white mb-4">This Week</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Total</span>
                <span className="text-lg font-semibold text-slate-900 dark:text-white">
                  {formatHours(totalStats.total_seconds * 5)}h
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Billable</span>
                <span className="text-lg font-semibold text-green-600 dark:text-green-400">
                  {formatHours(totalStats.billable_seconds * 5)}h
                </span>
              </div>
              <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 dark:text-slate-400">Entries</span>
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    {timeEntries.length}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-sm font-medium text-slate-900 dark:text-white mb-3">Quick Actions</h3>
            <div className="space-y-2">
              <button className="w-full px-3 py-2 text-sm text-left text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                📊 View Reports
              </button>
              <button className="w-full px-3 py-2 text-sm text-left text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                📥 Export Data
              </button>
              <button className="w-full px-3 py-2 text-sm text-left text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                ⚙️ Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
