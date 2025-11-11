/**
 * Tasks Page
 * Task management with filtering and quick actions
 */

import { useState, useEffect } from 'react';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { useAuth } from '../contexts/AuthContext';
import { taskService } from '../services/projects';
import type { Task } from '../types';

type FilterStatus = 'all' | 'todo' | 'in_progress' | 'in_review' | 'completed';
type FilterPriority = 'all' | 'low' | 'medium' | 'high' | 'urgent';

export default function Tasks() {
  const { currentWorkspace } = useWorkspace();
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [filterPriority, setFilterPriority] = useState<FilterPriority>('all');
  const [filterAssignee, setFilterAssignee] = useState<'all' | 'me'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (currentWorkspace) {
      loadTasks();
    }
  }, [currentWorkspace]);

  const loadTasks = async () => {
    if (!currentWorkspace) return;
    try {
      setIsLoading(true);
      const data = await taskService.getTasks({ workspace_id: currentWorkspace.id });
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompleteTask = async (taskId: number) => {
    try {
      await taskService.completeTask(taskId);
      setTasks(tasks.map(t => t.id === taskId ? { ...t, status: 'completed' } : t));
    } catch (error) {
      console.error('Failed to complete task:', error);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      todo: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
      in_progress: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      in_review: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
      completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
      blocked: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
    };
    return colors[status] || colors.todo;
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'text-slate-500 dark:text-slate-400',
      medium: 'text-blue-500 dark:text-blue-400',
      high: 'text-orange-500 dark:text-orange-400',
      urgent: 'text-red-500 dark:text-red-400',
    };
    return colors[priority] || colors.medium;
  };

  const getPriorityIcon = (priority: string) => {
    if (priority === 'urgent') return '🔥';
    if (priority === 'high') return '⬆️';
    if (priority === 'low') return '⬇️';
    return '➡️';
  };

  const getStatusLabel = (status: string) => {
    return status.replace('_', ' ').toUpperCase();
  };

  const filteredTasks = tasks.filter((task) => {
    if (filterStatus !== 'all' && task.status !== filterStatus) return false;
    if (filterPriority !== 'all' && task.priority !== filterPriority) return false;
    if (filterAssignee === 'me' && task.assignee_id !== user?.id) return false;
    if (searchQuery && !task.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const tasksByStatus = {
    todo: filteredTasks.filter(t => t.status === 'todo'),
    in_progress: filteredTasks.filter(t => t.status === 'in_progress'),
    in_review: filteredTasks.filter(t => t.status === 'in_review'),
    completed: filteredTasks.filter(t => t.status === 'completed'),
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
          <p className="text-slate-600 dark:text-slate-400">Loading tasks...</p>
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
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Tasks</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              {filteredTasks.length} task{filteredTasks.length !== 1 ? 's' : ''} found
            </p>
          </div>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            + New Task
          </button>
        </div>

        {/* Search and Filters */}
        <div className="space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tasks..."
              className="w-full px-4 py-2 pl-10 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {/* Filter Buttons */}
          <div className="flex flex-wrap gap-4">
            {/* Status Filter */}
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Status:</span>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
                className="px-3 py-1.5 text-sm bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="in_review">In Review</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            {/* Priority Filter */}
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Priority:</span>
              <select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value as FilterPriority)}
                className="px-3 py-1.5 text-sm bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            {/* Assignee Filter */}
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Assignee:</span>
              <select
                value={filterAssignee}
                onChange={(e) => setFilterAssignee(e.target.value as 'all' | 'me')}
                className="px-3 py-1.5 text-sm bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="me">Assigned to Me</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="To Do" count={tasksByStatus.todo.length} color="slate" />
        <StatCard label="In Progress" count={tasksByStatus.in_progress.length} color="blue" />
        <StatCard label="In Review" count={tasksByStatus.in_review.length} color="purple" />
        <StatCard label="Completed" count={tasksByStatus.completed.length} color="green" />
      </div>

      {/* Tasks List */}
      {filteredTasks.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
          <div className="text-6xl mb-4">✓</div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
            {searchQuery || filterStatus !== 'all' || filterPriority !== 'all' || filterAssignee !== 'all'
              ? 'No tasks match your filters'
              : 'No tasks yet'}
          </h3>
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            {searchQuery || filterStatus !== 'all' || filterPriority !== 'all' || filterAssignee !== 'all'
              ? 'Try adjusting your filters'
              : 'Get started by creating your first task'}
          </p>
          {!searchQuery && filterStatus === 'all' && filterPriority === 'all' && filterAssignee === 'all' && (
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
              + Create Task
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredTasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onComplete={handleCompleteTask}
              getStatusColor={getStatusColor}
              getStatusLabel={getStatusLabel}
              getPriorityColor={getPriorityColor}
              getPriorityIcon={getPriorityIcon}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  label: string;
  count: number;
  color: 'slate' | 'blue' | 'purple' | 'green';
}

function StatCard({ label, count, color }: StatCardProps) {
  const colorClasses: Record<string, string> = {
    slate: 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300',
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-300',
    purple: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300',
    green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700 text-green-700 dark:text-green-300',
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
      <div className="text-sm font-medium mb-1">{label}</div>
      <div className="text-2xl font-bold">{count}</div>
    </div>
  );
}

interface TaskCardProps {
  task: Task;
  onComplete: (taskId: number) => void;
  getStatusColor: (status: string) => string;
  getStatusLabel: (status: string) => string;
  getPriorityColor: (priority: string) => string;
  getPriorityIcon: (priority: string) => string;
}

function TaskCard({ task, onComplete, getStatusColor, getStatusLabel, getPriorityColor, getPriorityIcon }: TaskCardProps) {
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'completed';

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1 min-w-0">
          {/* Checkbox */}
          <button
            onClick={() => task.status !== 'completed' && onComplete(task.id)}
            className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
              task.status === 'completed'
                ? 'bg-green-500 border-green-500'
                : 'border-slate-300 dark:border-slate-600 hover:border-blue-500'
            }`}
          >
            {task.status === 'completed' && (
              <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            )}
          </button>

          {/* Task Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-2">
              <h3
                className={`text-base font-medium flex-1 ${
                  task.status === 'completed'
                    ? 'text-slate-500 dark:text-slate-400 line-through'
                    : 'text-slate-900 dark:text-white'
                }`}
              >
                {task.title}
              </h3>
            </div>

            {task.description && (
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2 line-clamp-2">
                {task.description}
              </p>
            )}

            <div className="flex items-center flex-wrap gap-2 text-sm">
              {/* Status Badge */}
              <span className={`px-2 py-0.5 text-xs font-medium rounded ${getStatusColor(task.status)}`}>
                {getStatusLabel(task.status)}
              </span>

              {/* Priority */}
              <span className={`flex items-center space-x-1 ${getPriorityColor(task.priority)}`}>
                <span>{getPriorityIcon(task.priority)}</span>
                <span className="text-xs font-medium capitalize">{task.priority}</span>
              </span>

              {/* Due Date */}
              {task.due_date && (
                <span
                  className={`text-xs ${
                    isOverdue ? 'text-red-600 dark:text-red-400 font-semibold' : 'text-slate-500 dark:text-slate-400'
                  }`}
                >
                  📅 {new Date(task.due_date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: new Date(task.due_date).getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined,
                  })}
                  {isOverdue && ' (Overdue)'}
                </span>
              )}

              {/* Project */}
              {task.project && (
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  📋 {task.project.name}
                </span>
              )}

              {/* Assignee */}
              {task.assignee && (
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  👤 {task.assignee.full_name}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-1 ml-4">
          <button className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors">
            <svg className="w-4 h-4 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
