import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  userGuideSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'user-guide/getting-started',
        'user-guide/first-login',
        'user-guide/workspace-setup',
      ],
    },
    {
      type: 'category',
      label: 'Core Features',
      items: [
        'user-guide/features/chat',
        'user-guide/features/projects',
        'user-guide/features/documents',
        'user-guide/features/time-tracking',
        'user-guide/features/calendar',
        'user-guide/features/whiteboard',
        'user-guide/features/video-calls',
        'user-guide/features/digital-signatures',
      ],
    },
    {
      type: 'category',
      label: 'User Guides',
      items: [
        'user-guide/guides/managing-projects',
        'user-guide/guides/collaborating-documents',
        'user-guide/guides/tracking-time',
        'user-guide/guides/scheduling-meetings',
        'user-guide/guides/signing-documents',
      ],
    },
    {
      type: 'category',
      label: 'Settings & Account',
      items: [
        'user-guide/settings/profile',
        'user-guide/settings/notifications',
        'user-guide/settings/security',
      ],
    },
  ],

  developerSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'developer/installation',
        'developer/quick-start',
        'developer/configuration',
      ],
    },
    {
      type: 'category',
      label: 'Architecture',
      items: [
        'developer/architecture/overview',
        'developer/architecture/frontend',
        'developer/architecture/backend',
        'developer/architecture/database',
        'developer/architecture/real-time',
      ],
    },
    {
      type: 'category',
      label: 'Development',
      items: [
        'developer/development/project-structure',
        'developer/development/coding-standards',
        'developer/development/testing',
        'developer/development/debugging',
      ],
    },
    {
      type: 'category',
      label: 'Deployment',
      items: [
        'developer/deployment/docker',
        'developer/deployment/production',
        'developer/deployment/scaling',
        'developer/deployment/monitoring',
      ],
    },
    {
      type: 'category',
      label: 'Contributing',
      items: [
        'developer/contributing/guidelines',
        'developer/contributing/pull-requests',
        'developer/contributing/code-review',
      ],
    },
  ],

  apiSidebar: [
    'api/overview',
    {
      type: 'category',
      label: 'Authentication',
      items: [
        'api/auth/overview',
        'api/auth/login',
        'api/auth/register',
        'api/auth/tokens',
      ],
    },
    {
      type: 'category',
      label: 'Workspaces',
      items: [
        'api/workspaces/overview',
        'api/workspaces/create',
        'api/workspaces/members',
      ],
    },
    {
      type: 'category',
      label: 'Chat',
      items: [
        'api/chat/channels',
        'api/chat/messages',
        'api/chat/direct-messages',
      ],
    },
    {
      type: 'category',
      label: 'Projects & Tasks',
      items: [
        'api/projects/projects',
        'api/projects/tasks',
        'api/projects/comments',
      ],
    },
    {
      type: 'category',
      label: 'Documents',
      items: [
        'api/documents/overview',
        'api/documents/upload',
        'api/documents/collaboration',
      ],
    },
    {
      type: 'category',
      label: 'Time Tracking',
      items: [
        'api/time-tracking/entries',
        'api/time-tracking/timesheets',
      ],
    },
    {
      type: 'category',
      label: 'WebSocket Events',
      items: [
        'api/websocket/overview',
        'api/websocket/chat-events',
        'api/websocket/presence',
      ],
    },
  ],
};

export default sidebars;
