import type { Meta, StoryObj } from '@storybook/react';
import LoadingSpinner, { PageLoader, InlineLoader } from '../LoadingSpinner';

/**
 * Loading spinner component for indicating loading states.
 */
const meta = {
  title: 'Design System/LoadingSpinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Loading spinner component with different sizes and optional loading messages. Includes full-screen, page, and inline variants.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size of the spinner',
    },
    message: {
      control: 'text',
      description: 'Optional loading message',
    },
    fullScreen: {
      control: 'boolean',
      description: 'Display as full-screen overlay',
    },
  },
} satisfies Meta<typeof LoadingSpinner>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic Sizes
export const Small: Story = {
  args: {
    size: 'sm',
  },
};

export const Medium: Story = {
  args: {
    size: 'md',
  },
};

export const Large: Story = {
  args: {
    size: 'lg',
  },
};

// With Message
export const WithMessage: Story = {
  args: {
    size: 'md',
    message: 'Loading data...',
  },
};

export const LoadingProjects: Story = {
  args: {
    size: 'lg',
    message: 'Loading your projects',
  },
};

export const SavingData: Story = {
  args: {
    size: 'md',
    message: 'Saving changes...',
  },
};

// Full Screen
export const FullScreen: Story = {
  args: {
    size: 'lg',
    message: 'Loading Native Colab...',
    fullScreen: true,
  },
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        story: 'Full-screen loading overlay - typically used during initial app load',
      },
    },
  },
};

// Variants
export const PageLoaderExample: Story = {
  render: () => <PageLoader message="Loading dashboard..." />,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        story: 'Page loader variant - fills the entire viewport',
      },
    },
  },
};

export const InlineLoaderExample: Story = {
  render: () => <InlineLoader message="Loading content..." />,
  parameters: {
    docs: {
      description: {
        story: 'Inline loader variant - for loading sections within a page',
      },
    },
  },
};

// Real-world Examples
export const DataFetching: Story = {
  args: {
    size: 'md',
    message: 'Fetching your data...',
  },
  parameters: {
    docs: {
      description: {
        story: 'Loading state while fetching data from API',
      },
    },
  },
};

export const FileUpload: Story = {
  args: {
    size: 'sm',
    message: 'Uploading file...',
  },
  parameters: {
    docs: {
      description: {
        story: 'Loading state during file upload',
      },
    },
  },
};

export const InitialLoad: Story = {
  args: {
    size: 'lg',
    message: 'Welcome to Native Colab',
    fullScreen: true,
  },
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        story: 'Initial application load screen',
      },
    },
  },
};

// Multiple Loaders
export const MultipleStates: Story = {
  render: () => (
    <div className="space-y-8 p-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Small Loader</h3>
        <LoadingSpinner size="sm" message="Small loading..." />
      </div>
      <div>
        <h3 className="text-lg font-semibold mb-4">Medium Loader</h3>
        <LoadingSpinner size="md" message="Medium loading..." />
      </div>
      <div>
        <h3 className="text-lg font-semibold mb-4">Large Loader</h3>
        <LoadingSpinner size="lg" message="Large loading..." />
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Comparison of all loader sizes',
      },
    },
  },
};
