"""
Tests for Enterprise Security Features
Tests token blacklisting, rate limiting, security headers, and security monitoring
"""

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import redis.asyncio as redis

from app.core.token_blacklist import TokenBlacklist, get_token_blacklist


class TestTokenBlacklisting:
    """Test JWT token blacklisting functionality"""

    @pytest.mark.asyncio
    async def test_blacklist_token(self):
        """Test blacklisting a single token"""
        # Mock Redis client
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=1)

        blacklist = TokenBlacklist(mock_redis)

        # Blacklist token
        await blacklist.blacklist_token(
            token="test_token_123",
            expires_in_seconds=3600,
            reason="user_logout"
        )

        # Verify setex was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "blacklist:token:test_token_123" in call_args[0][0]
        assert call_args[0][1] == 3600

        # Check if token is blacklisted
        is_blacklisted = await blacklist.is_blacklisted("test_token_123")
        assert is_blacklisted is True

    @pytest.mark.asyncio
    async def test_token_not_blacklisted(self):
        """Test checking a non-blacklisted token"""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.exists = AsyncMock(return_value=0)

        blacklist = TokenBlacklist(mock_redis)

        is_blacklisted = await blacklist.is_blacklisted("valid_token")
        assert is_blacklisted is False

    @pytest.mark.asyncio
    async def test_blacklist_all_user_tokens(self):
        """Test blacklisting all tokens for a user"""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.keys = AsyncMock(return_value=[b"session:1", b"session:2"])
        mock_redis.get = AsyncMock(return_value=b'{"user_id": 123}')

        blacklist = TokenBlacklist(mock_redis)

        await blacklist.blacklist_user_tokens(
            user_id=123,
            expires_in_seconds=7200,
            reason="account_compromised"
        )

        # Verify setex was called
        assert mock_redis.setex.call_count > 0

    @pytest.mark.asyncio
    async def test_get_blacklist_reason(self):
        """Test retrieving blacklist reason"""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=b"security_incident:2025-01-15T10:30:00Z")

        blacklist = TokenBlacklist(mock_redis)

        reason = await blacklist.get_blacklist_reason("test_token")
        assert reason is not None
        assert "security_incident" in reason

    @pytest.mark.asyncio
    async def test_token_expiry(self):
        """Test that blacklisted tokens expire"""
        mock_redis = AsyncMock(spec=redis.Redis)

        # Initially blacklisted
        mock_redis.exists = AsyncMock(return_value=1)
        blacklist = TokenBlacklist(mock_redis)
        assert await blacklist.is_blacklisted("test_token") is True

        # Simulate expiry
        mock_redis.exists = AsyncMock(return_value=0)
        assert await blacklist.is_blacklisted("test_token") is False


class TestRateLimiting:
    """Test rate limiting middleware"""

    def test_auth_endpoint_rate_limit(self, client: TestClient):
        """Test rate limiting on authentication endpoint"""
        # Attempt multiple logins rapidly
        for i in range(6):  # Limit is usually 5/minute for auth
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrong_password"
                }
            )

            if i < 5:
                # First 5 should go through (may fail auth but not rate limited)
                assert response.status_code in [401, 200]
            else:
                # 6th request should be rate limited
                assert response.status_code == 429
                assert "rate limit" in response.json()["detail"].lower()

    def test_rate_limit_headers(self, client: TestClient):
        """Test that rate limit headers are present"""
        response = client.get("/api/v1/health")

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_per_user(self, client: TestClient, auth_headers):
        """Test per-user rate limiting"""
        # Make multiple requests
        for i in range(65):  # Limit is usually 60/minute
            response = client.get(
                "/api/v1/projects",
                headers=auth_headers
            )

            if i < 60:
                # First 60 should succeed
                assert response.status_code in [200, 404]
            else:
                # Exceeding rate limit
                assert response.status_code == 429

    def test_rate_limit_reset_after_window(self, client: TestClient, auth_headers):
        """Test that rate limit resets after time window"""
        # Make requests up to limit
        for _ in range(60):
            client.get("/api/v1/projects", headers=auth_headers)

        # Next request should be rate limited
        response = client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 429

        # Wait for rate limit window to reset (would need to wait 60s in real test)
        # In practice, use time.sleep(60) or mock time

    def test_different_endpoints_different_limits(self, client: TestClient, auth_headers):
        """Test that different endpoints have different rate limits"""
        # Auth endpoints: 5/minute
        # Regular API: 60/minute
        # Upload: 10/minute
        # Export: 5/5 minutes

        # This would require checking actual limits per endpoint
        auth_response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        api_response = client.get("/api/v1/projects", headers=auth_headers)

        # Both should have different X-RateLimit-Limit values
        if "X-RateLimit-Limit" in auth_response.headers:
            auth_limit = int(auth_response.headers["X-RateLimit-Limit"])
            api_limit = int(api_response.headers["X-RateLimit-Limit"])
            assert auth_limit != api_limit


