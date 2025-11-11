/**
 * Projects Page
 * Project management with list and kanban views
 */

import { useState, useEffect } from 'react';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { projectService } from '../services/projects';
import type { Project } from '../types';

type ViewMode = 'list' | 'kanban';

export default function Projects() {
  const { currentWorkspace } = useWorkspace();
  const [projects, setProjects] = useState<Project[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('kanban');
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    if (currentWorkspace) {
      loadProjects();
    }
  }, [currentWorkspace]);

  const loadProjects = async () => {
    if (!currentWorkspace) return;
    try {
      setIsLoading(true);
      const data = await projectService.getProjects({ workspace_id: currentWorkspace.id });
      setProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      planning: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
      active: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      on_hold: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
      completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
      archived: 'bg-slate-200 dark:bg-slate-600 text-slate-600 dark:text-slate-400',
    };
    return colors[status] || colors.planning;
  };

  const getStatusLabel = (status: string) => {
    return status.replace('_', ' ').toUpperCase();
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'text-slate-500',
      medium: 'text-blue-500',
      high: 'text-orange-500',
      urgent: 'text-red-500',
    };
    return colors[priority] || colors.medium;
  };

  const filteredProjects = projects.filter((project) => {
    if (filter === 'all') return true;
    return project.status === filter;
  });

  const projectsByStatus = {
    planning: filteredProjects.filter((p) => p.status === 'planning'),
    active: filteredProjects.filter((p) => p.status === 'active'),
    on_hold: filteredProjects.filter((p) => p.status === 'on_hold'),
    completed: filteredProjects.filter((p) => p.status === 'completed'),
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
          <p className="text-slate-600 dark:text-slate-400">Loading projects...</p>
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
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Projects</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              {projects.length} project{projects.length !== 1 ? 's' : ''} in {currentWorkspace.name}
            </p>
          </div>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            + New Project
          </button>
        </div>

        {/* Filters and View Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('active')}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                filter === 'active'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setFilter('completed')}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                filter === 'completed'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              Completed
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'list'
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('kanban')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'kanban'
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {filteredProjects.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">No projects yet</h3>
          <p className="text-slate-600 dark:text-slate-400 mb-6">Get started by creating your first project</p>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            + Create Project
          </button>
        </div>
      ) : viewMode === 'list' ? (
        <div className="space-y-3">
          {filteredProjects.map((project) => (
            <ProjectListItem key={project.id} project={project} getStatusColor={getStatusColor} getStatusLabel={getStatusLabel} getPriorityColor={getPriorityColor} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KanbanColumn
            title="Planning"
            projects={projectsByStatus.planning}
            color="slate"
            getStatusColor={getStatusColor}
            getPriorityColor={getPriorityColor}
          />
          <KanbanColumn
            title="Active"
            projects={projectsByStatus.active}
            color="blue"
            getStatusColor={getStatusColor}
            getPriorityColor={getPriorityColor}
          />
          <KanbanColumn
            title="On Hold"
            projects={projectsByStatus.on_hold}
            color="yellow"
            getStatusColor={getStatusColor}
            getPriorityColor={getPriorityColor}
          />
          <KanbanColumn
            title="Completed"
            projects={projectsByStatus.completed}
            color="green"
            getStatusColor={getStatusColor}
            getPriorityColor={getPriorityColor}
          />
        </div>
      )}
    </div>
  );
}

interface ProjectListItemProps {
  project: Project;
  getStatusColor: (status: string) => string;
  getStatusLabel: (status: string) => string;
  getPriorityColor: (priority: string) => string;
}

function ProjectListItem({ project, getStatusColor, getStatusLabel, getPriorityColor }: ProjectListItemProps) {
  const progress = project.progress || 0;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{project.name}</h3>
            <span className={`px-2 py-0.5 text-xs font-medium rounded ${getStatusColor(project.status)}`}>
              {getStatusLabel(project.status)}
            </span>
          </div>
          {project.description && (
            <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">{project.description}</p>
          )}
        </div>
        <div className={`ml-4 ${getPriorityColor(project.priority)}`}>
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" />
          </svg>
        </div>
      </div>

      <div className="space-y-3">
        {/* Progress Bar */}
        <div>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-slate-600 dark:text-slate-400">Progress</span>
            <span className="font-medium text-slate-900 dark:text-white">{progress}%</span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Dates */}
        <div className="flex items-center justify-between text-sm">
          <div className="text-slate-600 dark:text-slate-400">
            {project.start_date && (
              <span>Started: {new Date(project.start_date).toLocaleDateString()}</span>
            )}
          </div>
          <div className="text-slate-600 dark:text-slate-400">
            {project.end_date && (
              <span>Due: {new Date(project.end_date).toLocaleDateString()}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface KanbanColumnProps {
  title: string;
  projects: Project[];
  color: string;
  getStatusColor: (status: string) => string;
  getPriorityColor: (priority: string) => string;
}

function KanbanColumn({ title, projects, color, getStatusColor, getPriorityColor }: KanbanColumnProps) {
  const colorClasses: Record<string, string> = {
    slate: 'bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-600',
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700',
    yellow: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700',
    green: 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700',
  };

  return (
    <div className="flex flex-col h-full">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center justify-between">
          <span>{title}</span>
          <span className="text-xs font-normal text-slate-500 dark:text-slate-400 ml-2">
            {projects.length}
          </span>
        </h3>
      </div>
      <div className={`flex-1 rounded-lg border-2 border-dashed p-3 space-y-3 min-h-[200px] ${colorClasses[color]}`}>
        {projects.map((project) => (
          <div
            key={project.id}
            className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between mb-2">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white line-clamp-2">
                {project.name}
              </h4>
              <div className={`ml-2 ${getPriorityColor(project.priority)}`}>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" />
                </svg>
              </div>
            </div>

            {project.description && (
              <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mb-3">
                {project.description}
              </p>
            )}

            {/* Progress */}
            <div className="mb-2">
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full transition-all"
                  style={{ width: `${project.progress || 0}%` }}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>{project.progress || 0}%</span>
              {project.end_date && (
                <span>{new Date(project.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
