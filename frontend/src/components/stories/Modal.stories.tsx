import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import Modal, { ModalFooter } from '../Modal';
import Button from '../Button';

const meta = {
  title: 'Design System/Modal',
  component: Modal,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Modal dialog component with overlay, escape-to-close, and multiple sizes. Supports optional title, close button, and scrollable content.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    isOpen: {
      control: 'boolean',
      description: 'Whether the modal is visible',
    },
    title: {
      control: 'text',
      description: 'Optional title in the header',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg', 'xl', 'full'],
      description: 'Width preset for the modal',
    },
    showCloseButton: {
      control: 'boolean',
      description: 'Show the X close button in the header',
    },
  },
  args: {
    onClose: () => {},
  },
} satisfies Meta<typeof Modal>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    isOpen: true,
    title: 'Modal Title',
    children: <p className="text-foreground">This is a modal dialog with a title and close button.</p>,
  },
};

export const WithoutTitle: Story = {
  args: {
    isOpen: true,
    showCloseButton: true,
    children: <p className="text-foreground">A modal rendered without a header title.</p>,
  },
};

export const Small: Story = {
  args: {
    isOpen: true,
    title: 'Small Modal',
    size: 'sm',
    children: <p className="text-foreground">A compact modal for simple confirmations.</p>,
  },
};

export const Medium: Story = {
  args: {
    isOpen: true,
    title: 'Medium Modal',
    size: 'md',
    children: <p className="text-foreground">Default medium width modal for general-purpose dialogs.</p>,
  },
};

export const Large: Story = {
  args: {
    isOpen: true,
    title: 'Large Modal',
    size: 'lg',
    children: <p className="text-foreground">A wider modal for detailed content or forms.</p>,
  },
};

export const ExtraLarge: Story = {
  args: {
    isOpen: true,
    title: 'Extra Large Modal',
    size: 'xl',
    children: <p className="text-foreground">Maximum width modal for dashboards or complex layouts.</p>,
  },
};

export const WithFooter: Story = {
  args: {
    isOpen: true,
    title: 'Confirm Action',
    children: (
      <div>
        <p className="text-foreground mb-4">Are you sure you want to delete this project? This action cannot be undone.</p>
        <ModalFooter>
          <Button variant="ghost" size="sm">Cancel</Button>
          <Button variant="danger" size="sm">Delete</Button>
        </ModalFooter>
      </div>
    ),
  },
};

export const LongScrollContent: Story = {
  args: {
    isOpen: true,
    title: 'Scrollable Content',
    children: (
      <div className="space-y-4 text-foreground">
        {Array.from({ length: 20 }, (_, i) => (
          <p key={i}>
            Paragraph {i + 1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
          </p>
        ))}
      </div>
    ),
  },
};

function InteractiveModal() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button onClick={() => setOpen(true)} variant="primary">Open Modal</Button>
      <Modal isOpen={open} onClose={() => setOpen(false)} title="Interactive Modal">
        <p className="text-foreground mb-4">Click the X, press Escape, or click the backdrop to close.</p>
        <ModalFooter>
          <Button variant="primary" size="sm" onClick={() => setOpen(false)}>Got it</Button>
        </ModalFooter>
      </Modal>
    </>
  );
}

export const Interactive: Story = {
  render: () => <InteractiveModal />,
  parameters: {
    docs: {
      description: {
        story: 'Click the button to open the modal. Close via X, Escape key, or backdrop click.',
      },
    },
  },
};
