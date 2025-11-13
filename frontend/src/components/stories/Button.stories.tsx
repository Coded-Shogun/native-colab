import type { Meta, StoryObj } from '@storybook/react';
import Button from '../Button';
import { Send, Download, Plus, Trash2 } from 'lucide-react';

/**
 * Button component with multiple variants, sizes, and states.
 * Part of the Native Colab design system.
 */
const meta = {
  title: 'Design System/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Versatile button component with support for variants, sizes, loading states, and full width layouts.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'danger', 'ghost', 'outline'],
      description: 'Visual style of the button',
    },
    size: {
      control: 'radio',
      options: ['sm', 'md', 'lg'],
      description: 'Size of the button',
    },
    isLoading: {
      control: 'boolean',
      description: 'Shows loading spinner and disables button',
    },
    fullWidth: {
      control: 'boolean',
      description: 'Makes button take full width of container',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the button',
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

// Default Button
export const Primary: Story = {
  args: {
    children: 'Primary Button',
    variant: 'primary',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary Button',
    variant: 'secondary',
  },
};

export const Danger: Story = {
  args: {
    children: 'Delete',
    variant: 'danger',
  },
};

export const Ghost: Story = {
  args: {
    children: 'Ghost Button',
    variant: 'ghost',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline Button',
    variant: 'outline',
  },
};

// Sizes
export const Small: Story = {
  args: {
    children: 'Small Button',
    size: 'sm',
  },
};

export const Medium: Story = {
  args: {
    children: 'Medium Button',
    size: 'md',
  },
};

export const Large: Story = {
  args: {
    children: 'Large Button',
    size: 'lg',
  },
};

// States
export const Loading: Story = {
  args: {
    children: 'Loading...',
    isLoading: true,
  },
};

export const Disabled: Story = {
  args: {
    children: 'Disabled Button',
    disabled: true,
  },
};

export const FullWidth: Story = {
  args: {
    children: 'Full Width Button',
    fullWidth: true,
  },
  parameters: {
    layout: 'padded',
  },
};

// With Icons
export const WithIcon: Story = {
  args: {
    children: (
      <>
        <Send className="w-4 h-4 mr-2" />
        Send Message
      </>
    ),
  },
};

export const IconOnly: Story = {
  args: {
    children: <Plus className="w-5 h-5" />,
    size: 'md',
  },
};

export const DownloadButton: Story = {
  args: {
    children: (
      <>
        <Download className="w-4 h-4 mr-2" />
        Download Report
      </>
    ),
    variant: 'secondary',
  },
};

export const DeleteButton: Story = {
  args: {
    children: (
      <>
        <Trash2 className="w-4 h-4 mr-2" />
        Delete Project
      </>
    ),
    variant: 'danger',
  },
};

// Button Group Example
export const ButtonGroup: Story = {
  render: () => (
    <div className="flex gap-2">
      <Button variant="primary">Save</Button>
      <Button variant="secondary">Cancel</Button>
      <Button variant="danger">Delete</Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple buttons displayed together',
      },
    },
  },
};

// Real-world Examples
export const CreateProject: Story = {
  args: {
    children: (
      <>
        <Plus className="w-4 h-4 mr-2" />
        Create New Project
      </>
    ),
    variant: 'primary',
    size: 'lg',
  },
  parameters: {
    docs: {
      description: {
        story: 'Example of a project creation button',
      },
    },
  },
};

export const SaveDraft: Story = {
  args: {
    children: 'Save Draft',
    variant: 'outline',
  },
};

export const SubmitForm: Story = {
  args: {
    children: 'Submit',
    variant: 'primary',
    isLoading: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with loading state for form submission',
      },
    },
  },
};
