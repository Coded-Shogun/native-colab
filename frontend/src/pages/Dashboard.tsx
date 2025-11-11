/**
 * Dashboard Page
 * Main application dashboard with overview and quick actions
 */

import { useAuth } from '../contexts/AuthContext';
import { useWorkspace } from '../contexts/WorkspaceContext';

export default function Dashboard() {
  const { user } = useAuth();
  const { currentWorkspace } = useWorkspace();

  return (
    <div className="p-6">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          Welcome back, {user?.full_name}! 👋
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">
          {currentWorkspace
            ? `Working in ${currentWorkspace.name}`
            : 'Select a workspace to get started'}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Projects"
          value="12"
          change="+3"
          icon="📋"
          color="blue"
        />
        <StatCard
          title="Tasks"
          value="48"
          change="+12"
          icon="✓"
          color="green"
        />
        <StatCard
          title="Messages"
          value="234"
          change="+45"
          icon="💬"
          color="purple"
        />
        <StatCard
          title="Hours Tracked"
          value="156"
          change="+24"
          icon="⏱️"
          color="orange"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
            Recent Activity
          </h2>
          <div className="space-y-4">
            <ActivityItem
              icon="📝"
              title="New task assigned"
              description="Design system documentation"
              time="2 hours ago"
            />
            <ActivityItem
              icon="💬"
              title="New message"
              description="Sarah mentioned you in #design"
              time="3 hours ago"
            />
            <ActivityItem
              icon="📄"
              title="Document updated"
              description="Q4 Roadmap.pdf"
              time="5 hours ago"
            />
            <ActivityItem
              icon="✅"
              title="Task completed"
              description="API integration testing"
              time="1 day ago"
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
            Quick Actions
          </h2>
          <div className="space-y-3">
            <QuickActionButton icon="📋" label="New Project" />
            <QuickActionButton icon="✓" label="Create Task" />
            <QuickActionButton icon="📄" label="Upload Document" />
            <QuickActionButton icon="📅" label="Schedule Meeting" />
            <QuickActionButton icon="⏱️" label="Start Timer" />
          </div>
        </div>
      </div>

      {/* Upcoming Section */}
      <div className="mt-6 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
          Upcoming This Week
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <UpcomingCard
            type="Meeting"
            title="Team Standup"
            time="Today, 10:00 AM"
            color="blue"
          />
          <UpcomingCard
            type="Deadline"
            title="Q4 Report Due"
            time="Tomorrow, 5:00 PM"
            color="red"
          />
          <UpcomingCard
            type="Event"
            title="Product Launch"
            time="Friday, 2:00 PM"
            color="green"
          />
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
}

function StatCard({ title, value, change, icon, color }: StatCardProps) {
  const colors = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
    orange: 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400',
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-600 dark:text-slate-400">{title}</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{value}</p>
          <p className="text-sm text-green-600 dark:text-green-400 mt-1">{change} this week</p>
        </div>
        <div className={`text-3xl p-3 rounded-lg ${colors[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

interface ActivityItemProps {
  icon: string;
  title: string;
  description: string;
  time: string;
}

function ActivityItem({ icon, title, description, time }: ActivityItemProps) {
  return (
    <div className="flex items-start space-x-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
      <span className="text-2xl">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 dark:text-white">{title}</p>
        <p className="text-sm text-slate-600 dark:text-slate-400 truncate">{description}</p>
        <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">{time}</p>
      </div>
    </div>
  );
}

interface QuickActionButtonProps {
  icon: string;
  label: string;
}

function QuickActionButton({ icon, label }: QuickActionButtonProps) {
  return (
    <button className="w-full flex items-center space-x-3 p-3 rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-left">
      <span className="text-xl">{icon}</span>
      <span className="text-sm font-medium text-slate-900 dark:text-white">{label}</span>
    </button>
  );
}

interface UpcomingCardProps {
  type: string;
  title: string;
  time: string;
  color: 'blue' | 'red' | 'green';
}

function UpcomingCard({ type, title, time, color }: UpcomingCardProps) {
  const colors = {
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  };

  return (
    <div className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
      <span className={`text-xs font-medium px-2 py-1 rounded ${colors[color]}`}>
        {type}
      </span>
      <h3 className="text-sm font-semibold text-slate-900 dark:text-white mt-3">{title}</h3>
      <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">{time}</p>
    </div>
  );
}
