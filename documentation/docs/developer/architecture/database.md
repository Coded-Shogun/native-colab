# Database Architecture

Native Colab uses PostgreSQL 15+ for data persistence with a carefully designed schema for multi-tenancy and scalability.

## Schema Overview

The database follows these principles:
- Multi-tenant with workspace isolation
- Proper foreign key relationships
- Comprehensive indexing
- Full-text search support
- Audit trails where needed

## Core Tables

### Users & Authentication

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
```

### Workspaces

```sql
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- admin, manager, member, guest
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

CREATE INDEX idx_workspace_members_user_id ON workspace_members(user_id);
```

### Projects & Tasks

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'todo',
    priority VARCHAR(20) DEFAULT 'medium',
    assignee_id UUID REFERENCES users(id) ON DELETE SET NULL,
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_projects_workspace_id ON projects(workspace_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_assignee_id ON tasks(assignee_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
```

### Chat & Messages

```sql
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(20) NOT NULL, -- public, private
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE channel_members (
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (channel_id, user_id)
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    parent_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    edited_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_channels_workspace_id ON channels(workspace_id);
CREATE INDEX idx_messages_channel_id ON messages(channel_id);
CREATE INDEX idx_messages_parent_id ON messages(parent_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);

-- Full-text search on messages
ALTER TABLE messages ADD COLUMN search_vector tsvector;
CREATE INDEX idx_messages_search ON messages USING GIN(search_vector);
```

### Documents

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    content TEXT,
    version INTEGER DEFAULT 1,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_workspace_id ON documents(workspace_id);
CREATE INDEX idx_document_versions_document_id ON document_versions(document_id);
```

## Relationships

### One-to-Many

- Workspace → Projects
- Project → Tasks
- Channel → Messages
- User → Messages

### Many-to-Many

- Users ↔ Workspaces (through workspace_members)
- Users ↔ Channels (through channel_members)
- Tasks ↔ Users (through task_assignments)

### Self-Referential

- Messages → Parent Message (threads)

## Indexing Strategy

### Primary Indexes

- All primary keys (UUID)
- Unique constraints (email, slug)

### Foreign Key Indexes

```sql
-- For efficient joins
CREATE INDEX idx_projects_workspace_id ON projects(workspace_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_messages_channel_id ON messages(channel_id);
```

### Query Optimization Indexes

```sql
-- For common WHERE clauses
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assignee_id ON tasks(assignee_id);

-- For sorting
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- Composite indexes for complex queries
CREATE INDEX idx_tasks_project_status ON tasks(project_id, status);
```

### Full-Text Search

```sql
-- For search functionality
CREATE INDEX idx_messages_search ON messages USING GIN(search_vector);
CREATE INDEX idx_documents_search ON documents USING GIN(to_tsvector('english', content));
```

## Multi-Tenancy

All tenant-specific tables have `workspace_id`:

```sql
-- Row Level Security (optional)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY projects_isolation ON projects
    USING (workspace_id IN (
        SELECT workspace_id FROM workspace_members
        WHERE user_id = current_user_id()
    ));
```

## Migrations with Alembic

### Create Migration

```bash
# Auto-generate from models
alembic revision --autogenerate -m "Add projects table"

# Empty migration for custom SQL
alembic revision -m "Add indexes"
```

### Example Migration

```python
def upgrade():
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_projects_workspace_id', 'projects', ['workspace_id'])

def downgrade():
    op.drop_index('idx_projects_workspace_id')
    op.drop_table('projects')
```

## Query Optimization

### Connection Pooling

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
```

### N+1 Query Prevention

```python
# Bad: N+1 queries
projects = await session.execute(select(Project))
for project in projects:
    tasks = await session.execute(
        select(Task).where(Task.project_id == project.id)
    )

# Good: Join or eager loading
projects = await session.execute(
    select(Project).options(selectinload(Project.tasks))
)
```

### Pagination

```python
# Offset pagination
query = select(Task).limit(20).offset(page * 20)

# Cursor pagination (more efficient for large datasets)
query = select(Task).where(Task.id > last_id).limit(20)
```

## Backup & Recovery

```bash
# Backup
pg_dump -U nativecolab nativecolab > backup.sql

# Restore
psql -U nativecolab nativecolab < backup.sql

# Continuous archiving (WAL)
# Configure in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /archive/%f'
```

## Performance Tips

1. **Use Indexes**: For frequently queried columns
2. **Avoid SELECT ***: Query only needed columns
3. **Use Joins**: Instead of multiple queries
4. **Batch Operations**: Use bulk insert/update
5. **Monitor Slow Queries**: Enable slow query logging
6. **Vacuum Regularly**: Keep statistics updated
7. **Connection Pooling**: Reuse connections
