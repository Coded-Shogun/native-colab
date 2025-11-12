"""
Prometheus Metrics Endpoint
Exposes application metrics for monitoring
"""

from fastapi import APIRouter, Depends, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from app.core.deps import get_current_user
from app.db.models.user import User

router = APIRouter()

# Define metrics

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
active_users_total = Gauge(
    'active_users_total',
    'Total number of active users'
)

workspaces_total = Gauge(
    'workspaces_total',
    'Total number of workspaces'
)

projects_total = Gauge(
    'projects_total',
    'Total number of projects'
)

messages_sent_total = Counter(
    'messages_sent_total',
    'Total messages sent'
)

tasks_created_total = Counter(
    'tasks_created_total',
    'Total tasks created'
)

documents_created_total = Counter(
    'documents_created_total',
    'Total documents created'
)

# Database metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Idle database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

# WebSocket metrics
websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

websocket_messages_sent_total = Counter(
    'websocket_messages_sent_total',
    'Total WebSocket messages sent',
    ['event_type']
)

# Celery metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name']
)

# Security metrics
failed_login_attempts_total = Counter(
    'failed_login_attempts_total',
    'Total failed login attempts'
)

security_events_total = Counter(
    'security_events_total',
    'Total security events',
    ['event_type', 'severity']
)

tokens_blacklisted_total = Counter(
    'tokens_blacklisted_total',
    'Total tokens blacklisted'
)

# Rate limiting metrics
rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['tier', 'identifier_type']
)


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    This endpoint should be scraped by Prometheus server.

    **Note:** In production, this endpoint should be:
    1. Protected by network firewall (only accessible to Prometheus)
    2. Or authenticated with Prometheus bearer token
    3. Not exposed to public internet
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns 200 OK if service is healthy.
    """
    return {
        "status": "healthy",
        "service": "native-colab-api"
    }


@router.get("/readiness")
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 OK if service is ready to accept traffic.
    """
    # TODO: Check database connectivity
    # TODO: Check Redis connectivity
    # TODO: Check external service dependencies

    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "celery": "ok"
        }
    }


@router.get("/liveness")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.
    Returns 200 OK if service is alive (not deadlocked).
    """
    return {
        "status": "alive"
    }