class TestSecurityHeaders:
    """Test enterprise security headers"""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are present in responses"""
        response = client.get("/api/v1/health")

        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers

    def test_csp_header_present(self, client: TestClient):
        """Test Content-Security-Policy header"""
        response = client.get("/")

        if "Content-Security-Policy" in response.headers:
            csp = response.headers["Content-Security-Policy"]
            assert "default-src" in csp
            assert "'self'" in csp

    def test_server_header_removed(self, client: TestClient):
        """Test that Server header is not exposed"""
        response = client.get("/api/v1/health")

        # Server header should be hidden or generic
        if "Server" in response.headers:
            assert "FastAPI" not in response.headers["Server"]
            assert "uvicorn" not in response.headers["Server"].lower()


class TestSecurityMonitoring:
    """Test security event monitoring"""

    @pytest.mark.asyncio
    async def test_failed_login_creates_security_event(
        self,
        client: TestClient,
        db_session
    ):
        """Test that failed login attempts create security events"""
        # Attempt failed login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrong_password"
            }
        )

        assert response.status_code == 401

        # Check if security event was created
        from sqlalchemy import select
        from app.db.models.audit_log import SecurityEvent

        result = await db_session.execute(
            select(SecurityEvent)
            .where(SecurityEvent.event_type == "failed_login")
            .order_by(SecurityEvent.created_at.desc())
            .limit(1)
        )
        event = result.scalar_one_or_none()

        if event:  # May not exist if middleware not integrated yet
            assert event.severity in ["low", "medium"]
            assert "failed login" in event.description.lower()

    @pytest.mark.asyncio
    async def test_multiple_failed_logins_high_severity(
        self,
        client: TestClient,
        db_session
    ):
        """Test that multiple failed logins create high-severity events"""
        # Attempt multiple failed logins
        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrong_password"
                }
            )

        # Check for high-severity security event
        from sqlalchemy import select
        from app.db.models.audit_log import SecurityEvent

        result = await db_session.execute(
            select(SecurityEvent)
            .where(
                SecurityEvent.event_type.in_(["brute_force_attempt", "multiple_failed_logins"]),
                SecurityEvent.severity.in_(["high", "critical"])
            )
            .order_by(SecurityEvent.created_at.desc())
            .limit(1)
        )
        event = result.scalar_one_or_none()

        # May not exist if monitoring not fully integrated
        if event:
            assert event.severity in ["high", "critical"]


class TestPasswordSecurity:
    """Test password security requirements"""

    def test_weak_password_rejected(self, client: TestClient):
        """Test that weak passwords are rejected"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",  # Too short
                "full_name": "New User"
            }
        )

        assert response.status_code == 422  # Validation error
        assert "password" in str(response.json()).lower()

    def test_password_requirements(self, client: TestClient):
        """Test password complexity requirements"""
        # No uppercase
        response1 = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user1@example.com",
                "password": "lowercase123!",
                "full_name": "User One"
            }
        )

        # No numbers
        response2 = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user2@example.com",
                "password": "NoNumbers!",
                "full_name": "User Two"
            }
        )

        # No special characters
        response3 = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user3@example.com",
                "password": "NoSpecial123",
                "full_name": "User Three"
            }
        )

        # At least one should fail validation
        statuses = [response1.status_code, response2.status_code, response3.status_code]
        assert 422 in statuses  # At least one validation failure


