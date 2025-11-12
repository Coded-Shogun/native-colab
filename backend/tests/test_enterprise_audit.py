"""
Tests for Enterprise Audit Logging System
Tests audit logs, security events, data access logs, and compliance logs
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog, SecurityEvent, DataAccessLog, ComplianceLog
from app.middleware.audit import AuditLoggingMiddleware, sanitize_for_logging


class TestAuditLogging:
    """Test audit logging functionality"""

    @pytest.mark.asyncio
    async def test_create_audit_log(self, db_session: AsyncSession, test_workspace, test_user):
        """Test creating an audit log entry"""
        audit_log = AuditLog(
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            action="create",
            resource_type="project",
            resource_id="proj_123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            request_method="POST",
            request_path="/api/v1/projects",
            request_id="req_abc123",
            new_values={"name": "Test Project", "status": "active"},
            success=True,
            risk_level="low",
            duration_ms=45
        )

        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(audit_log)

        assert audit_log.id is not None
        assert audit_log.action == "create"
        assert audit_log.resource_type == "project"
        assert audit_log.success is True
        assert audit_log.risk_level == "low"

    @pytest.mark.asyncio
    async def test_audit_log_with_old_and_new_values(self, db_session: AsyncSession, test_user):
        """Test audit log captures before/after values"""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="update",
            resource_type="project",
            resource_id="proj_123",
            old_values={"status": "in_progress", "name": "Old Name"},
            new_values={"status": "completed", "name": "New Name"},
            success=True
        )

        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(audit_log)

        assert audit_log.old_values["status"] == "in_progress"
        assert audit_log.new_values["status"] == "completed"
        assert audit_log.old_values["name"] == "Old Name"
        assert audit_log.new_values["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_audit_log_failure(self, db_session: AsyncSession, test_user):
        """Test audit log for failed operations"""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="delete",
            resource_type="project",
            resource_id="proj_123",
            success=False,
            failure_reason="Insufficient permissions",
            risk_level="medium"
        )

        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(audit_log)

        assert audit_log.success is False
        assert audit_log.failure_reason == "Insufficient permissions"
        assert audit_log.risk_level == "medium"

    @pytest.mark.asyncio
    async def test_query_audit_logs_by_user(self, db_session: AsyncSession, test_user):
        """Test querying audit logs by user"""
        # Create multiple audit logs
        for i in range(5):
            audit_log = AuditLog(
                user_id=test_user.id,
                action="read",
                resource_type="project",
                resource_id=f"proj_{i}",
                success=True
            )
            db_session.add(audit_log)

        await db_session.commit()

        # Query logs for user
        from sqlalchemy import select
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.user_id == test_user.id)
        )
        logs = result.scalars().all()

        assert len(logs) == 5
        assert all(log.user_id == test_user.id for log in logs)

    @pytest.mark.asyncio
    async def test_query_audit_logs_by_date_range(self, db_session: AsyncSession, test_user):
        """Test querying audit logs by date range"""
        # Create logs with different dates
        now = datetime.utcnow()
        old_log = AuditLog(
            user_id=test_user.id,
            action="read",
            resource_type="project",
            resource_id="proj_old",
            created_at=now - timedelta(days=10),
            success=True
        )
        recent_log = AuditLog(
            user_id=test_user.id,
            action="read",
            resource_type="project",
            resource_id="proj_recent",
            created_at=now,
            success=True
        )

        db_session.add(old_log)
        db_session.add(recent_log)
        await db_session.commit()

        # Query logs from last 5 days
        from sqlalchemy import select
        cutoff = now - timedelta(days=5)
        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.user_id == test_user.id,
                AuditLog.created_at >= cutoff
            )
        )
        logs = result.scalars().all()

        assert len(logs) == 1
        assert logs[0].resource_id == "proj_recent"


class TestSecurityEvents:
    """Test security event logging"""

    @pytest.mark.asyncio
    async def test_create_security_event(self, db_session: AsyncSession, test_user):
        """Test creating a security event"""
        event = SecurityEvent(
            event_type="failed_login",
            user_id=test_user.id,
            severity="medium",
            description="Failed login attempt with incorrect password",
            ip_address="203.0.113.42",
            user_agent="Mozilla/5.0",
            action_taken="logged"
        )

        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        assert event.id is not None
        assert event.event_type == "failed_login"
        assert event.severity == "medium"
        assert event.resolved is False

    @pytest.mark.asyncio
    async def test_resolve_security_event(self, db_session: AsyncSession, test_user, test_admin):
        """Test resolving a security event"""
        event = SecurityEvent(
            event_type="brute_force_attempt",
            user_id=test_user.id,
            severity="high",
            description="Multiple failed login attempts",
            ip_address="203.0.113.42",
            action_taken="blocked"
        )

        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        # Resolve the event
        event.resolved = True
        event.resolved_at = datetime.utcnow()
        event.resolved_by = test_admin.id

        await db_session.commit()
        await db_session.refresh(event)

        assert event.resolved is True
        assert event.resolved_at is not None
        assert event.resolved_by == test_admin.id

    @pytest.mark.asyncio
    async def test_query_unresolved_security_events(self, db_session: AsyncSession, test_user):
        """Test querying unresolved security events"""
        # Create resolved and unresolved events
        resolved_event = SecurityEvent(
            event_type="failed_login",
            user_id=test_user.id,
            severity="low",
            description="Resolved event",
            resolved=True,
            resolved_at=datetime.utcnow()
        )
        unresolved_event = SecurityEvent(
            event_type="suspicious_activity",
            user_id=test_user.id,
            severity="high",
            description="Unresolved event",
            resolved=False
        )

        db_session.add(resolved_event)
        db_session.add(unresolved_event)
        await db_session.commit()

        # Query unresolved events
        from sqlalchemy import select
        result = await db_session.execute(
            select(SecurityEvent).where(SecurityEvent.resolved == False)
        )
        events = result.scalars().all()

        assert len(events) >= 1
        assert all(not event.resolved for event in events)


class TestDataAccessLogs:
    """Test data access logging for compliance"""

    @pytest.mark.asyncio
    async def test_log_data_access(self, db_session: AsyncSession, test_user, test_workspace):
        """Test logging data access"""
        access_log = DataAccessLog(
            user_id=test_user.id,
            workspace_id=test_workspace.id,
            resource_type="document",
            resource_id="doc_123",
            action="read",
            data_classification="confidential",
            ip_address="192.168.1.100",
            justification="Business need",
            granted_by_policy="manager_access_policy"
        )

        db_session.add(access_log)
        await db_session.commit()
        await db_session.refresh(access_log)

        assert access_log.id is not None
        assert access_log.action == "read"
        assert access_log.data_classification == "confidential"

    @pytest.mark.asyncio
    async def test_query_data_access_by_classification(self, db_session: AsyncSession, test_user):
        """Test querying data access by classification level"""
        # Create logs with different classifications
        confidential_log = DataAccessLog(
            user_id=test_user.id,
            resource_type="document",
            resource_id="doc_conf",
            action="read",
            data_classification="confidential"
        )
        public_log = DataAccessLog(
            user_id=test_user.id,
            resource_type="document",
            resource_id="doc_pub",
            action="read",
            data_classification="public"
        )

        db_session.add(confidential_log)
        db_session.add(public_log)
        await db_session.commit()

        # Query confidential data access
        from sqlalchemy import select
        result = await db_session.execute(
            select(DataAccessLog).where(
                DataAccessLog.data_classification == "confidential"
            )
        )
        logs = result.scalars().all()

        assert len(logs) >= 1
        assert all(log.data_classification == "confidential" for log in logs)


class TestComplianceLogs:
    """Test compliance logging for GDPR, SOC 2, etc."""

    @pytest.mark.asyncio
    async def test_log_gdpr_data_export(self, db_session: AsyncSession, test_user):
        """Test logging GDPR data export request"""
        compliance_log = ComplianceLog(
            compliance_type="gdpr",
            action_type="data_export_requested",
            user_id=test_user.id,
            description="User requested data export in JSON format",
            legal_basis="consent",
            data_subject_id=str(test_user.id),
            processing_purpose="User data portability request (Article 20)",
            data_categories=["personal_info", "messages", "documents"],
            retention_period=30,
            metadata={"format": "json", "include_audit_logs": True}
        )

        db_session.add(compliance_log)
        await db_session.commit()
        await db_session.refresh(compliance_log)

        assert compliance_log.id is not None
        assert compliance_log.compliance_type == "gdpr"
        assert compliance_log.action_type == "data_export_requested"
        assert "personal_info" in compliance_log.data_categories

    @pytest.mark.asyncio
    async def test_log_gdpr_data_deletion(self, db_session: AsyncSession, test_user):
        """Test logging GDPR data deletion request"""
        compliance_log = ComplianceLog(
            compliance_type="gdpr",
            action_type="data_deletion_requested",
            user_id=test_user.id,
            description="User requested account deletion",
            legal_basis="user_request",
            data_subject_id=str(test_user.id),
            processing_purpose="Right to erasure (Article 17)",
            expiry_date=datetime.utcnow() + timedelta(days=30)
        )

        db_session.add(compliance_log)
        await db_session.commit()
        await db_session.refresh(compliance_log)

        assert compliance_log.compliance_type == "gdpr"
        assert compliance_log.action_type == "data_deletion_requested"
        assert compliance_log.expiry_date is not None


class TestAuditMiddleware:
    """Test audit logging middleware"""

    def test_sanitize_for_logging(self):
        """Test sanitization of sensitive data"""
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com",
            "token": "abc123xyz",
            "api_key": "key_secret",
            "credit_card": "1234-5678-9012-3456"
        }

        sanitized = sanitize_for_logging(data)

        assert sanitized["username"] == "testuser"
        assert sanitized["email"] == "test@example.com"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["credit_card"] == "***REDACTED***"

    def test_sanitize_nested_data(self):
        """Test sanitization of nested structures"""
        data = {
            "user": {
                "name": "Test User",
                "password": "secret"
            },
            "settings": {
                "api_key": "key_123"
            }
        }

        sanitized = sanitize_for_logging(data)

        assert sanitized["user"]["name"] == "Test User"
        assert sanitized["user"]["password"] == "***REDACTED***"
        assert sanitized["settings"]["api_key"] == "***REDACTED***"


class TestAuditQueries:
    """Test common audit log queries"""

    @pytest.mark.asyncio
    async def test_get_user_activity_summary(self, db_session: AsyncSession, test_user):
        """Test getting user activity summary"""
        # Create various audit logs
        actions = ["create", "read", "update", "delete", "read"]
        for action in actions:
            audit_log = AuditLog(
                user_id=test_user.id,
                action=action,
                resource_type="project",
                resource_id="proj_test",
                success=True
            )
            db_session.add(audit_log)

        await db_session.commit()

        # Query activity summary
        from sqlalchemy import select, func
        result = await db_session.execute(
            select(
                AuditLog.action,
                func.count(AuditLog.id).label("count")
            )
            .where(AuditLog.user_id == test_user.id)
            .group_by(AuditLog.action)
        )
        summary = {row.action: row.count for row in result}

        assert summary["read"] == 2
        assert summary["create"] == 1
        assert summary["update"] == 1
        assert summary["delete"] == 1

    @pytest.mark.asyncio
    async def test_get_high_risk_activities(self, db_session: AsyncSession):
        """Test querying high-risk activities"""
        # Create logs with different risk levels
        risk_levels = ["low", "medium", "high", "critical"]
        for level in risk_levels:
            audit_log = AuditLog(
                action="action",
                resource_type="project",
                risk_level=level,
                success=True
            )
            db_session.add(audit_log)

        await db_session.commit()

        # Query high-risk activities
        from sqlalchemy import select
        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.risk_level.in_(["high", "critical"])
            )
        )
        logs = result.scalars().all()

        assert len(logs) >= 2
        assert all(log.risk_level in ["high", "critical"] for log in logs)
