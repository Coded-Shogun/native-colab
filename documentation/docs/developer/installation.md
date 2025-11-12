# Installation

Get Native Colab running on your local development environment.

## Prerequisites

### Required Software

- **Docker**: 24.0+ and Docker Compose 2.20+
- **Node.js**: 18+ (for local frontend development)
- **Python**: 3.11+ (for local backend development)
- **Git**: Latest version

### System Requirements

**Minimum:**
- 4 CPU cores
- 8GB RAM
- 20GB available disk space

**Recommended:**
- 8 CPU cores
- 16GB RAM
- 50GB available disk space (for databases and file storage)

## Quick Start with Docker

The fastest way to get Native Colab running:

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/native-colab.git
cd native-colab
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferred editor
nano .env  # or vim, code, etc.
```

**Key settings to configure:**
```env
# Application
SECRET_KEY=your-secret-key-change-this
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://nativecolab:password@postgres:5432/nativecolab

# Redis
REDIS_URL=redis://redis:6379/0

# Frontend
VITE_API_URL=http://localhost:8000
```

### 3. Start Development Environment

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Create initial data (optional)
docker-compose exec backend python scripts/create_initial_data.py
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

**Default Login:**
```
Email: admin@nativecolab.local
Password: ChangeMe123!
```

## Local Development Setup

For active development without Docker:

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/nativecolab"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="your-secret-key"

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your settings

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173 with hot-reload enabled.

### Database Setup (Local PostgreSQL)

```bash
# Install PostgreSQL 15+
# On macOS:
brew install postgresql@15

# On Ubuntu/Debian:
sudo apt-get install postgresql-15

# Create database and user
psql postgres
CREATE DATABASE nativecolab;
CREATE USER nativecolab WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE nativecolab TO nativecolab;
\q
```

### Redis Setup (Local)

```bash
# Install Redis 7+
# On macOS:
brew install redis
brew services start redis

# On Ubuntu/Debian:
sudo apt-get install redis-server
sudo systemctl start redis
```

## Verification

### Check Services

```bash
# Docker setup
docker-compose ps

# Should show all services as 'Up'
```

### Test API

```bash
# Health check
curl http://localhost:8000/health

# Expected response: {"status": "healthy"}
```

### Test Frontend

Open http://localhost:3000 in your browser. You should see the login page.

## Common Issues

### Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
lsof -i :8000  # On macOS/Linux
netstat -ano | findstr :8000  # On Windows

# Kill the process or change port in docker-compose.yml
```

### Database Connection Failed

**Error:** `could not connect to server: Connection refused`

**Solution:**
```bash
# Ensure PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Recreate database container
docker-compose down postgres
docker-compose up -d postgres
```

### Permission Denied

**Error:** `Permission denied` when running Docker commands

**Solution:**
```bash
# Add your user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended for development)
sudo docker-compose up
```

### Module Not Found (Python)

**Error:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port 5173 Already in Use (Frontend)

**Solution:**
```bash
# Kill process on port 5173
kill $(lsof -t -i:5173)  # macOS/Linux

# Or change port in vite.config.ts
server: {
  port: 3001  # Different port
}
```

## Development Tools

### Recommended IDE/Editor

**VSCode** with extensions:
- Python
- Pylance
- ESLint
- Prettier
- Docker
- PostgreSQL

**PyCharm Professional** (alternative for backend)

### Recommended Browser Extensions

- React Developer Tools
- Redux DevTools
- JSON Formatter

### Database Management

**GUI Tools:**
- pgAdmin 4 (PostgreSQL)
- DBeaver (Universal)
- TablePlus (macOS)

**Redis:**
- RedisInsight
- Redis Commander

## Environment Variables Reference

### Backend (.env)

```env
# Application
APP_NAME=Native Colab
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (for local testing, use MailHog)
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
MAIL_FROM=noreply@nativecolab.local

# File Storage
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=nativecolab
S3_REGION=us-east-1

# WebRTC
STUN_SERVER=stun:stun.l.google.com:19302

# Monitoring
SENTRY_DSN=  # Optional
```

### Frontend (.env.local)

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_NAME=Native Colab
VITE_APP_ENV=development
```

## Next Steps

- [Quick Start Guide →](./quick-start)
- [Project Structure →](./development/project-structure)
- [Configuration Guide →](./configuration)
- [Architecture Overview →](./architecture/overview)
