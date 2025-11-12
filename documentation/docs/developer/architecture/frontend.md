# Frontend Architecture

The Native Colab frontend is built with React 18 and TypeScript, following modern best practices for maintainability and performance.

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   ├── ui/          # shadcn/ui components
│   │   ├── chat/        # Chat-specific components
│   │   ├── projects/    # Project components
│   │   └── common/      # Shared components
│   ├── features/         # Feature modules
│   │   ├── auth/        # Authentication
│   │   ├── chat/        # Chat feature
│   │   ├── projects/    # Projects feature
│   │   └── documents/   # Documents feature
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API services
│   ├── lib/              # Utilities
│   ├── routes/           # Route definitions
│   ├── types/            # TypeScript types
│   └── App.tsx           # Root component
├── public/               # Static assets
└── package.json
```

## Key Technologies

- **React 18**: Concurrent features, automatic batching
- **TypeScript**: Type safety
- **Vite**: Fast builds and HMR
- **TanStack Query**: Server state management
- **TanStack Router**: Type-safe routing
- **Socket.io Client**: WebSocket communication
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: Accessible components

## State Management

### Server State (TanStack Query)

All server data managed with React Query:

```typescript
// Fetching data
const { data, isLoading, error } = useQuery({
  queryKey: ['projects', workspaceId],
  queryFn: () => projectService.getProjects(workspaceId),
});

// Mutations
const mutation = useMutation({
  mutationFn: projectService.createProject,
  onSuccess: () => {
    queryClient.invalidateQueries(['projects']);
  },
});
```

### Client State (React Hooks)

Local UI state with useState/useReducer:

```typescript
// Simple state
const [isOpen, setIsOpen] = useState(false);

// Complex state
const [state, dispatch] = useReducer(reducer, initialState);
```

### Global Client State (Context)

For truly global UI state:

```typescript
const ThemeContext = createContext<ThemeContextType | null>(null);

export function ThemeProvider({ children }: Props) {
  const [theme, setTheme] = useState<Theme>('light');

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

## Component Architecture

### Component Types

**1. Page Components:**
```typescript
// src/features/projects/pages/ProjectsPage.tsx
export function ProjectsPage() {
  const { workspaceId } = useParams();
  const { data: projects } = useProjects(workspaceId);

  return (
    <div>
      <ProjectList projects={projects} />
    </div>
  );
}
```

**2. Feature Components:**
```typescript
// src/features/projects/components/ProjectList.tsx
export function ProjectList({ projects }: ProjectListProps) {
  return (
    <div className="grid gap-4">
      {projects.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

**3. UI Components:**
```typescript
// src/components/ui/button.tsx
export function Button({ children, ...props }: ButtonProps) {
  return (
    <button className={cn("btn", props.className)} {...props}>
      {children}
    </button>
  );
}
```

## Routing

### TanStack Router Setup

```typescript
// src/routes/__root.tsx
export const Route = createRootRoute({
  component: RootLayout,
});

// src/routes/projects/index.tsx
export const Route = createFileRoute('/projects/')({
  component: ProjectsPage,
  loader: async ({ context }) => {
    const projects = await context.queryClient.ensureQueryData({
      queryKey: ['projects'],
      queryFn: projectService.getProjects,
    });
    return { projects };
  },
});
```

### Protected Routes

```typescript
export const Route = createFileRoute('/projects/')({
  beforeLoad: ({ context }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({ to: '/login' });
    }
  },
});
```

## API Services

### Service Layer

```typescript
// src/services/project.service.ts
class ProjectService {
  private api = axios.create({
    baseURL: config.apiUrl,
  });

  async getProjects(workspaceId: string): Promise<Project[]> {
    const { data } = await this.api.get(`/workspaces/${workspaceId}/projects`);
    return data;
  }

  async createProject(project: CreateProjectInput): Promise<Project> {
    const { data } = await this.api.post('/projects', project);
    return data;
  }
}

export const projectService = new ProjectService();
```

### API Client Configuration

```typescript
// src/lib/api.ts
export const api = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token)
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor (handle errors)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic
      await refreshToken();
      return api.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

## Real-Time Communication

### Socket.io Setup

```typescript
// src/lib/socket.ts
import { io } from 'socket.io-client';

export const socket = io(config.wsUrl, {
  autoConnect: false,
  auth: {
    token: getAccessToken(),
  },
});

// Connection management
export function connectSocket() {
  socket.connect();
}

export function disconnectSocket() {
  socket.disconnect();
}
```

### React Hook for Socket Events

```typescript
// src/hooks/useSocketEvent.ts
export function useSocketEvent<T>(
  event: string,
  handler: (data: T) => void
) {
  useEffect(() => {
    socket.on(event, handler);
    return () => {
      socket.off(event, handler);
    };
  }, [event, handler]);
}

// Usage
function ChatMessages() {
  useSocketEvent<Message>('message:new', (message) => {
    queryClient.setQueryData(['messages'], (old) => [...old, message]);
  });
}
```

## Custom Hooks

### Data Fetching Hooks

```typescript
// src/hooks/useProjects.ts
export function useProjects(workspaceId: string) {
  return useQuery({
    queryKey: ['projects', workspaceId],
    queryFn: () => projectService.getProjects(workspaceId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: projectService.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries(['projects']);
      toast.success('Project created!');
    },
    onError: (error) => {
      toast.error('Failed to create project');
    },
  });
}
```

### Utility Hooks

```typescript
// src/hooks/useDebounce.ts
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}
```

## TypeScript Patterns

### API Types

```typescript
// src/types/project.ts
export interface Project {
  id: string;
  name: string;
  description: string;
  workspaceId: string;
  createdAt: string;
  updatedAt: string;
}

export type CreateProjectInput = Pick<Project, 'name' | 'description' | 'workspaceId'>;
export type UpdateProjectInput = Partial<CreateProjectInput>;
```

### Component Props

```typescript
interface ProjectCardProps {
  project: Project;
  onEdit?: (project: Project) => void;
  onDelete?: (id: string) => void;
  className?: string;
}

export function ProjectCard({
  project,
  onEdit,
  onDelete,
  className
}: ProjectCardProps) {
  // ...
}
```

## Performance Optimization

### Code Splitting

```typescript
// Lazy load routes
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'));

// In router
<Route path="/projects" element={
  <Suspense fallback={<Loading />}>
    <ProjectsPage />
  </Suspense>
} />
```

### Memoization

```typescript
// Memoize expensive computations
const sortedProjects = useMemo(() => {
  return projects.sort((a, b) => a.name.localeCompare(b.name));
}, [projects]);

// Memoize callbacks
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

### Virtual Lists

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

function MessageList({ messages }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef}>
      {virtualizer.getVirtualItems().map((item) => (
        <Message key={item.key} message={messages[item.index]} />
      ))}
    </div>
  );
}
```

## Best Practices

1. **Component Organization**: Group by feature, not type
2. **Props Drilling**: Use context for deeply nested data
3. **Error Boundaries**: Catch and handle errors gracefully
4. **Loading States**: Show loading indicators
5. **Type Safety**: Leverage TypeScript fully
6. **Accessibility**: Use semantic HTML and ARIA attributes
7. **Testing**: Write tests for critical paths