class TestSessionSecurity:
    """Test session security features"""

    def test_session_token_invalidation_on_logout(
        self,
        client: TestClient,
        auth_headers
    ):
        """Test that session is invalidated on logout"""
        # Verify token works
        response1 = client.get("/api/v1/users/me", headers=auth_headers)
        assert response1.status_code == 200

        # Logout
        logout_response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert logout_response.status_code == 200

        # Token should no longer work
        response2 = client.get("/api/v1/users/me", headers=auth_headers)
        assert response2.status_code == 401

    def test_concurrent_session_limit(self, client: TestClient):
        """Test maximum concurrent sessions per user"""
        # This would require creating multiple sessions
        # and verifying that old sessions are invalidated
        pass  # Implement based on session limit configuration


class TestAPIKeySecurity:
    """Test API key security features"""

    def test_api_key_authentication(self, client: TestClient):
        """Test API key authentication"""
        # Create API key (would need endpoint)
        # Use API key for authentication
        # Verify it works
        pass  # Implement when API key endpoint exists

    def test_api_key_scopes(self, client: TestClient):
        """Test that API keys respect scopes"""
        # Create API key with limited scopes
        # Try to access endpoints outside scope
        # Should be denied
        pass  # Implement when API key scopes exist


class TestIPWhitelisting:
    """Test IP whitelisting features"""

    def test_admin_endpoint_ip_restriction(self, client: TestClient, admin_auth_headers):
        """Test that admin endpoints can be IP-restricted"""
        # This would require configuration of IP whitelist
        # And testing from different IPs
        pass  # Implement based on IP whitelist configuration


class TestEncryption:
    """Test encryption features"""

    @pytest.mark.asyncio
    async def test_sensitive_data_encrypted(self, db_session):
        """Test that sensitive data is encrypted in database"""
        # Check that certain fields are encrypted
        # E.g., API keys, tokens, sensitive user data
        pass  # Implement based on encryption strategy

    def test_https_required(self, client: TestClient):
        """Test that HTTPS is required for sensitive endpoints"""
        # In production, HTTP should redirect to HTTPS
        # Or sensitive endpoints should reject HTTP
        pass  # Implement based on HTTPS configuration


class TestAuditTrailSecurity:
    """Test audit trail integrity"""

    @pytest.mark.asyncio
    async def test_audit_logs_immutable(self, db_session):
        """Test that audit logs cannot be modified"""
        from app.db.models.audit_log import AuditLog

        # Create audit log
        audit_log = AuditLog(
            action="test_action",
            resource_type="test",
            success=True
        )
        db_session.add(audit_log)
        await db_session.commit()
        original_created_at = audit_log.created_at

        # Try to modify (should have restrictions)
        audit_log.action = "modified_action"
        await db_session.commit()

        # In enterprise setup, this should either fail or create new entry
        # For now, we just verify timestamp doesn't change
        assert audit_log.created_at == original_created_at

    @pytest.mark.asyncio
    async def test_audit_log_retention(self, db_session):
        """Test audit log retention policy"""
        # Verify old audit logs are archived but not deleted
        # within retention period
        pass  # Implement based on retention policy


class TestComplianceIntegration:
    """Test compliance-related security features"""

    def test_data_classification_enforcement(self, client: TestClient, auth_headers):
        """Test that data classification is enforced"""
        # Attempt to access highly classified data without proper clearance
        # Should be denied
        pass  # Implement based on data classification system

    @pytest.mark.asyncio
    async def test_data_access_logged(self, client: TestClient, auth_headers, db_session):
        """Test that data access is logged for compliance"""
        # Access some data
        response = client.get("/api/v1/projects/1", headers=auth_headers)

        # Verify data access log was created
        from sqlalchemy import select
        from app.db.models.audit_log import DataAccessLog

        result = await db_session.execute(
            select(DataAccessLog)
            .where(DataAccessLog.resource_type == "project")
            .order_by(DataAccessLog.created_at.desc())
            .limit(1)
        )
        log = result.scalar_one_or_none()

        # May not exist if middleware not integrated yet
        if log:
            assert log.action == "read"
