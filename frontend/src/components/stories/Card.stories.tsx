import type { Meta, StoryObj } from '@storybook/react';
import Card, { CardHeader, CardTitle, CardContent, CardFooter } from '../Card';
import Button from '../Button';
import { Calendar, Users, FileText } from 'lucide-react';

/**
 * Card component for containing content with optional header, title, content, and footer sections.
 */
const meta = {
  title: 'Design System/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Flexible card container component with support for headers, titles, content, and footers. Perfect for displaying grouped information.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    padding: {
      control: 'select',
      options: ['none', 'sm', 'md', 'lg'],
      description: 'Padding size inside the card',
    },
    hover: {
      control: 'boolean',
      description: 'Adds hover effect with shadow',
    },
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic Cards
export const Default: Story = {
  args: {
    children: <p>This is a basic card</p>,
  },
};

export const WithPadding: Story = {
  render: () => (
    <div className="space-y-4">
      <Card padding="sm">
        <p className="text-sm">Small padding</p>
      </Card>
      <Card padding="md">
        <p>Medium padding (default)</p>
      </Card>
      <Card padding="lg">
        <p>Large padding</p>
      </Card>
    </div>
  ),
};

export const NoPadding: Story = {
  args: {
    padding: 'none',
    children: <img src="https://via.placeholder.com/300x200" alt="Placeholder" className="w-full rounded-lg" />,
  },
};

export const Hoverable: Story = {
  args: {
    hover: true,
    children: <p>Hover over me for a shadow effect</p>,
  },
};

// With Sub-components
export const WithHeader: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Project Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-slate-600 dark:text-slate-400">
          This is the main content of the card. It can contain any type of information.
        </p>
      </CardContent>
    </Card>
  ),
};

export const WithFooter: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Confirm Action</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-slate-600 dark:text-slate-400">
          Are you sure you want to proceed with this action?
        </p>
      </CardContent>
      <CardFooter>
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm">Cancel</Button>
          <Button variant="primary" size="sm">Confirm</Button>
        </div>
      </CardFooter>
    </Card>
  ),
};

export const Complete: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Complete Card Example</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-slate-600 dark:text-slate-400">
          This card has all components: header, title, content, and footer.
        </p>
      </CardContent>
      <CardFooter>
        <Button variant="primary" size="sm" fullWidth>
          Take Action
        </Button>
      </CardFooter>
    </Card>
  ),
};

// Real-world Examples
export const ProjectCard: Story = {
  render: () => (
    <Card hover className="w-80">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>Q4 Marketing Campaign</CardTitle>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Due: Dec 31, 2025
            </p>
          </div>
          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
            Active
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
          Launch new marketing campaign targeting enterprise customers with focus on digital channels.
        </p>
        <div className="flex items-center gap-4 text-sm text-slate-500">
          <div className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            <span>5 members</span>
          </div>
          <div className="flex items-center gap-1">
            <FileText className="w-4 h-4" />
            <span>12 tasks</span>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="outline" size="sm" fullWidth>
          View Details
        </Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Real-world example of a project card',
      },
    },
  },
};

export const EventCard: Story = {
  render: () => (
    <Card hover className="w-80">
      <CardContent>
        <div className="flex gap-4">
          <div className="flex flex-col items-center justify-center bg-blue-100 dark:bg-blue-900 rounded-lg p-3 w-16 h-16">
            <Calendar className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1">
            <CardTitle>Team Standup</CardTitle>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Today at 10:00 AM
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
              Daily sync with the development team
            </p>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="primary" size="sm" fullWidth>
          Join Meeting
        </Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Calendar event card example',
      },
    },
  },
};

export const UserCard: Story = {
  render: () => (
    <Card className="w-64">
      <CardContent>
        <div className="flex flex-col items-center text-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 mb-3" />
          <CardTitle>John Doe</CardTitle>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Product Manager
          </p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-2">
            john.doe@example.com
          </p>
        </div>
      </CardContent>
      <CardFooter>
        <div className="flex gap-2 w-full">
          <Button variant="outline" size="sm" fullWidth>
            Message
          </Button>
          <Button variant="primary" size="sm" fullWidth>
            View Profile
          </Button>
        </div>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'User profile card example',
      },
    },
  },
};

export const StatsCard: Story = {
  render: () => (
    <Card className="w-64">
      <CardContent>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Total Projects
        </p>
        <p className="text-3xl font-bold text-slate-900 dark:text-white mt-2">
          127
        </p>
        <p className="text-sm text-green-600 dark:text-green-400 mt-2">
          ↑ 12% from last month
        </p>
      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Statistics card example',
      },
    },
  },
};

export const CardGrid: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-4 p-4">
      <Card>
        <CardContent>
          <p className="text-sm font-medium text-slate-500">Active Tasks</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">24</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <p className="text-sm font-medium text-slate-500">Completed</p>
          <p className="text-2xl font-bold text-green-600 mt-1">156</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <p className="text-sm font-medium text-slate-500">Team Members</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">8</p>
        </CardContent>
      </Card>
    </div>
  ),
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        story: 'Multiple cards in a grid layout',
      },
    },
  },
};
