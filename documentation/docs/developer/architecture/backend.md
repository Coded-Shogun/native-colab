# Backend Architecture

The Native Colab backend is built with FastAPI, following clean architecture principles with clear separation of concerns.

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   │   └── v1/          # API version 1
│   │       ├── auth.py
│   │       ├── users.py
│   │       └── ...
│   ├── core/             # Core configuration
│   │   ├── config.py    # Settings
│   │   ├── security.py  # Security utilities
│   │   └── deps.py      # Dependencies
│   ├── db/               # Database
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/      # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── repositories/     # Data access
│   ├── socketio/         # WebSocket handlers
│   ├── tasks/            # Celery tasks
│   ├── utils/            # Utilities
│   └── main.py           # Application entry
├── alembic/              # Migrations
├── tests/                # Tests
└── requirements.txt
```

## Layered Architecture

### 1. API Layer (Routes)

Thin controllers that handle HTTP:

```python
from fastapi import APIRouter, Depends
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project import ProjectService

router = APIRouter()

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    service: ProjectService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Create a new project."""
    return await service.create_project(project, current_user)
```

### 2. Service Layer (Business Logic)

Contains all business logic:

```python
from app.repositories.project import ProjectRepository

class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository = Depends(),
    ):
        self.project_repo = project_repo

    async def create_project(
        self,
        project: ProjectCreate,
        user: User,
    ) -> Project:
        # Validate permissions
        if not user.can_create_project():
            raise PermissionError()

        # Business logic
        project_data = {
            **project.dict(),
            "owner_id": user.id,
            "created_at": datetime.utcnow(),
        }

        # Create in database
        return await self.project_repo.create(project_data)
```

### 3. Repository Layer (Data Access)

Handles all database operations:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.project import Project

class ProjectRepository:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def create(self, data: dict) -> Project:
        project = Project(**data)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_by_id(self, project_id: str) -> Project | None:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()
```

## Database Models

### SQLAlchemy Models

```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_projects_workspace_id", "workspace_id"),
        Index("ix_projects_owner_id", "owner_id"),
    )
```

## Pydantic Schemas

### Request/Response Models

```python
from pydantic import BaseModel, Field
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

class ProjectCreate(ProjectBase):
    workspace_id: str

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ProjectResponse(ProjectBase):
    id: str
    workspace_id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
```

## Authentication & Authorization

### JWT Authentication

```python
from jose import jwt, JWTError
from app.core.config import settings

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user
```

### Permission Checking

```python
from functools import wraps

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if not current_user.has_permission(permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

@router.delete("/{project_id}")
@require_permission("project:delete")
async def delete_project(project_id: str, current_user: User = Depends(get_current_user)):
    ...
```

## WebSocket (Socket.io)

### Server Setup

```python
import socketio
from app.core.security import verify_token

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
)

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection."""
    token = auth.get('token')
    user = await verify_token(token)
    if not user:
        return False

    # Save user session
    await sio.save_session(sid, {'user_id': user.id})

    # Join user room
    await sio.enter_room(sid, f"user:{user.id}")

    return True

@sio.event
async def message_send(sid, data):
    """Handle message sending."""
    session = await sio.get_session(sid)
    user_id = session['user_id']

    # Save message to database
    message = await create_message(data, user_id)

    # Broadcast to channel
    await sio.emit('message:new', message.dict(), room=f"channel:{data['channel_id']}")
```

## Background Tasks (Celery)

### Task Definition

```python
from celery import Celery
from app.core.config import settings

celery_app = Celery("worker", broker=settings.CELERY_BROKER_URL)

@celery_app.task
def send_email(to: str, subject: str, body: str):
    """Send email asynchronously."""
    # Email sending logic
    ...

@celery_app.task
def generate_report(user_id: str, report_type: str):
    """Generate report asynchronously."""
    # Report generation logic
    ...
```

### Calling Tasks

```python
@router.post("/reports/generate")
async def generate_report(report: ReportRequest, current_user: User = Depends(get_current_user)):
    # Queue task
    task = generate_report.delay(current_user.id, report.type)
    return {"task_id": task.id, "status": "processing"}
```

## Database Migrations

### Alembic Setup

```python
# alembic/env.py
from app.db.base import Base
from app.db.models import *  # Import all models

target_metadata = Base.metadata

# Create migration
# alembic revision --autogenerate -m "Add projects table"

# Apply migration
# alembic upgrade head

# Rollback
# alembic downgrade -1
```

## Error Handling

### Custom Exceptions

```python
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

class NotFoundException(AppException):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} with id {id} not found", 404)
```

### Global Exception Handler

```python
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )
```

## Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)
```

## API Documentation

FastAPI auto-generates OpenAPI docs:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Testing

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/projects/",
        json={"name": "Test Project", "workspace_id": "ws-123"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"
```

## Best Practices

1. **Async Everywhere**: Use async/await for I/O operations
2. **Type Hints**: Add type hints to all functions
3. **Validation**: Use Pydantic for input validation
4. **Error Handling**: Proper exception handling and logging
5. **Testing**: Write tests for all endpoints
6. **Documentation**: Document complex logic
7. **Security**: Validate all inputs, use parameterized queries
