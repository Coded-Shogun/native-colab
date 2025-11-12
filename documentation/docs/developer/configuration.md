# Configuration Guide

Comprehensive guide to configuring Native Colab for different environments and use cases.

## Environment Files

### Backend Configuration

**File:** `backend/.env`

```env
# === Application Settings ===
APP_NAME=Native Colab
APP_ENV=development  # development, staging, production
DEBUG=true
SECRET_KEY=your-secret-key-min-32-chars
API_V1_PREFIX=/api/v1
FRONTEND_URL=http://localhost:3000

# === Server Settings ===
HOST=0.0.0.0
PORT=8000
WORKERS=4  # For production
RELOAD=true  # Development only

# === Database Settings ===
DATABASE_URL=postgresql+asyncpg://nativecolab:password@postgres:5432/nativecolab
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_PRE_PING=true
DB_ECHO=false  # Set true for SQL query logging

# === Redis Settings ===
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL=3600

# === JWT Settings ===
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# === Email Settings ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true
SMTP_SSL=false
MAIL_FROM=noreply@nativecolab.local
MAIL_FROM_NAME=Native Colab

# === File Storage (MinIO/S3) ===
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=nativecolab
S3_REGION=us-east-1
S3_SECURE=false  # Use true for HTTPS

# === Celery Settings ===
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# === WebRTC Settings ===
STUN_SERVER=stun:stun.l.google.com:19302
TURN_SERVER=  # Optional
TURN_USERNAME=
TURN_PASSWORD=

# === CORS Settings ===
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
CORS_CREDENTIALS=true
CORS_METHODS=["GET","POST","PUT","DELETE","PATCH","OPTIONS"]

# === Rate Limiting ===
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# === Monitoring ===
SENTRY_DSN=  # Optional
SENTRY_ENVIRONMENT=development

# === OAuth (Optional) ===
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# === Feature Flags ===
ENABLE_REGISTRATION=true
ENABLE_OAUTH=false
ENABLE_EMAIL_VERIFICATION=true
ENABLE_2FA=true
```

### Frontend Configuration

**File:** `frontend/.env.local`

```env
# === API Configuration ===
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_API_VERSION=v1

# === Application Settings ===
VITE_APP_NAME=Native Colab
VITE_APP_ENV=development
VITE_APP_VERSION=1.0.0

# === Feature Flags ===
VITE_ENABLE_DEV_TOOLS=true
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_ERROR_REPORTING=false

# === Third Party Services ===
VITE_SENTRY_DSN=
VITE_GOOGLE_ANALYTICS_ID=

# === WebRTC Configuration ===
VITE_STUN_SERVER=stun:stun.l.google.com:19302
VITE_TURN_SERVER=
```

## Docker Configuration

### Development

**File:** `docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - RELOAD=true
    ports:
      - "8000:8000"
      - "5678:5678"  # Debugger port

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
```

### Production

**File:** `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      args:
        - BUILD_ENV=production
    environment:
      - DEBUG=false
      - WORKERS=4
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/nginx/ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

## Application Configuration

### Backend Settings

**File:** `backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Native Colab"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 3600

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Frontend Settings

**File:** `frontend/src/config/index.ts`

```typescript
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  apiVersion: import.meta.env.VITE_API_VERSION || 'v1',
  appName: import.meta.env.VITE_APP_NAME || 'Native Colab',
  environment: import.meta.env.VITE_APP_ENV || 'development',

  features: {
    devTools: import.meta.env.VITE_ENABLE_DEV_TOOLS === 'true',
    analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  },

  webrtc: {
    stunServer: import.meta.env.VITE_STUN_SERVER || 'stun:stun.l.google.com:19302',
    turnServer: import.meta.env.VITE_TURN_SERVER,
  },
} as const;
```

## Environment-Specific Settings

### Development

```env
# Relaxed settings for development
DEBUG=true
RELOAD=true
DB_ECHO=true
CORS_ORIGINS=["*"]
RATE_LIMIT_ENABLED=false
ENABLE_REGISTRATION=true
```

### Staging

```env
# Production-like with some flexibility
DEBUG=false
RELOAD=false
DB_ECHO=false
CORS_ORIGINS=["https://staging.nativecolab.com"]
RATE_LIMIT_ENABLED=true
ENABLE_REGISTRATION=true
```

### Production

```env
# Strict production settings
DEBUG=false
RELOAD=false
DB_ECHO=false
CORS_ORIGINS=["https://nativecolab.com"]
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=30
ENABLE_REGISTRATION=false  # Invite-only
```

## Security Configuration

### Generating Secret Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
openssl rand -hex 32
```

### SSL/TLS Configuration

**Nginx SSL:**

```nginx
server {
    listen 443 ssl http2;
    server_name nativecolab.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... rest of configuration
}
```

### Environment Variable Security

```bash
# Never commit .env files
echo ".env" >> .gitignore
echo "**/.env" >> .gitignore
echo "**/.env.local" >> .gitignore

# Use secrets management in production
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
```

## Database Configuration

### PostgreSQL Tuning

**For Development:**
```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
```

**For Production:**
```
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
max_connections = 200
```

### Connection Pooling

```python
# Backend configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # Normal connections
    max_overflow=10,        # Overflow connections
    pool_pre_ping=True,     # Check connection before use
    pool_recycle=3600,      # Recycle connections hourly
    echo=settings.DEBUG,    # Log SQL in debug mode
)
```

## Monitoring Configuration

### Prometheus

**File:** `docker/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
```

### Sentry Integration

```python
# Backend
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0 if settings.DEBUG else 0.1,
    )
```

```typescript
// Frontend
import * as Sentry from "@sentry/react";

if (config.sentry.dsn) {
  Sentry.init({
    dsn: config.sentry.dsn,
    environment: config.environment,
    tracesSampleRate: 1.0,
  });
}
```

## Next Steps

- [Architecture Overview →](./architecture/overview)
- [Deployment Guide →](./deployment/docker)
- [Security Best Practices →](./deployment/production)
