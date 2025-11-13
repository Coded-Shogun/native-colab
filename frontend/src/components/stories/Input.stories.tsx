import type { Meta, StoryObj } from '@storybook/react';
import Input from '../Input';

/**
 * Input component for forms with support for labels, errors, and helper text.
 */
const meta = {
  title: 'Design System/Input',
  component: Input,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Form input component with label, error states, and helper text. Supports all standard HTML input types.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    label: {
      control: 'text',
      description: 'Label text for the input',
    },
    error: {
      control: 'text',
      description: 'Error message to display',
    },
    helperText: {
      control: 'text',
      description: 'Helper text shown below input',
    },
    fullWidth: {
      control: 'boolean',
      description: 'Makes input take full width',
    },
    required: {
      control: 'boolean',
      description: 'Marks input as required',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the input',
    },
  },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic Inputs
export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
};

export const WithLabel: Story = {
  args: {
    label: 'Email Address',
    placeholder: 'you@example.com',
  },
};

export const WithHelperText: Story = {
  args: {
    label: 'Username',
    placeholder: 'johndoe',
    helperText: 'This will be your public display name',
  },
};

export const Required: Story = {
  args: {
    label: 'Company Name',
    placeholder: 'Acme Inc.',
    required: true,
  },
};

// States
export const WithError: Story = {
  args: {
    label: 'Email',
    placeholder: 'you@example.com',
    error: 'Please enter a valid email address',
    defaultValue: 'invalid-email',
  },
};

export const Disabled: Story = {
  args: {
    label: 'Disabled Input',
    placeholder: 'Cannot edit',
    disabled: true,
    defaultValue: 'This field is disabled',
  },
};

// Types
export const Email: Story = {
  args: {
    type: 'email',
    label: 'Email Address',
    placeholder: 'you@example.com',
  },
};

export const Password: Story = {
  args: {
    type: 'password',
    label: 'Password',
    placeholder: '••••••••',
    helperText: 'Must be at least 8 characters',
  },
};

export const Number: Story = {
  args: {
    type: 'number',
    label: 'Age',
    placeholder: '25',
    min: 0,
    max: 120,
  },
};

export const Date: Story = {
  args: {
    type: 'date',
    label: 'Date of Birth',
  },
};

export const Search: Story = {
  args: {
    type: 'search',
    placeholder: 'Search projects...',
  },
};

// Full Width
export const FullWidth: Story = {
  args: {
    label: 'Project Description',
    placeholder: 'Describe your project',
    fullWidth: true,
  },
  parameters: {
    layout: 'padded',
  },
};

// Form Examples
export const LoginForm: Story = {
  render: () => (
    <div className="space-y-4 w-80">
      <Input
        type="email"
        label="Email"
        placeholder="you@example.com"
        required
        fullWidth
      />
      <Input
        type="password"
        label="Password"
        placeholder="••••••••"
        required
        fullWidth
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example of inputs in a login form',
      },
    },
  },
};

export const ProfileForm: Story = {
  render: () => (
    <div className="space-y-4 w-96">
      <Input
        label="Full Name"
        placeholder="John Doe"
        required
        fullWidth
      />
      <Input
        type="email"
        label="Email"
        placeholder="john@example.com"
        helperText="We'll never share your email"
        required
        fullWidth
      />
      <Input
        label="Company"
        placeholder="Acme Inc."
        fullWidth
      />
      <Input
        type="url"
        label="Website"
        placeholder="https://example.com"
        fullWidth
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example of inputs in a profile form',
      },
    },
  },
};

export const ValidationExample: Story = {
  render: () => (
    <div className="space-y-4 w-80">
      <Input
        label="Valid Email"
        type="email"
        defaultValue="user@example.com"
        fullWidth
      />
      <Input
        label="Invalid Email"
        type="email"
        defaultValue="not-an-email"
        error="Please enter a valid email address"
        fullWidth
      />
      <Input
        label="Required Field"
        placeholder="This field is required"
        required
        error="This field cannot be empty"
        fullWidth
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example showing validation states',
      },
    },
  },
};
