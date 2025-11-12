# Architecture Overview

Native Colab is built as a modern, scalable web application using a microservices-inspired architecture with clear separation of concerns.

## High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│    Nginx     │────▶│   Backend   │
│  (React)    │◀────│ (Reverse     │◀────│  (FastAPI)  │
└─────────────┘     │  Proxy)      │     └─────────────┘
                    └──────────────┘            │
                                                │
                         ┌──────────────────────┼──────────────────┐
                         │                      │                  │
                    ┌────▼────┐           ┌────▼────┐       ┌────▼────┐
                    │PostgreSQL│           │  Redis  │       │  MinIO  │
                    │(Database)│           │ (Cache) │       │(Storage)│
                    └──────────┘           └─────────┘       └─────────┘
```

## Technology Stack

### Frontend
- **React 18**: UI library with hooks
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **TanStack Query**: Data fetching and caching
- **TanStack Router**: Type-safe routing
- **Socket.io Client**: Real-time communication
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: Component library

### Backend
- **FastAPI**: Modern Python web framework
- **Python 3.11+**: Async/await support
- **SQLAlchemy 2.0**: Async ORM
- **Pydantic v2**: Data validation
- **Socket.io**: Real-time websockets
- **Celery**: Background task processing
- **Alembic**: Database migrations

### Infrastructure
- **PostgreSQL 15+**: Primary database
- **Redis 7+**: Caching and pub/sub
- **MinIO**: S3-compatible object storage
- **Docker**: Containerization
- **Nginx**: Reverse proxy and load balancing

## Architecture Principles

### 1. Separation of Concerns

**Frontend:**
- Presentation layer only
- No business logic
- API calls through services
- State management with TanStack Query

**Backend:**
- Business logic in services
- Data access through repositories
- API routes as thin controllers
- Async operations throughout

### 2. API-First Design

- RESTful API with OpenAPI/Swagger docs
- Versioned API (`/api/v1/`)
- Consistent response formats
- Comprehensive error handling

### 3. Real-Time Communication

**WebSocket Events:**
- Chat messages
- Presence updates
- Notifications
- Document collaboration
- Task updates

**Socket.io Rooms:**
- User-specific rooms
- Workspace rooms
- Channel/project rooms

### 4. Scalability

**Horizontal Scaling:**
- Stateless backend (session in Redis)
- Load balancer ready
- Database read replicas
- CDN for static assets

**Caching Strategy:**
- Redis for session data
- Query result caching
- API response caching
- Browser caching headers

### 5. Security

**Authentication:**
- JWT tokens (access + refresh)
- HTTP-only cookies for refresh tokens
- Token rotation on refresh
- 2FA support

**Authorization:**
- Role-Based Access Control (RBAC)
- Resource-level permissions
- Workspace isolation
- API rate limiting

## Data Flow

### API Request Flow

```
1. Client makes request
2. Nginx receives and forwards
3. FastAPI middleware chain:
   - CORS handling
   - Rate limiting
   - Authentication
   - Request logging
4. Route handler
5. Service layer (business logic)
6. Repository layer (data access)
7. Database query
8. Response back through layers
9. Client receives response
```

### WebSocket Connection Flow

```
1. Client connects to Socket.io
2. Authentication via JWT
3. Join user-specific room
4. Join workspace rooms
5. Real-time event subscription
6. Bidirectional communication
7. Automatic reconnection on disconnect
```

### Background Task Flow

```
1. API endpoint triggers task
2. Task added to Redis queue
3. Celery worker picks up task
4. Task executes asynchronously
5. Result stored in Redis
6. Frontend polls or receives notification
```

## Module Architecture

### Core Modules

Each feature module follows consistent structure:

```
module/
├── api/              # API routes
│   ├── endpoints.py  # Route handlers
│   └── deps.py       # Dependencies
├── schemas/          # Pydantic schemas
│   ├── request.py    # Request models
│   └── response.py   # Response models
├── models/           # SQLAlchemy models
│   └── models.py     # Database models
├── services/         # Business logic
│   └── service.py    # Service functions
├── repositories/     # Data access
│   └── repository.py # Database queries
└── tests/            # Unit tests
    └── test_*.py
```

### Authentication Module

```python
auth/
├── api/
│   ├── login.py      # Login endpoint
│   ├── register.py   # Registration
│   ├── tokens.py     # Token refresh
│   └── oauth.py      # OAuth providers
├── schemas/
│   ├── user.py       # User schemas
│   └── token.py      # Token schemas
├── models/
│   ├── user.py       # User model
│   └── session.py    # Session model
├── services/
│   ├── auth.py       # Auth logic
│   ├── password.py   # Password hashing
│   └── jwt.py        # JWT handling
└── utils/
    └── security.py   # Security utilities
```

## Database Architecture

### Schema Design

**Multi-tenancy:**
- Workspace-based isolation
- Foreign keys to workspace_id
- Row-level security (RLS)

**Relationships:**
- One-to-Many: User → Messages
- Many-to-Many: Users ←→ Workspaces
- Self-referential: Message → Parent Message

**Indexing Strategy:**
- Primary keys (B-tree)
- Foreign keys (B-tree)
- Full-text search (GIN)
- Timestamp queries (B-tree)

### Connection Pooling

```python
# Async connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Base connections
    max_overflow=10,     # Extra connections
    pool_pre_ping=True,  # Health check
)
```

## Caching Strategy

### Redis Usage

**Session Storage:**
```python
# User sessions
session:{user_id} → session_data
TTL: 7 days
```

**Cache Keys:**
```python
# API response cache
cache:users:{user_id} → user_data
cache:projects:{project_id} → project_data
TTL: 5 minutes

# Query result cache
cache:query:{hash} → result
TTL: 1 hour
```

**Pub/Sub:**
```python
# Real-time notifications
channel:workspace:{id} → events
channel:user:{id} → notifications
```

## File Storage Architecture

### MinIO (S3-Compatible)

**Bucket Structure:**
```
nativecolab/
├── avatars/
│   └── {user_id}/{filename}
├── documents/
│   └── {workspace_id}/{document_id}/{version}/{file}
├── attachments/
│   └── {workspace_id}/{entity_type}/{entity_id}/{file}
└── exports/
    └── {user_id}/{export_id}/{file}
```

**Upload Flow:**
1. Client requests presigned URL
2. Backend generates URL with policy
3. Client uploads directly to MinIO
4. Client confirms upload to backend
5. Backend saves metadata to database

## Monitoring & Observability

### Logging

```python
# Structured logging
logger.info(
    "user_login",
    user_id=user.id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

### Metrics

- **Prometheus**: System metrics
- **Custom Metrics**: Business metrics
- **Grafana**: Visualization

### Tracing

- **Sentry**: Error tracking
- **Request IDs**: End-to-end tracing
- **Performance Monitoring**: Slow query detection

## Performance Considerations

### Frontend Optimization

- Code splitting by route
- Lazy loading components
- Image optimization
- Service worker caching
- Debounced API calls

### Backend Optimization

- Async/await everywhere
- Database query optimization
- N+1 query prevention
- Response compression
- HTTP caching headers

### Database Optimization

- Proper indexing
- Query result caching
- Connection pooling
- Read replicas for scaling
- Materialized views for reports

## Next Steps

- [Frontend Architecture →](./frontend)
- [Backend Architecture →](./backend)
- [Database Architecture →](./database)
- [Real-Time Architecture →](./real-time)
