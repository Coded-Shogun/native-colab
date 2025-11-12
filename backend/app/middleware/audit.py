"""
Audit Logging Middleware
Automatically logs all API requests and data modifications for compliance
"""

import time
import uuid
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog, SecurityEvent
from app.db.session import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all API requests for audit trail.
    Creates audit log entries for compliance and security monitoring.
    """

    # Sensitive fields to exclude from logging
    SENSITIVE_FIELDS = {"password", "token", "secret", "api_key", "credit_card"}

    # Actions that should be audited
    AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Map HTTP methods to audit actions
    METHOD_TO_ACTION = {
        "POST": "create",
        "GET": "read",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete"
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and create audit log."""
        # Generate request ID for distributed tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Extract context
        user_id = getattr(request.state, "user_id", None) if hasattr(request.state, "user_id") else None
        workspace_id = getattr(request.state, "workspace_id", None) if hasattr(request.state, "workspace_id") else None

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Determine if this should be audited
        should_audit = (
            request.method in self.AUDIT_METHODS or
            response.status_code >= 400 or  # Audit all errors
            "/auth/" in str(request.url)  # Always audit authentication
        )

        if should_audit:
            try:
                await self._create_audit_log(
                    request=request,
                    response=response,
                    duration_ms=duration_ms,
                    request_id=request_id,
                    user_id=user_id,
                    workspace_id=workspace_id
                )
            except Exception as e:
                logger.error(f"Failed to create audit log: {e}")

        return response

    async def _create_audit_log(
        self,
        request: Request,
        response: Response,
        duration_ms: int,
        request_id: str,
        user_id: int = None,
        workspace_id: int = None
    ):
        """Create audit log entry in database."""
        try:
            # Extract resource information from path
            path_parts = str(request.url.path).split("/")
            resource_type = self._extract_resource_type(path_parts)
            resource_id = self._extract_resource_id(path_parts)

            # Determine action
            action = self.METHOD_TO_ACTION.get(request.method, "unknown")

            # Determine success
            success = 200 <= response.status_code < 400

            # Determine risk level
            risk_level = self._calculate_risk_level(
                request.method,
                response.status_code,
                str(request.url.path)
            )

            # Get IP address
            ip_address = request.client.host if request.client else None

            # Get user agent
            user_agent = request.headers.get("user-agent", "")

            # Create audit log
            async with AsyncSessionLocal() as session:
                audit_log = AuditLog(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_method=request.method,
                    request_path=str(request.url.path),
                    request_id=request_id,
                    success=success,
                    failure_reason=None if success else f"HTTP {response.status_code}",
                    risk_level=risk_level,
                    duration_ms=duration_ms,
                    metadata={
                        "status_code": response.status_code,
                        "query_params": dict(request.query_params),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    created_at=datetime.utcnow()
                )

                session.add(audit_log)
                await session.commit()

                # Create security event for high-risk operations
                if risk_level in ["high", "critical"] and not success:
                    await self._create_security_event(
                        session=session,
                        user_id=user_id,
                        workspace_id=workspace_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        event_type=self._determine_security_event_type(
                            request.method,
                            response.status_code,
                            str(request.url.path)
                        ),
                        description=f"Failed {action} on {resource_type}: HTTP {response.status_code}",
                        severity=risk_level
                    )

        except Exception as e:
            logger.error(f"Error creating audit log: {e}")

    def _extract_resource_type(self, path_parts: list) -> str:
        """Extract resource type from URL path."""
        # Example: /api/v1/projects/123 -> "project"
        for part in path_parts:
            if part in ["projects", "tasks", "documents", "users", "workspaces",
                        "channels", "messages", "teams", "meetings", "signatures"]:
                return part.rstrip("s")  # Remove trailing 's'
        return "unknown"

    def _extract_resource_id(self, path_parts: list) -> str:
        """Extract resource ID from URL path."""
        # Look for numeric or UUID-like values
        for part in path_parts:
            if part.isdigit() or (len(part) > 20 and "-" in part):
                return part
        return None

    def _calculate_risk_level(
        self,
        method: str,
        status_code: int,
        path: str
    ) -> str:
        """Calculate risk level of operation."""
        # Failed authentication attempts are high risk
        if "/auth/" in path and status_code == 401:
            return "high"

        # Successful deletions are medium risk
        if method == "DELETE" and status_code < 400:
            return "medium"

        # Any server errors are high risk
        if status_code >= 500:
            return "critical"

        # Failed requests are medium risk
        if 400 <= status_code < 500:
            return "medium"

        # Normal operations are low risk
        return "low"

    def _determine_security_event_type(
        self,
        method: str,
        status_code: int,
        path: str
    ) -> str:
        """Determine type of security event."""
        if "/auth/login" in path and status_code == 401:
            return "failed_login"
        elif "/auth/" in path and status_code == 429:
            return "brute_force_attempt"
        elif status_code == 403:
            return "unauthorized_access"
        elif status_code == 404 and method in ["PUT", "DELETE"]:
            return "resource_manipulation_attempt"
        else:
            return "suspicious_activity"

    async def _create_security_event(
        self,
        session: AsyncSession,
        user_id: int,
        workspace_id: int,
        ip_address: str,
        user_agent: str,
        event_type: str,
        description: str,
        severity: str
    ):
        """Create security event for high-risk operations."""
        try:
            security_event = SecurityEvent(
                event_type=event_type,
                user_id=user_id,
                workspace_id=workspace_id,
                severity=severity,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                action_taken="logged",  # Can be extended to "blocked", "alerted", etc.
                resolved=False,
                metadata={
                    "timestamp": datetime.utcnow().isoformat()
                },
                created_at=datetime.utcnow()
            )

            session.add(security_event)
            await session.commit()

            # Log to application logs as well
            logger.warning(
                f"Security Event: {event_type} from IP {ip_address} - {description}"
            )

        except Exception as e:
            logger.error(f"Failed to create security event: {e}")


def sanitize_for_logging(data: dict) -> dict:
    """Remove sensitive fields from data before logging."""
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in AuditLoggingMiddleware.SENSITIVE_FIELDS):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_logging(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_for_logging(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value

    return sanitized
