# Native Colab Storybook

## 📚 Overview

This Storybook contains the complete component library for Native Colab, an enterprise-grade unified collaboration platform.

## 🚀 Getting Started

### Running Storybook Locally

```bash
# Navigate to frontend directory
cd frontend

# Start Storybook development server
npm run storybook

# Storybook will open at http://localhost:6006
```

### Building Storybook for Production

```bash
# Build static Storybook
npm run build-storybook

# Output will be in storybook-static/
```

## 📦 What's Included

### Design System Components

**Foundation**
- **Button**: Primary, secondary, danger, ghost, outline variants with sizes and states
- **Input**: Form inputs with labels, validation, error states, and helper text
- **Card**: Flexible container with header, title, content, and footer sections
- **LoadingSpinner**: Loading indicators in multiple sizes with full-screen support

**Coming Soon**
- Modal/Dialog components
- Dropdown menus
- Tabs and navigation
- Toast notifications
- Data tables
- Forms and validation

### Feature Components

**Chat** (Planned)
- Message bubbles and threads
- Channel lists
- User presence
- Reactions and emoji

**Projects** (Planned)
- Kanban boards
- Task cards
- Project lists
- Timeline views

**Documents** (Planned)
- Document editor
- File browser
- Version history

**Calendar** (Planned)
- Calendar grid
- Event cards
- Meeting schedulers

**Whiteboard** (Planned)
- Canvas tools
- Drawing components

## 🎨 Component Development

### Creating a New Story

1. Create your component in `/src/components/`
2. Create a `.stories.tsx` file next to it or in `/src/components/stories/`

Example structure:
```typescript
import type { Meta, StoryObj } from '@storybook/react';
import YourComponent from '../YourComponent';

const meta = {
  title: 'Category/YourComponent',
  component: YourComponent,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    // Define controls here
  },
} satisfies Meta<typeof YourComponent>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    // Default props
  },
};
```

### Story Categories

- **Design System/**: Foundational UI components
- **Features/Chat/**: Chat and messaging components
- **Features/Projects/**: Project management components
- **Features/Documents/**: Document handling components
- **Features/Calendar/**: Calendar and scheduling components
- **Features/Whiteboard/**: Whiteboard components
- **Features/Signatures/**: Digital signature components
- **Patterns/**: Common UI patterns and compositions

### Best Practices

1. **Multiple Variants**: Show all variants of your component
2. **Different States**: Include loading, error, disabled, hover states
3. **Real Examples**: Add real-world usage examples
4. **Documentation**: Use JSDoc comments and story descriptions
5. **Accessibility**: Test with the a11y addon
6. **Interactions**: Add interaction tests for complex components

## 🔧 Configuration

### Addons Installed

- **@storybook/addon-essentials**: Core addons (docs, controls, actions, etc.)
- **@storybook/addon-interactions**: Interaction testing
- **@storybook/addon-links**: Link between stories
- **@storybook/addon-a11y**: Accessibility testing

### Tailwind CSS Integration

Storybook is configured to use the same Tailwind CSS configuration as the main app, ensuring consistent styling.

## 🎯 Use Cases

### For Developers

- **Component Development**: Build components in isolation
- **Documentation**: Auto-generated prop documentation
- **Testing**: Visual and interaction testing
- **Debugging**: Test edge cases and states easily

### For Designers

- **Design System**: Reference for consistent UI patterns
- **Component States**: See all states and variants
- **Responsive Design**: Test components at different sizes
- **Dark Mode**: All components support dark mode

### For Marketing/Sales

- **Screenshots**: Capture high-quality UI screenshots for sales materials
- **Feature Showcase**: Demonstrate platform capabilities
- **UI Quality**: Show polished, professional interface
- **Product Documentation**: Reference for feature documentation

### For QA

- **Visual Testing**: Catch visual regressions
- **Component Testing**: Test components independently
- **Accessibility**: Verify WCAG compliance
- **State Coverage**: Ensure all states work correctly

## 🧪 Testing with Storybook

### Visual Testing

```bash
# Install Chromatic for visual regression testing
npm install --save-dev chromatic

# Run visual tests
npx chromatic --project-token=<your-token>
```

### Accessibility Testing

1. Open any story in Storybook
2. Click the "Accessibility" tab
3. Review violations and warnings
4. Fix issues in your components

### Interaction Testing

```typescript
// Example interaction test in a story
export const InteractiveExample: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const button = await canvas.getByRole('button');
    await userEvent.click(button);
    await expect(canvas.getByText('Clicked!')).toBeInTheDocument();
  },
};
```

## 📱 Responsive Design

All stories support responsive testing:

1. Use the viewport addon in Storybook toolbar
2. Test common breakpoints: mobile (320px), tablet (768px), desktop (1024px+)
3. All components should be mobile-friendly

## 🌙 Dark Mode Support

Toggle dark mode using the toolbar theme selector. All components support dark mode out of the box.

## 🔗 Integration with Main App

Components in Storybook use the exact same code as the production app, ensuring:
- What you see in Storybook is what you get in production
- No drift between documentation and reality
- Changes are reflected immediately

## 📊 Component Status

| Component | Status | Stories | Tests | Docs |
|-----------|--------|---------|-------|------|
| Button | ✅ Complete | ✅ | ✅ | ✅ |
| Input | ✅ Complete | ✅ | ✅ | ✅ |
| Card | ✅ Complete | ✅ | ✅ | ✅ |
| LoadingSpinner | ✅ Complete | ✅ | ✅ | ✅ |
| Modal | 🚧 In Progress | ⏳ | ⏳ | ⏳ |
| Chat Components | 📋 Planned | - | - | - |
| Project Components | 📋 Planned | - | - | - |

## 🤝 Contributing

1. **Add New Components**: Follow the component development guide above
2. **Update Existing**: Keep stories in sync with component changes
3. **Document Everything**: Add descriptions and examples
4. **Test Accessibility**: Ensure WCAG AA compliance
5. **Write Interactions**: Add interaction tests for complex components

## 📚 Resources

- [Storybook Documentation](https://storybook.js.org/docs/react/get-started/introduction)
- [Component Driven Development](https://www.componentdriven.org/)
- [Atomic Design Principles](https://bradfrost.com/blog/post/atomic-web-design/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## 🐛 Troubleshooting

### Storybook Won't Start

```bash
# Clear cache and reinstall
rm -rf node_modules .storybook-cache
npm install
npm run storybook
```

### Styles Not Loading

- Ensure Tailwind CSS is properly imported in `.storybook/preview.ts`
- Check that `tailwind.config.js` includes Storybook paths

### Component Not Found

- Verify import paths are correct
- Check that component is exported properly
- Ensure file is included in Storybook's story patterns

## 📞 Support

For questions or issues:
- Check existing stories for examples
- Review Storybook documentation
- Ask in the team Slack channel
- Create an issue in the repository

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Maintainers**: Native Colab Frontend Team
