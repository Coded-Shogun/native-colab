"""
Native Colab - Main FastAPI Application
Unified Collaboration Platform
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import redis.asyncio as redis

from app.core.config import settings
from app.core.token_blacklist import TokenBlacklist, init_token_blacklist

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} ({settings.APP_ENV})")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize Redis client for token blacklisting and rate limiting
    redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
    redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    # Initialize token blacklist
    token_blacklist = TokenBlacklist(redis_client)
    init_token_blacklist(token_blacklist)
    logger.info("Token blacklist initialized")

    # Initialize database tables (in development)
    if settings.DEBUG:
        logger.info("Database tables will be created by Alembic migrations")

    yield

    # Shutdown
    logger.info("Closing Redis connection")
    await redis_client.close()
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Unified Collaboration Platform - Chat, Projects, Documents, Time Tracking & More",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ============================================
# Middleware Configuration
# ============================================

# Enterprise Audit Logging Middleware (First - logs all requests)
from app.middleware.audit import AuditLoggingMiddleware
app.add_middleware(AuditLoggingMiddleware)
logger.info("Audit logging middleware enabled")

# Enterprise Rate Limiting Middleware
from app.middleware.rate_limit import RateLimitMiddleware
redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
app.add_middleware(RateLimitMiddleware, redis_url=redis_url)
logger.info("Rate limiting middleware enabled")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================
# Socket.io Integration
# ============================================

from app.realtime import socket_app

# Mount Socket.io ASGI app
app.mount("/ws", socket_app)

logger.info("Socket.io mounted at /ws")

# ============================================
# Root Endpoints
# ============================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG
    }


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    prometheus_enabled = getattr(settings, 'PROMETHEUS_ENABLED', True)
    if not prometheus_enabled:
        return JSONResponse(
            status_code=404,
            content={"detail": "Metrics endpoint is disabled"}
        )

    # Import here to avoid circular imports
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================
# API Routes
# ============================================

from app.api.v1 import auth, users, workspaces, teams, projects, tasks, time_entries, channels, messages, calendars, events, notifications, folders, documents, signatures, signing, whiteboards, meetings, search, webhooks, integrations, gdpr, metrics

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(workspaces.router, prefix=f"{settings.API_V1_PREFIX}/workspaces", tags=["Workspaces"])
app.include_router(teams.router, prefix=f"{settings.API_V1_PREFIX}/teams", tags=["Teams"])
app.include_router(projects.router, prefix=f"{settings.API_V1_PREFIX}/projects", tags=["Projects"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_PREFIX}/tasks", tags=["Tasks"])
app.include_router(time_entries.router, prefix=f"{settings.API_V1_PREFIX}/time-entries", tags=["Time Tracking"])
app.include_router(channels.router, prefix=f"{settings.API_V1_PREFIX}/channels", tags=["Chat - Channels"])
app.include_router(messages.router, prefix=f"{settings.API_V1_PREFIX}/messages", tags=["Chat - Messages"])
app.include_router(calendars.router, prefix=f"{settings.API_V1_PREFIX}/calendars", tags=["Calendar - Calendars"])
app.include_router(events.router, prefix=f"{settings.API_V1_PREFIX}/events", tags=["Calendar - Events"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_PREFIX}/notifications", tags=["Notifications"])
app.include_router(folders.router, prefix=f"{settings.API_V1_PREFIX}/folders", tags=["Documents - Folders"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["Documents - Files"])
app.include_router(signatures.router, prefix=f"{settings.API_V1_PREFIX}/signature-requests", tags=["Signatures - Requests"])
app.include_router(signing.router, prefix=f"{settings.API_V1_PREFIX}/sign", tags=["Signatures - Signing"])
app.include_router(whiteboards.router, prefix=f"{settings.API_V1_PREFIX}/whiteboards", tags=["Whiteboards"])
app.include_router(meetings.router, prefix=f"{settings.API_V1_PREFIX}/meetings", tags=["Meetings"])
app.include_router(search.router, prefix=f"{settings.API_V1_PREFIX}/search", tags=["Search"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_PREFIX}/webhooks", tags=["Webhooks"])
app.include_router(integrations.router, prefix=f"{settings.API_V1_PREFIX}/integrations", tags=["Integrations"])

# Enterprise Features
app.include_router(gdpr.router, prefix=f"{settings.API_V1_PREFIX}/gdpr", tags=["Enterprise - GDPR Compliance"])
app.include_router(metrics.router, prefix=f"{settings.API_V1_PREFIX}", tags=["Enterprise - Metrics"])
logger.info("Enterprise GDPR and metrics endpoints enabled")

# TODO: Include remaining API routers
# from app.api.v1 import chat, projects, documents, etc.
# app.include_router(chat.router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["Chat"])
# app.include_router(projects.router, prefix=f"{settings.API_V1_PREFIX}/projects", tags=["Projects"])
# app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["Documents"])
# app.include_router(signatures.router, prefix=f"{settings.API_V1_PREFIX}/signatures", tags=["Signatures"])
# app.include_router(time_tracking.router, prefix=f"{settings.API_V1_PREFIX}/time-tracking", tags=["Time Tracking"])
# app.include_router(whiteboard.router, prefix=f"{settings.API_V1_PREFIX}/whiteboard", tags=["Whiteboard"])
# app.include_router(calendar.router, prefix=f"{settings.API_V1_PREFIX}/calendar", tags=["Calendar"])
# app.include_router(webhooks.router, prefix=f"{settings.API_V1_PREFIX}/webhooks", tags=["Webhooks"])


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if not settings.DEBUG else str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
