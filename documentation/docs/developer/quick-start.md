# Quick Start Guide

Get up and running with Native Colab development in minutes.

## 5-Minute Setup

### Prerequisites Check

```bash
# Verify installations
docker --version        # Should be 24.0+
docker-compose --version  # Should be 2.20+
node --version         # Should be 18+
python --version       # Should be 3.11+
git --version
```

### One-Command Setup

```bash
# Clone, setup, and start
git clone https://github.com/yourusername/native-colab.git && \
cd native-colab && \
cp .env.example .env && \
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d && \
docker-compose exec backend alembic upgrade head
```

### Verify Installation

```bash
# Check all services are running
docker-compose ps

# Test API
curl http://localhost:8000/health

# Open frontend
open http://localhost:3000  # macOS
# or visit http://localhost:3000 in your browser
```

## Your First Changes

### Backend Change

1. Edit a file:
```bash
# Open backend code
code backend/app/main.py
```

2. Add a test endpoint:
```python
@app.get("/api/v1/test")
async def test_endpoint():
    return {"message": "Hello from Native Colab!"}
```

3. Test it:
```bash
curl http://localhost:8000/api/v1/test
```

The server auto-reloads with your changes!

### Frontend Change

1. Edit a component:
```bash
# Open frontend code
code frontend/src/App.tsx
```

2. Make a change:
```tsx
// Modify the welcome message
<h1>Welcome to Native Colab Development!</h1>
```

3. See it live:
The browser auto-refreshes at http://localhost:3000

## Development Workflow

### Daily Workflow

**Morning:**
```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend frontend
```

**During Development:**
```bash
# Run tests
cd backend && pytest
cd frontend && npm test

# Check code quality
cd backend && flake8
cd frontend && npm run lint
```

**Evening:**
```bash
# Stop services
docker-compose down

# Keep data (recommended)
# or

# Clean everything
docker-compose down -v  # Removes volumes
```

### Making Changes

**Backend:**
```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Add new field"

# Run migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Frontend:**
```bash
cd frontend

# Add new dependency
npm install package-name

# Update all dependencies
npm update

# Build for production
npm run build
```

## Common Tasks

### Reset Database

```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm native-colab_postgres_data

# Start fresh
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Run Tests

```bash
# Backend tests
docker-compose exec backend pytest

# With coverage
docker-compose exec backend pytest --cov=app

# Frontend tests
docker-compose exec frontend npm test

# E2E tests
npm run test:e2e
```

### Database Operations

```bash
# Access PostgreSQL CLI
docker-compose exec postgres psql -U nativecolab -d nativecolab

# Backup database
docker-compose exec postgres pg_dump -U nativecolab nativecolab > backup.sql

# Restore database
docker-compose exec -T postgres psql -U nativecolab nativecolab < backup.sql
```

### Redis Operations

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Monitor Redis
docker-compose exec redis redis-cli MONITOR

# Flush all data
docker-compose exec redis redis-cli FLUSHALL
```

## Debugging

### Backend Debugging

**Add breakpoints:**
```python
import pdb; pdb.set_trace()  # Python debugger
# or
import ipdb; ipdb.set_trace()  # Enhanced debugger
```

**Attach debugger:**
```bash
# VSCode launch.json
{
  "name": "Python: Remote Attach",
  "type": "python",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5678
  },
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}/backend",
      "remoteRoot": "/app"
    }
  ]
}
```

### Frontend Debugging

**Browser DevTools:**
- Press F12
- Use React DevTools
- Check Console for errors
- Network tab for API calls

**VSCode Debugging:**
```json
{
  "name": "Chrome: Launch",
  "type": "chrome",
  "request": "launch",
  "url": "http://localhost:3000",
  "webRoot": "${workspaceFolder}/frontend/src"
}
```

## API Documentation

While developing, access interactive API docs:

**Swagger UI:**
- http://localhost:8000/docs

**ReDoc:**
- http://localhost:8000/redoc

## Hot Tips

### Performance

```bash
# Increase Docker resources (Mac/Windows)
# Docker Desktop → Preferences → Resources
# Recommended: 4 CPUs, 8GB RAM

# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
```

### Productivity

```bash
# Shell aliases for common commands
alias dc='docker-compose'
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dclogs='docker-compose logs -f'

# Add to ~/.bashrc or ~/.zshrc
```

### Code Quality

```bash
# Pre-commit hooks
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Troubleshooting Quick Fixes

**Services won't start:**
```bash
docker-compose down -v
docker-compose up -d --force-recreate
```

**Port conflicts:**
```bash
# Change ports in docker-compose.dev.yml
ports:
  - "3001:3000"  # Frontend
  - "8001:8000"  # Backend
```

**Database issues:**
```bash
docker-compose restart postgres
docker-compose logs postgres
```

**Cache issues (frontend):**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Cache issues (backend):**
```bash
cd backend
find . -type d -name __pycache__ -exec rm -r {} +
pip install -r requirements.txt --force-reinstall
```

## Next Steps

Now that you're set up:

1. [Explore the Architecture →](./architecture/overview)
2. [Understand Project Structure →](./development/project-structure)
3. [Read Coding Standards →](./development/coding-standards)
4. [Set Up Testing →](./development/testing)
5. [Learn Debugging Techniques →](./development/debugging)

## Getting Help

- **Documentation**: You're reading it!
- **GitHub Issues**: For bugs and features
- **Discussions**: For questions and ideas
- **Code Comments**: Check inline documentation
